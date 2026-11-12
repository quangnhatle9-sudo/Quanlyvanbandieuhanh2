import os
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Q

from quanly.models import (
    NhiemVu, BaoCaoKetQua, PhanCongVanBanDen, VanBanDen, NguoiDung, PhongBan
)
from quanly.permissions import is_lanh_dao_chi_dao, is_to_truong
from .forms import PhanBoTaskForm, NopBaoCaoForm, DuyetBaoCaoForm


# ==============================================================================
# UC3.2: PHÂN BỔ NHIỆM VỤ CHI TIẾT (Tổ trưởng / Quản lý cấp trung)
# ==============================================================================

@login_required
def nhiem_vu_tu_bgh_view(request):
    """
    Tổ trưởng mở mục 'Nhiệm vụ mới nhận từ BGH'
    Xem danh sách các văn bản BGH đã chỉ đạo tới tổ của mình.
    """
    user = request.user
    # Lấy các phân công chỉ đạo tới phòng ban của user hoặc đích danh user
    if user.phong_ban:
        phan_cong_list = PhanCongVanBanDen.objects.filter(
            Q(phong_ban_nhan=user.phong_ban) | Q(nguoi_nhan=user)
        ).select_related('ma_van_ban_den', 'nguoi_chi_dao', 'phong_ban_nhan').order_by('-ngay_phan_cong')
    else:
        phan_cong_list = PhanCongVanBanDen.objects.filter(
            nguoi_nhan=user
        ).select_related('ma_van_ban_den', 'nguoi_chi_dao', 'phong_ban_nhan').order_by('-ngay_phan_cong')

    context = {
        'phan_cong_list': phan_cong_list,
        'user_phong_ban': user.phong_ban,
    }
    return render(request, 'nhiemvu/nhiem_vu_tu_bgh.html', context)


@login_required
def giao_viec_view(request, ma_phan_cong):
    """
    UC3.2: Tổ trưởng tạo đầu việc (Task) cụ thể từ chỉ đạo của BGH
    Giao cho Giáo viên/Nhân viên trong tổ kèm Deadline con.
    """
    phan_cong = get_object_or_404(
        PhanCongVanBanDen.objects.select_related('ma_van_ban_den', 'nguoi_chi_dao', 'phong_ban_nhan'),
        ma_phan_cong=ma_phan_cong
    )

    # Danh sách task đã tạo từ văn bản này
    tasks_da_tao = NhiemVu.objects.filter(
        ma_van_ban_den=phan_cong.ma_van_ban_den
    ).select_related('nguoi_giao', 'nguoi_nhan').order_by('-ngay_giao')

    if request.method == 'POST':
        form = PhanBoTaskForm(request.POST, to_truong=request.user, phan_cong=phan_cong)
        if form.is_valid():
            tieu_de = form.cleaned_data['tieu_de']
            noi_dung_yeu_cau = form.cleaned_data['noi_dung_yeu_cau']
            nguoi_nhan = form.cleaned_data['nguoi_nhan']
            nguoi_phoi_hop = form.cleaned_data.get('nguoi_phoi_hop')
            han_xu_ly = form.cleaned_data['han_xu_ly']

            # Ghi chú thêm cán bộ phối hợp vào nội dung nếu có
            if nguoi_phoi_hop:
                noi_dung_yeu_cau += f" [Cán bộ phối hợp: {nguoi_phoi_hop.ho_ten}]"

            ma_nv = f"NV{uuid.uuid4().hex[:6].upper()}"
            NhiemVu.objects.create(
                ma_nhiem_vu=ma_nv,
                ma_van_ban_den=phan_cong.ma_van_ban_den,
                tieu_de=tieu_de,
                noi_dung_yeu_cau=noi_dung_yeu_cau,
                nguoi_giao=request.user,
                phong_ban_nhan=request.user.phong_ban,
                nguoi_nhan=nguoi_nhan,
                ngay_giao=timezone.now(),
                han_xu_ly=han_xu_ly,
                trang_thai_nhiem_vu='Chờ xử lý'
            )
            messages.success(request, f'Giao việc thành công! Task đã được chuyển đến Bàn làm việc của {nguoi_nhan.ho_ten}.')
            return redirect('giao_viec', ma_phan_cong=ma_phan_cong)
    else:
        # Khởi tạo mặc định deadline gợi ý bằng deadline của BGH
        initial_data = {}
        if phan_cong.han_xu_ly:
            initial_data['han_xu_ly'] = phan_cong.han_xu_ly.strftime('%Y-%m-%dT%H:%M')
        form = PhanBoTaskForm(initial=initial_data, to_truong=request.user, phan_cong=phan_cong)

    context = {
        'phan_cong': phan_cong,
        'form': form,
        'tasks_da_tao': tasks_da_tao,
    }
    return render(request, 'nhiemvu/giao_viec.html', context)


# ==============================================================================
# UC3.3: THỰC THI NHIỆM VỤ VÀ NỘP BÁO CÁO (Giáo viên / Nhân viên)
# ==============================================================================

@login_required
def ban_lam_viec_ca_nhan_view(request):
    """
    UC3.3: Bàn làm việc cá nhân của Giáo viên/Nhân viên
    Bao gồm 4 tabs:
    1. Việc cần xử lý (Chờ xử lý, Đang thực hiện)
    2. Văn bản / Nhiệm vụ bị trả lại (Yêu cầu chỉnh sửa)
    3. Việc đã nộp báo cáo (Chờ duyệt kết quả)
    4. Việc đã hoàn thành (Đã hoàn thành)
    """
    user = request.user
    active_tab = request.GET.get('tab', 'can_xu_ly')

    # Danh sách nhiệm vụ được giao cho user
    base_qs = NhiemVu.objects.filter(nguoi_nhan=user).select_related(
        'ma_van_ban_den', 'nguoi_giao', 'phong_ban_nhan'
    ).order_by('-ngay_giao')

    viec_can_xu_ly = base_qs.filter(trang_thai_nhiem_vu__in=['Chờ xử lý', 'Đang thực hiện'])
    viec_bi_tra_lai = base_qs.filter(trang_thai_nhiem_vu__in=['Yêu cầu chỉnh sửa', 'Chưa đạt'])
    viec_cho_duyet = base_qs.filter(trang_thai_nhiem_vu__in=['Chờ duyệt kết quả', 'Tổ trưởng đã duyệt - Chờ BGH duyệt'])
    viec_hoan_thanh = base_qs.filter(trang_thai_nhiem_vu='Đã hoàn thành')

    context = {
        'active_tab': active_tab,
        'viec_can_xu_ly': viec_can_xu_ly,
        'viec_bi_tra_lai': viec_bi_tra_lai,
        'viec_cho_duyet': viec_cho_duyet,
        'viec_hoan_thanh': viec_hoan_thanh,
        'count_can_xu_ly': viec_can_xu_ly.count(),
        'count_tra_lai': viec_bi_tra_lai.count(),
        'count_cho_duyet': viec_cho_duyet.count(),
        'count_hoan_thanh': viec_hoan_thanh.count(),
    }
    return render(request, 'nhiemvu/ban_lam_viec.html', context)


@login_required
def tiep_nhan_nhiem_vu_view(request, ma_nhiem_vu):
    """Giáo viên bấm nút Tiếp nhận nhiệm vụ -> Chuyển sang 'Đang thực hiện'"""
    task = get_object_or_404(NhiemVu, ma_nhiem_vu=ma_nhiem_vu, nguoi_nhan=request.user)
    if task.trang_thai_nhiem_vu == 'Chờ xử lý':
        task.trang_thai_nhiem_vu = 'Đang thực hiện'
        task.save()
        messages.success(request, f'Đã tiếp nhận nhiệm vụ: "{task.tieu_de}". Bắt đầu thực hiện.')
    return redirect('ban_lam_viec_ca_nhan')


@login_required
def nop_bao_cao_view(request, ma_nhiem_vu):
    """
    UC3.3: Giáo viên đính kèm tệp kết quả và nộp báo cáo kết quả thực hiện.
    Hoặc hoàn thiện lại nếu nhiệm vụ nằm trong danh mục 'Văn bản bị trả lại'.
    """
    task = get_object_or_404(
        NhiemVu.objects.select_related('ma_van_ban_den', 'nguoi_giao', 'phong_ban_nhan'),
        ma_nhiem_vu=ma_nhiem_vu,
        nguoi_nhan=request.user
    )

    # Không cho phép nộp lại nếu hồ sơ đã Đã hoàn thành (Read-only)
    if task.trang_thai_nhiem_vu == 'Đã hoàn thành':
        messages.error(request, 'Hồ sơ nhiệm vụ này đã được phê duyệt hoàn tất và đóng băng (Read-only), không thể chỉnh sửa.')
        return redirect('ban_lam_viec_ca_nhan')

    # Tìm báo cáo trước đó nếu có (trường hợp bị trả lại nộp lại)
    bao_cao_cu = BaoCaoKetQua.objects.filter(ma_nhiem_vu=task).order_by('-ngay_bao_cao').first()

    if request.method == 'POST':
        form = NopBaoCaoForm(request.POST, request.FILES)
        if form.is_valid():
            noi_dung_bao_cao = form.cleaned_data['noi_dung_bao_cao']
            file_upload = form.cleaned_data['file_ket_qua']

            # Lưu file vào thư mục media/bao_cao/
            ten_file_luu = f"bao_cao_{task.ma_nhiem_vu}_{uuid.uuid4().hex[:6]}_{file_upload.name}"
            duong_dan_file = os.path.join('bao_cao', ten_file_luu)
            default_storage.save(duong_dan_file, file_upload)

            # Tạo bản ghi báo cáo kết quả
            ma_bc = f"BC{uuid.uuid4().hex[:6].upper()}"
            BaoCaoKetQua.objects.create(
                ma_bao_cao=ma_bc,
                ma_nhiem_vu=task,
                nguoi_bao_cao=request.user,
                noi_dung_bao_cao=noi_dung_bao_cao,
                file_ket_qua=duong_dan_file,
                ngay_bao_cao=timezone.now(),
                trang_thai_duyet='Chờ duyệt kết quả'
            )

            # Chuyển trạng thái nhiệm vụ sang 'Chờ duyệt kết quả'
            task.trang_thai_nhiem_vu = 'Chờ duyệt kết quả'
            task.save()

            messages.success(request, 'Nộp báo cáo thành công! Hồ sơ đã được chuyển lên Tổ trưởng / BGH để kiểm duyệt.')
            return redirect('ban_lam_viec_ca_nhan')
    else:
        initial_data = {}
        if bao_cao_cu:
            initial_data['noi_dung_bao_cao'] = bao_cao_cu.noi_dung_bao_cao
        form = NopBaoCaoForm(initial=initial_data)

    context = {
        'task': task,
        'form': form,
        'bao_cao_cu': bao_cao_cu,
    }
    return render(request, 'nhiemvu/nop_bao_cao.html', context)


# ==============================================================================
# UC3.4: KIỂM DUYỆT VÀ KÝ DUYỆT KẾT QUẢ (2 CẤP: Tổ trưởng & Ban Giám hiệu)
# ==============================================================================

@login_required
def kiem_duyet_danh_sach_view(request):
    """
    UC3.4: Danh sách hồ sơ chờ kiểm duyệt 2 cấp:
    - Cấp 1 (Tổ trưởng): Duyệt sơ bộ kết quả của GV trong tổ ('Chờ duyệt kết quả').
    - Cấp 2 (Ban Giám hiệu): Duyệt lần cuối kết quả đã qua Tổ trưởng xác nhận Đạt ('Tổ trưởng đã duyệt - Chờ BGH duyệt').
    """
    user = request.user
    la_lanh_dao = is_lanh_dao_chi_dao(user)
    la_to_truong = is_to_truong(user)

    if not (la_lanh_dao or la_to_truong):
        messages.error(request, 'Bạn không có thẩm quyền kiểm duyệt kết quả.')
        return redirect('ban_lam_viec_ca_nhan')

    # Báo cáo chờ Tổ trưởng duyệt sơ bộ (Cấp 1)
    danh_sach_cap_1 = []
    if la_to_truong and user.phong_ban:
        danh_sach_cap_1 = NhiemVu.objects.filter(
            phong_ban_nhan=user.phong_ban,
            trang_thai_nhiem_vu='Chờ duyệt kết quả'
        ).select_related('nguoi_nhan', 'nguoi_giao', 'ma_van_ban_den').order_by('-ngay_giao')

    # Báo cáo chờ Ban Giám hiệu duyệt cuối (Cấp 2)
    danh_sach_cap_2 = []
    if la_lanh_dao:
        danh_sach_cap_2 = NhiemVu.objects.filter(
            Q(trang_thai_nhiem_vu='Tổ trưởng đã duyệt - Chờ BGH duyệt') |
            Q(trang_thai_nhiem_vu='Chờ duyệt kết quả', nguoi_giao=user) # Nhiệm vụ BGH giao thẳng khẩn
        ).select_related('nguoi_nhan', 'nguoi_giao', 'ma_van_ban_den', 'phong_ban_nhan').order_by('-ngay_giao')

    # Danh sách đã hoàn thành (Read-only archive)
    danh_sach_da_hoan_thanh = NhiemVu.objects.filter(
        trang_thai_nhiem_vu='Đã hoàn thành'
    ).select_related('nguoi_nhan', 'nguoi_giao', 'ma_van_ban_den').order_by('-han_xu_ly')[:10]

    context = {
        'la_lanh_dao': la_lanh_dao,
        'la_to_truong': la_to_truong,
        'danh_sach_cap_1': danh_sach_cap_1,
        'danh_sach_cap_2': danh_sach_cap_2,
        'danh_sach_da_hoan_thanh': danh_sach_da_hoan_thanh,
    }
    return render(request, 'nhiemvu/kiem_duyet_danh_sach.html', context)


@login_required
def chi_tiet_duyet_view(request, ma_nhiem_vu):
    """
    UC3.4: Màn hình thẩm định báo cáo, xác nhận Đạt hoặc Yêu cầu chỉnh sửa
    """
    task = get_object_or_404(
        NhiemVu.objects.select_related('ma_van_ban_den', 'nguoi_nhan', 'nguoi_giao', 'phong_ban_nhan'),
        ma_nhiem_vu=ma_nhiem_vu
    )
    bao_cao = BaoCaoKetQua.objects.filter(ma_nhiem_vu=task).order_by('-ngay_bao_cao').first()

    la_lanh_dao = is_lanh_dao_chi_dao(request.user)
    la_to_truong = is_to_truong(request.user)
    is_completed = (task.trang_thai_nhiem_vu == 'Đã hoàn thành')

    if request.method == 'POST':
        # Business Rule: Đóng băng hồ sơ khi đã hoàn thành (Read-only)
        if is_completed:
            messages.error(request, 'Hồ sơ đã được phê duyệt hoàn tất và đóng băng (Read-only), không được phép chỉnh sửa.')
            return redirect('kiem_duyet_danh_sach')

        form = DuyetBaoCaoForm(request.POST)
        if form.is_valid():
            quyet_dinh = form.cleaned_data['quyet_dinh']
            nhan_xet = form.cleaned_data['nhan_xet']

            if quyet_dinh == 'DAT':
                if task.trang_thai_nhiem_vu == 'Tổ trưởng đã duyệt - Chờ BGH duyệt' or (la_lanh_dao and task.nguoi_giao == request.user):
                    # BGH Ký duyệt hoàn thành (Bước cuối)
                    task.trang_thai_nhiem_vu = 'Đã hoàn thành'
                    task.save()
                    if bao_cao:
                        bao_cao.nguoi_duyet = request.user
                        bao_cao.trang_thai_duyet = 'Đã hoàn thành'
                        bao_cao.nhan_xet = nhan_xet or 'Ban Giám hiệu ký duyệt hoàn thành.'
                        bao_cao.save()
                    messages.success(request, f'Ban Giám hiệu đã ký duyệt hoàn thành nhiệm vụ "{task.tieu_de}". Hồ sơ đã được đóng băng lưu trữ (Read-only).')
                else:
                    # Tổ trưởng duyệt sơ bộ Đạt (Cấp 1) -> Chuyển lên BGH
                    task.trang_thai_nhiem_vu = 'Tổ trưởng đã duyệt - Chờ BGH duyệt'
                    task.save()
                    if bao_cao:
                        bao_cao.nguoi_duyet = request.user
                        bao_cao.trang_thai_duyet = 'Tổ trưởng đã duyệt Đạt'
                        bao_cao.nhan_xet = nhan_xet or 'Tổ trưởng duyệt sơ bộ: Đạt yêu cầu. Trình BGH ký duyệt.'
                        bao_cao.save()
                    messages.success(request, f'Tổ trưởng đã xác nhận Đạt. Hồ sơ đã được chuyển lên Ban Giám hiệu để ký duyệt lần cuối.')

            elif quyet_dinh == 'TRA_LAI':
                # Chưa đạt: Trả lại yêu cầu chỉnh sửa kèm lý do (nhận xét)
                task.trang_thai_nhiem_vu = 'Yêu cầu chỉnh sửa'
                task.save()
                if bao_cao:
                    bao_cao.nguoi_duyet = request.user
                    bao_cao.trang_thai_duyet = 'Yêu cầu chỉnh sửa'
                    bao_cao.nhan_xet = nhan_xet
                    bao_cao.save()
                messages.warning(request, f'Đã trả lại hồ sơ cho {task.nguoi_nhan.ho_ten} kèm yêu cầu chỉnh sửa: "{nhan_xet}".')

            return redirect('kiem_duyet_danh_sach')
    else:
        form = DuyetBaoCaoForm()

    context = {
        'task': task,
        'bao_cao': bao_cao,
        'form': form,
        'la_lanh_dao': la_lanh_dao,
        'la_to_truong': la_to_truong,
        'is_completed': is_completed,
    }
    return render(request, 'nhiemvu/chi_tiet_duyet.html', context)
