
import os
import hashlib
from datetime import datetime, date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.views.decorators.http import require_POST

from quanly.models import (
    NguoiDung,
    VaiTro,
    PhongBan,
    LoaiVanBan,
    NhiemVu,
    VanBanDen,
    VanBanDi
)

from .models import MauVanBan, ThongBao, ThongBaoDaDoc

from .forms import (
    NguoiDungForm,
    NguoiDungUpdateForm,
    VaiTroForm,
    PhongBanForm,
    LoaiVanBanForm,
    MauVanBanForm
)


# ==========================
# TRANG TỔNG QUAN
# ==========================

@login_required
def dashboard_home(request):

    tu_khoa = request.GET.get('q', '').strip()
    tu_ngay = request.GET.get('tu_ngay', '').strip()
    den_ngay = request.GET.get('den_ngay', '').strip()
    ma_loai = request.GET.get('loai_van_ban', '').strip()
    ma_phong_ban = request.GET.get('phong_ban', '').strip()

    ngay_bat_dau_loc = None
    ngay_ket_thuc_loc = None

    try:
        if tu_ngay:
            ngay_bat_dau_loc = date.fromisoformat(tu_ngay)
    except ValueError:
        tu_ngay = ''

    try:
        if den_ngay:
            ngay_ket_thuc_loc = date.fromisoformat(den_ngay)
    except ValueError:
        den_ngay = ''

    # LỌC VĂN BẢN ĐẾN

    van_ban_den_qs = VanBanDen.objects.select_related(
        'ma_loai',
        'nguoi_dang_ky__phong_ban'
    ).all()

    if tu_khoa:
        van_ban_den_qs = van_ban_den_qs.filter(
            Q(so_ky_hieu__icontains=tu_khoa)
            | Q(trich_yeu__icontains=tu_khoa)
        )

    if ngay_bat_dau_loc:
        van_ban_den_qs = van_ban_den_qs.filter(
            ngay_van_ban__gte=ngay_bat_dau_loc
        )

    if ngay_ket_thuc_loc:
        van_ban_den_qs = van_ban_den_qs.filter(
            ngay_van_ban__lte=ngay_ket_thuc_loc
        )

    if ma_loai:
        van_ban_den_qs = van_ban_den_qs.filter(
            ma_loai_id=ma_loai
        )

    if ma_phong_ban:
        van_ban_den_qs = van_ban_den_qs.filter(
            nguoi_dang_ky__phong_ban_id=ma_phong_ban
        )

    # LỌC VĂN BẢN ĐI

    van_ban_di_qs = VanBanDi.objects.select_related(
        'ma_loai',
        'nguoi_soan_thao__phong_ban'
    ).all()

    if tu_khoa:
        van_ban_di_qs = van_ban_di_qs.filter(
            Q(so_ky_hieu_di__icontains=tu_khoa)
            | Q(trich_yeu__icontains=tu_khoa)
        )

    if ngay_bat_dau_loc:
        van_ban_di_qs = van_ban_di_qs.filter(
            ngay_ban_hanh__gte=ngay_bat_dau_loc
        )

    if ngay_ket_thuc_loc:
        van_ban_di_qs = van_ban_di_qs.filter(
            ngay_ban_hanh__lte=ngay_ket_thuc_loc
        )

    if ma_loai:
        van_ban_di_qs = van_ban_di_qs.filter(
            ma_loai_id=ma_loai
        )

    if ma_phong_ban:
        van_ban_di_qs = van_ban_di_qs.filter(
            nguoi_soan_thao__phong_ban_id=ma_phong_ban
        )

    # TẠO DANH SÁCH VĂN BẢN HIỂN THỊ

    danh_sach_van_ban = []

    for van_ban in van_ban_den_qs:
        phong_ban = van_ban.nguoi_dang_ky.phong_ban

        danh_sach_van_ban.append({
            'nhom': 'Văn bản đến',
            'so_ky_hieu': van_ban.so_ky_hieu,
            'trich_yeu': van_ban.trich_yeu,
            'ngay': van_ban.ngay_van_ban,
            'loai': van_ban.ma_loai.ten_loai,
            'don_vi': phong_ban.ten_phong_ban if phong_ban else 'Chưa phân công',
            'trang_thai': van_ban.trang_thai_vb,
        })

    for van_ban in van_ban_di_qs:
        phong_ban = van_ban.nguoi_soan_thao.phong_ban

        danh_sach_van_ban.append({
            'nhom': 'Văn bản đi',
            'so_ky_hieu': van_ban.so_ky_hieu_di or 'Bản nháp',
            'trich_yeu': van_ban.trich_yeu,
            'ngay': van_ban.ngay_ban_hanh,
            'loai': van_ban.ma_loai.ten_loai,
            'don_vi': phong_ban.ten_phong_ban if phong_ban else 'Chưa phân công',
            'trang_thai': van_ban.trang_thai_vb_di,
        })

    danh_sach_van_ban.sort(
        key=lambda item: item['ngay'] or date.min,
        reverse=True
    )

    tong_van_ban_tim_thay = len(danh_sach_van_ban)
    danh_sach_van_ban_hien_thi = danh_sach_van_ban[:20]

    # THỐNG KÊ DỮ LIỆU HỆ THỐNG

    tong_nguoi_dung = NguoiDung.objects.count()
    tong_vai_tro = VaiTro.objects.count()
    tong_phong_ban = PhongBan.objects.count()
    tong_loai_van_ban = LoaiVanBan.objects.count()

    # THỐNG KÊ NHIỆM VỤ THEO TRẠNG THÁI

    tong_cho_xu_ly = NhiemVu.objects.filter(
        trang_thai_nhiem_vu='Chờ xử lý'
    ).count()

    tong_dang_xu_ly = NhiemVu.objects.filter(
        trang_thai_nhiem_vu='Đang xử lý'
    ).count()

    tong_hoan_thanh = NhiemVu.objects.filter(
        trang_thai_nhiem_vu__in=[
            'Hoàn thành',
            'Đã hoàn thành'
        ]
    ).count()

    tong_qua_han = NhiemVu.objects.filter(
        han_xu_ly__lt=timezone.now()
    ).exclude(
        trang_thai_nhiem_vu__in=[
            'Hoàn thành',
            'Đã hoàn thành'
        ]
    ).count()

    tong_nhiem_vu = NhiemVu.objects.count()

    tong_khac = (
        tong_nhiem_vu
        - tong_cho_xu_ly
        - tong_dang_xu_ly
        - tong_hoan_thanh
    )

    # TÍNH TỶ LỆ BIỂU ĐỒ DONUT

    if tong_nhiem_vu > 0:
        ty_le_cho_xu_ly = round(
            tong_cho_xu_ly / tong_nhiem_vu * 100, 1
        )
        ty_le_dang_xu_ly = round(
            tong_dang_xu_ly / tong_nhiem_vu * 100, 1
        )
        ty_le_hoan_thanh = round(
            tong_hoan_thanh / tong_nhiem_vu * 100, 1
        )
        ty_le_khac = round(
            tong_khac / tong_nhiem_vu * 100, 1
        )
    else:
        ty_le_cho_xu_ly = 0
        ty_le_dang_xu_ly = 0
        ty_le_hoan_thanh = 0
        ty_le_khac = 0

    goc_cho_xu_ly = ty_le_cho_xu_ly
    goc_dang_xu_ly = goc_cho_xu_ly + ty_le_dang_xu_ly
    goc_hoan_thanh = goc_dang_xu_ly + ty_le_hoan_thanh

    # THỐNG KÊ NHIỆM VỤ THEO 5 THÁNG

    ngay_hien_tai = (
        timezone.localdate()
        if settings.USE_TZ
        else datetime.now().date()
    )

    chi_so_thang = (
        ngay_hien_tai.year * 12
        + ngay_hien_tai.month - 1
        - 4
    )

    nam_bat_dau = chi_so_thang // 12
    thang_bat_dau = chi_so_thang % 12 + 1

    ngay_bat_dau = datetime(nam_bat_dau, thang_bat_dau, 1)
    if settings.USE_TZ:
        ngay_bat_dau = timezone.make_aware(ngay_bat_dau)

    du_lieu_thang = NhiemVu.objects.filter(
        ngay_giao__gte=ngay_bat_dau
    ).annotate(
        thang=TruncMonth('ngay_giao')
    ).values(
        'thang'
    ).annotate(
        so_luong=Count('ma_nhiem_vu')
    ).order_by('thang')

    thong_ke_theo_thang = {}

    for item in du_lieu_thang:
        khoa_thang = (
            item['thang'].year,
            item['thang'].month
        )
        thong_ke_theo_thang[khoa_thang] = item['so_luong']

    du_lieu_bieu_do = []

    for i in range(5):
        chi_so = (
            nam_bat_dau * 12
            + thang_bat_dau - 1
            + i
        )

        nam = chi_so // 12
        thang = chi_so % 12 + 1

        so_luong = thong_ke_theo_thang.get(
            (nam, thang), 0
        )

        du_lieu_bieu_do.append({
            'nhan': f'T{thang}/{nam}',
            'so_luong': so_luong
        })

    gia_tri_lon_nhat = max(
        item['so_luong'] for item in du_lieu_bieu_do
    )

    if gia_tri_lon_nhat == 0:
        gia_tri_lon_nhat = 1

    cac_diem = []

    for i, item in enumerate(du_lieu_bieu_do):
        x = 40 + i * 130
        y = 180 - (
            item['so_luong'] / gia_tri_lon_nhat * 140
        )

        cac_diem.append({
            'x': x,
            'y': round(y, 2),
            'nhan': item['nhan'],
            'so_luong': item['so_luong']
        })

    duong_bieu_do = ' '.join(
        f"{item['x']},{item['y']}"
        for item in cac_diem
    )

    # THỐNG KÊ VĂN BẢN THEO NHÓM

    tong_van_ban_den = van_ban_den_qs.count()

    tong_van_ban_di = van_ban_di_qs.filter(
        ngay_ban_hanh__isnull=False
    ).count()

    tong_van_ban_du_thao = van_ban_di_qs.filter(
        ngay_ban_hanh__isnull=True
    ).count()

    du_lieu_nhom_van_ban = [
        {
            'nhan': 'Văn bản đến',
            'so_luong': tong_van_ban_den
        },
        {
            'nhan': 'Văn bản đi',
            'so_luong': tong_van_ban_di
        },
        {
            'nhan': 'Văn bản dự thảo',
            'so_luong': tong_van_ban_du_thao
        }
    ]

    gia_tri_lon_nhat_van_ban = max(
        item['so_luong']
        for item in du_lieu_nhom_van_ban
    )

    if gia_tri_lon_nhat_van_ban == 0:
        gia_tri_lon_nhat_van_ban = 1

    for item in du_lieu_nhom_van_ban:
        item['ty_le'] = round(
            item['so_luong']
            / gia_tri_lon_nhat_van_ban * 100,
            1
        )

    # DANH SÁCH NHIỆM VỤ ƯU TIÊN

    thoi_gian_hien_tai = timezone.now()

    danh_sach_nhiem_vu_uu_tien = NhiemVu.objects.select_related(
        'nguoi_nhan'
    ).exclude(
        trang_thai_nhiem_vu__in=[
            'Hoàn thành',
            'Đã hoàn thành'
        ]
    ).order_by(
        'han_xu_ly'
    )[:5]

    for nhiem_vu in danh_sach_nhiem_vu_uu_tien:
        nhiem_vu.da_qua_han = (
            nhiem_vu.han_xu_ly < thoi_gian_hien_tai
        )

    # DỮ LIỆU BỘ LỌC

    danh_sach_loai_van_ban = LoaiVanBan.objects.all().order_by(
        'ten_loai'
    )

    danh_sach_phong_ban = PhongBan.objects.all().order_by(
        'ten_phong_ban'
    )

    # DỮ LIỆU TRUYỀN SANG TEMPLATE

    context = {
        'tong_nguoi_dung': tong_nguoi_dung,
        'tong_vai_tro': tong_vai_tro,
        'tong_phong_ban': tong_phong_ban,
        'tong_loai_van_ban': tong_loai_van_ban,

        'tong_cho_xu_ly': tong_cho_xu_ly,
        'tong_dang_xu_ly': tong_dang_xu_ly,
        'tong_qua_han': tong_qua_han,
        'tong_hoan_thanh': tong_hoan_thanh,
        'tong_nhiem_vu': tong_nhiem_vu,
        'tong_khac': tong_khac,

        'ty_le_cho_xu_ly': ty_le_cho_xu_ly,
        'ty_le_dang_xu_ly': ty_le_dang_xu_ly,
        'ty_le_hoan_thanh': ty_le_hoan_thanh,
        'ty_le_khac': ty_le_khac,

        'goc_cho_xu_ly': goc_cho_xu_ly,
        'goc_dang_xu_ly': goc_dang_xu_ly,
        'goc_hoan_thanh': goc_hoan_thanh,

        'du_lieu_bieu_do': du_lieu_bieu_do,
        'cac_diem': cac_diem,
        'duong_bieu_do': duong_bieu_do,

        'du_lieu_nhom_van_ban': du_lieu_nhom_van_ban,
        'tong_van_ban_den': tong_van_ban_den,
        'tong_van_ban_di': tong_van_ban_di,
        'tong_van_ban_du_thao': tong_van_ban_du_thao,
        'gia_tri_lon_nhat_van_ban': gia_tri_lon_nhat_van_ban,

        'danh_sach_nhiem_vu_uu_tien': danh_sach_nhiem_vu_uu_tien,

        'tu_khoa': tu_khoa,
        'tu_ngay': tu_ngay,
        'den_ngay': den_ngay,
        'ma_loai_dang_chon': ma_loai,
        'ma_phong_ban_dang_chon': ma_phong_ban,
        'danh_sach_loai_van_ban': danh_sach_loai_van_ban,
        'danh_sach_phong_ban': danh_sach_phong_ban,

        'danh_sach_van_ban': danh_sach_van_ban_hien_thi,
        'tong_van_ban_tim_thay': tong_van_ban_tim_thay,
    }

    return render(
        request,
        'dashboard/dashboard.html',
        context
    )


# ==========================
# QUẢN LÝ NGƯỜI DÙNG
# ==========================

@login_required
def user_list(request):
    danh_sach_nguoi_dung = NguoiDung.objects.select_related(
        'vai_tro',
        'phong_ban'
    ).all().order_by('username')

    context = {
        'danh_sach_nguoi_dung': danh_sach_nguoi_dung,
    }

    return render(request, 'dashboard/user_list.html', context)


@login_required
def user_create(request):
    if request.method == 'POST':
        form = NguoiDungForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Thêm người dùng thành công!')
            return redirect('dashboard:user_list')
    else:
        form = NguoiDungForm()

    return render(request, 'dashboard/user_form.html', {'form': form})


@login_required
def user_update(request, user_id):
    nguoi_dung = get_object_or_404(NguoiDung, pk=user_id)

    if request.method == 'POST':
        form = NguoiDungUpdateForm(request.POST, instance=nguoi_dung)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Cập nhật thông tin người dùng thành công!'
            )
            return redirect('dashboard:user_list')
    else:
        form = NguoiDungUpdateForm(instance=nguoi_dung)

    context = {
        'form': form,
        'nguoi_dung': nguoi_dung,
    }

    return render(request, 'dashboard/user_update.html', context)


# ==========================
# QUẢN LÝ VAI TRÒ
# ==========================

@login_required
def role_list(request):
    danh_sach_vai_tro = VaiTro.objects.all().order_by('ma_vai_tro')

    return render(
        request,
        'dashboard/role_list.html',
        {'danh_sach_vai_tro': danh_sach_vai_tro}
    )


@login_required
def role_create(request):
    if request.method == 'POST':
        form = VaiTroForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Thêm vai trò thành công!')
            return redirect('dashboard:role_list')
    else:
        form = VaiTroForm()

    return render(request, 'dashboard/role_form.html', {'form': form})


@login_required
def role_update(request, ma_vai_tro):
    vai_tro = get_object_or_404(VaiTro, pk=ma_vai_tro)

    if request.method == 'POST':
        form = VaiTroForm(request.POST, instance=vai_tro)

        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật vai trò thành công!')
            return redirect('dashboard:role_list')
    else:
        form = VaiTroForm(instance=vai_tro)

    return render(
        request,
        'dashboard/role_update.html',
        {'form': form, 'vai_tro': vai_tro}
    )


# ==========================
# QUẢN LÝ PHÒNG BAN
# ==========================

@login_required
def department_list(request):
    danh_sach_phong_ban = PhongBan.objects.select_related(
        'ma_truong_bo_phan'
    ).all().order_by('ma_phong_ban')

    return render(
        request,
        'dashboard/department_list.html',
        {'danh_sach_phong_ban': danh_sach_phong_ban}
    )


@login_required
def department_create(request):
    if request.method == 'POST':
        form = PhongBanForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Thêm phòng ban thành công!')
            return redirect('dashboard:department_list')
    else:
        form = PhongBanForm()

    return render(
        request,
        'dashboard/department_form.html',
        {'form': form}
    )


@login_required
def department_update(request, ma_phong_ban):
    phong_ban = get_object_or_404(PhongBan, pk=ma_phong_ban)

    if request.method == 'POST':
        form = PhongBanForm(request.POST, instance=phong_ban)

        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật phòng ban thành công!')
            return redirect('dashboard:department_list')
    else:
        form = PhongBanForm(instance=phong_ban)

    return render(
        request,
        'dashboard/department_update.html',
        {'form': form, 'phong_ban': phong_ban}
    )


# ==========================
# QUẢN LÝ LOẠI VĂN BẢN
# ==========================

@login_required
def document_type_list(request):
    danh_sach_loai_van_ban = LoaiVanBan.objects.all().order_by('ma_loai')

    return render(
        request,
        'dashboard/document_type_list.html',
        {'danh_sach_loai_van_ban': danh_sach_loai_van_ban}
    )


@login_required
def document_type_create(request):
    if request.method == 'POST':
        form = LoaiVanBanForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Thêm loại văn bản thành công!')
            return redirect('dashboard:document_type_list')
    else:
        form = LoaiVanBanForm()

    return render(
        request,
        'dashboard/document_type_form.html',
        {'form': form}
    )


@login_required
def document_type_update(request, ma_loai):
    loai_van_ban = get_object_or_404(LoaiVanBan, pk=ma_loai)

    if request.method == 'POST':
        form = LoaiVanBanForm(request.POST, instance=loai_van_ban)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Cập nhật loại văn bản thành công!'
            )
            return redirect('dashboard:document_type_list')
    else:
        form = LoaiVanBanForm(instance=loai_van_ban)

    return render(
        request,
        'dashboard/document_type_update.html',
        {'form': form, 'loai_van_ban': loai_van_ban}
    )


# ==========================
# TRANG CHỦ QUẢN TRỊ HỆ THỐNG
# ==========================

@login_required
def system_management_home(request):
    return render(
        request,
        'dashboard/quan_tri_he_thong.html'
    )


# ==========================
# KHO MẪU VĂN BẢN
# ==========================

@login_required
def template_list(request):
    tu_khoa = request.GET.get('q', '').strip()
    ma_loai = request.GET.get('loai_van_ban', '').strip()
    nam = request.GET.get('nam', '').strip()

    danh_sach_mau = MauVanBan.objects.select_related(
        'ma_loai'
    ).all()

    if tu_khoa:
        danh_sach_mau = danh_sach_mau.filter(
            Q(ten_mau__icontains=tu_khoa)
            | Q(ma_mau__icontains=tu_khoa)
            | Q(can_cu__icontains=tu_khoa)
        )

    if ma_loai:
        danh_sach_mau = danh_sach_mau.filter(
            ma_loai_id=ma_loai
        )

    if nam:
        try:
            danh_sach_mau = danh_sach_mau.filter(
                ngay_cap_nhat__year=int(nam)
            )
        except ValueError:
            nam = ''

    paginator = Paginator(danh_sach_mau, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    danh_sach_loai_van_ban = LoaiVanBan.objects.all().order_by(
        'ten_loai'
    )

    danh_sach_nam = MauVanBan.objects.dates(
        'ngay_cap_nhat',
        'year',
        order='DESC'
    )

    context = {
        'danh_sach_mau': page_obj,
        'page_obj': page_obj,
        'danh_sach_loai_van_ban': danh_sach_loai_van_ban,
        'danh_sach_nam': danh_sach_nam,
        'tu_khoa': tu_khoa,
        'ma_loai_dang_chon': ma_loai,
        'nam_dang_chon': nam,
    }

    return render(
        request,
        'dashboard/template_list.html',
        context
    )


@login_required
def template_create(request):
    if request.method == 'POST':
        form = MauVanBanForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Thêm mẫu văn bản thành công!'
            )
            return redirect('dashboard:template_list')
    else:
        form = MauVanBanForm()

    return render(
        request,
        'dashboard/template_form.html',
        {'form': form}
    )


@login_required
def template_detail(request, ma_mau):
    mau_van_ban = get_object_or_404(
        MauVanBan.objects.select_related('ma_loai'),
        pk=ma_mau
    )

    return render(
        request,
        'dashboard/template_detail.html',
        {
            'mau_van_ban': mau_van_ban,
            'mau': mau_van_ban
        }
    )


@login_required
def template_update(request, ma_mau):
    mau_van_ban = get_object_or_404(
        MauVanBan,
        pk=ma_mau
    )

    if request.method == 'POST':
        form = MauVanBanForm(
            request.POST,
            request.FILES,
            instance=mau_van_ban
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Cập nhật mẫu văn bản thành công!'
            )
            return redirect('dashboard:template_list')
    else:
        form = MauVanBanForm(
            instance=mau_van_ban
        )

    return render(
        request,
        'dashboard/template_update.html',
        {
            'form': form,
            'mau_van_ban': mau_van_ban
        }
    )


@login_required
@require_POST
def template_delete(request, ma_mau):
    mau_van_ban = get_object_or_404(
        MauVanBan,
        pk=ma_mau
    )

    if mau_van_ban.file_mau:
        mau_van_ban.file_mau.delete(save=False)

    mau_van_ban.delete()

    messages.success(
        request,
        'Xóa mẫu văn bản thành công!'
    )

    return redirect('dashboard:template_list')


@login_required
def template_download(request, ma_mau):
    mau_van_ban = get_object_or_404(
        MauVanBan,
        pk=ma_mau
    )

    if not mau_van_ban.file_mau:
        raise Http404(
            'Mẫu văn bản chưa có file đính kèm.'
        )

    ten_file = os.path.basename(
        mau_van_ban.file_mau.name
    )

    return FileResponse(
        mau_van_ban.file_mau.open('rb'),
        as_attachment=True,
        filename=ten_file
    )


# ==========================
# THÔNG BÁO & CẢNH BÁO
# ==========================

def _lay_nhiem_vu_duoc_phep_xem(request):
    """
    Chỉ lấy nhiệm vụ được giao trực tiếp cho người dùng
    hoặc nhiệm vụ của phòng ban mà người dùng phụ trách.
    """

    queryset = NhiemVu.objects.select_related(
        'nguoi_nhan',
        'phong_ban_nhan',
        'ma_van_ban_den',
        'ma_van_ban_di'
    ).exclude(
        trang_thai_nhiem_vu__in=[
            'Hoàn thành',
            'Đã hoàn thành'
        ]
    )

    if request.user.is_superuser or request.user.is_staff:
        return queryset

    dieu_kien = Q(nguoi_nhan=request.user)

    if request.user.phong_ban_id:
        dieu_kien |= Q(
            nguoi_nhan__isnull=True,
            phong_ban_nhan_id=request.user.phong_ban_id
        )

    return queryset.filter(dieu_kien)


def _tao_ma_thong_bao_nhiem_vu(nguoi_dung_id, nhiem_vu_id):
    """
    Tạo mã thông báo ổn định theo người dùng và nhiệm vụ.
    """

    noi_dung = f'{nguoi_dung_id}:{nhiem_vu_id}'

    return hashlib.sha256(
        noi_dung.encode('utf-8')
    ).hexdigest()[:10].upper()


def _dong_bo_thong_bao_nhiem_vu(
    request,
    nhiem_vu_qs,
    thoi_gian_hien_tai,
    moc_sap_den_han
):
    """
    Tạo và cập nhật cảnh báo nhiệm vụ cá nhân.

    Thông báo nhiệm vụ luôn gắn với người nhận cụ thể,
    không được chia sẻ công khai hoặc theo vai trò.
    """

    cac_ma_thong_bao_dang_hop_le = set()

    for nhiem_vu in nhiem_vu_qs.filter(
        han_xu_ly__lte=moc_sap_den_han
    ).order_by('han_xu_ly'):

        if nhiem_vu.han_xu_ly < thoi_gian_hien_tai:
            loai_thong_bao = 'QUA_HAN'
            tieu_de = f'Nhiệm vụ quá hạn: {nhiem_vu.tieu_de}'

            noi_dung = (
                f'Nhiệm vụ "{nhiem_vu.tieu_de}" đã quá hạn xử lý. '
                f'Hạn xử lý: '
                f'{timezone.localtime(nhiem_vu.han_xu_ly).strftime("%d/%m/%Y %H:%M")}. '
                f'Vui lòng kiểm tra và xử lý nhiệm vụ.'
            )

        else:
            loai_thong_bao = 'SAP_DEN_HAN'
            tieu_de = f'Nhiệm vụ sắp đến hạn: {nhiem_vu.tieu_de}'

            noi_dung = (
                f'Nhiệm vụ "{nhiem_vu.tieu_de}" sắp đến hạn xử lý. '
                f'Hạn xử lý: '
                f'{timezone.localtime(nhiem_vu.han_xu_ly).strftime("%d/%m/%Y %H:%M")}. '
                f'Vui lòng hoàn thành đúng thời hạn.'
            )

        ma_thong_bao = _tao_ma_thong_bao_nhiem_vu(
            request.user.pk,
            nhiem_vu.pk
        )

        cac_ma_thong_bao_dang_hop_le.add(ma_thong_bao)

        ThongBao.objects.update_or_create(
            ma_thong_bao=ma_thong_bao,
            defaults={
                'tieu_de': tieu_de,
                'noi_dung': noi_dung,
                'loai_thong_bao': loai_thong_bao,
                'nguoi_nhan': request.user,
                'nhiem_vu': nhiem_vu,
                'cong_khai': False,
            }
        )

    # Xóa những cảnh báo tự động không còn hợp lệ.

    cac_thong_bao_nhiem_vu = ThongBao.objects.filter(
        nguoi_nhan=request.user,
        nhiem_vu__isnull=False
    ).select_related('nhiem_vu')

    for thong_bao in cac_thong_bao_nhiem_vu:
        ma_du_kien = _tao_ma_thong_bao_nhiem_vu(
            request.user.pk,
            thong_bao.nhiem_vu_id
        )

        if (
            thong_bao.ma_thong_bao == ma_du_kien
            and thong_bao.ma_thong_bao not in cac_ma_thong_bao_dang_hop_le
        ):
            thong_bao.delete()


def _lay_thong_bao_duoc_phep_xem(request, ma_vai_tro=None):
    """
    Lấy các thông báo được phép hiển thị:

    - Thông báo cá nhân của người dùng hiện tại.
    - Thông báo công khai.
    - Thông báo chung dành cho vai trò được chọn.

    Thông báo liên quan đến nhiệm vụ luôn được giữ riêng tư.
    """

    dieu_kien = (
        Q(nguoi_nhan=request.user)
        | Q(
            cong_khai=True,
            nhiem_vu__isnull=True
        )
    )

    if ma_vai_tro:
        dieu_kien |= Q(
            vai_tro_nhan__ma_vai_tro=ma_vai_tro,
            nhiem_vu__isnull=True
        )

    return ThongBao.objects.filter(
        dieu_kien
    ).select_related(
        'nguoi_nhan',
        'nhiem_vu',
        'mau_van_ban'
    ).prefetch_related(
        'vai_tro_nhan'
    ).distinct()


@login_required
def notification_list(request):
    thoi_gian_hien_tai = timezone.now()
    moc_sap_den_han = thoi_gian_hien_tai + timedelta(days=3)

    tab_dang_chon = request.GET.get('tab', 'all')
    vai_tro_dang_chon = request.GET.get('vai_tro', '').strip()

    cac_tab_hop_le = [
        'all',
        'QUA_HAN',
        'SAP_DEN_HAN',
        'HE_THONG'
    ]

    if tab_dang_chon not in cac_tab_hop_le:
        tab_dang_chon = 'all'

    # LẤY VÀ ĐỒNG BỘ NHIỆM VỤ CÁ NHÂN

    nhiem_vu_qs = _lay_nhiem_vu_duoc_phep_xem(request)

    _dong_bo_thong_bao_nhiem_vu(
        request,
        nhiem_vu_qs,
        thoi_gian_hien_tai,
        moc_sap_den_han
    )

    # KIỂM TRA VAI TRÒ ĐƯỢC CHỌN

    danh_sach_vai_tro = VaiTro.objects.all().order_by(
        'ma_vai_tro'
    )

    if vai_tro_dang_chon:
        vai_tro_hop_le = danh_sach_vai_tro.filter(
            ma_vai_tro=vai_tro_dang_chon
        ).exists()

        if not vai_tro_hop_le:
            vai_tro_dang_chon = ''

    # LẤY THÔNG BÁO CÔNG KHAI, THEO VAI TRÒ
    # VÀ THÔNG BÁO CÁ NHÂN CỦA NGƯỜI DÙNG

    thong_bao_he_thong = _lay_thong_bao_duoc_phep_xem(
        request,
        vai_tro_dang_chon
    ).order_by('-ngay_tao')

    # LẤY CÁC THÔNG BÁO CHUNG ĐÃ ĐỌC BỞI TÀI KHOẢN HIỆN TẠI

    cac_ma_thong_bao_da_doc = set(
        ThongBaoDaDoc.objects.filter(
            nguoi_dung=request.user,
            thong_bao__in=thong_bao_he_thong
        ).values_list(
            'thong_bao_id',
            flat=True
        )
    )

    # TẠO DANH SÁCH THÔNG BÁO DẠNG CHUNG

    danh_sach_thong_bao = []

    for thong_bao in thong_bao_he_thong:

        if thong_bao.nguoi_nhan_id == request.user.pk:
            da_doc = thong_bao.da_doc
        else:
            da_doc = thong_bao.pk in cac_ma_thong_bao_da_doc

        danh_sach_thong_bao.append({
            'ma_thong_bao': str(thong_bao.pk),
            'tieu_de': thong_bao.tieu_de,
            'noi_dung': thong_bao.noi_dung,
            'loai_thong_bao': thong_bao.loai_thong_bao,
            'ngay_hien_thi': thong_bao.ngay_tao,
            'da_doc': da_doc,
            'la_nhiem_vu': thong_bao.nhiem_vu_id is not None,
            'doi_tuong': thong_bao,
        })

    # LỌC THEO TAB

    if tab_dang_chon != 'all':
        danh_sach_thong_bao = [
            item for item in danh_sach_thong_bao
            if item['loai_thong_bao'] == tab_dang_chon
        ]

    # PHÂN TRANG

    paginator = Paginator(danh_sach_thong_bao, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    # THỐNG KÊ THEO NHÓM THÔNG BÁO ĐANG ĐƯỢC HIỂN THỊ

    tong_qua_han = thong_bao_he_thong.filter(
        loai_thong_bao='QUA_HAN'
    ).count()

    tong_sap_den_han = thong_bao_he_thong.filter(
        loai_thong_bao='SAP_DEN_HAN'
    ).count()

    tong_he_thong = thong_bao_he_thong.filter(
        loai_thong_bao='HE_THONG'
    ).count()

    context = {
        'danh_sach_thong_bao': page_obj,
        'page_obj': page_obj,
        'tab_dang_chon': tab_dang_chon,

        'tong_qua_han': tong_qua_han,
        'tong_sap_den_han': tong_sap_den_han,
        'tong_he_thong': tong_he_thong,

        'danh_sach_vai_tro': danh_sach_vai_tro,
        'vai_tro_dang_chon': vai_tro_dang_chon,
    }

    return render(
        request,
        'dashboard/notification_list.html',
        context
    )


@login_required
def notification_detail(request, ma_thong_bao):

    # HỖ TRỢ LIÊN KẾT CŨ TỪ THÔNG BÁO NHIỆM VỤ

    if ma_thong_bao.startswith('NV__'):
        ma_nhiem_vu = ma_thong_bao[4:]

        nhiem_vu = get_object_or_404(
            _lay_nhiem_vu_duoc_phep_xem(request),
            pk=ma_nhiem_vu
        )

        return render(
            request,
            'dashboard/notification_detail.html',
            {
                'la_nhiem_vu': True,
                'nhiem_vu': nhiem_vu,
            }
        )

    # LẤY VAI TRÒ ĐƯỢC TRUYỀN TỪ ĐƯỜNG DẪN

    ma_vai_tro = request.GET.get('vai_tro', '').strip()

    # CHỈ CHẤP NHẬN MÃ VAI TRÒ CÓ TRONG HỆ THỐNG

    if ma_vai_tro:
        vai_tro_hop_le = VaiTro.objects.filter(
            ma_vai_tro=ma_vai_tro
        ).exists()

        if not vai_tro_hop_le:
            ma_vai_tro = ''

    # LẤY THÔNG BÁO ĐƯỢC PHÉP XEM

    thong_bao = get_object_or_404(
        _lay_thong_bao_duoc_phep_xem(
            request,
            ma_vai_tro
        ),
        pk=ma_thong_bao
    )

    # ĐÁNH DẤU ĐÃ ĐỌC RIÊNG CHO TÀI KHOẢN HIỆN TẠI

    if thong_bao.nguoi_nhan_id == request.user.pk:
        if not thong_bao.da_doc:
            thong_bao.da_doc = True
            thong_bao.save(update_fields=['da_doc'])
    else:
        ThongBaoDaDoc.objects.get_or_create(
            thong_bao=thong_bao,
            nguoi_dung=request.user
        )

    # NẾU LÀ THÔNG BÁO NHIỆM VỤ

    if thong_bao.nhiem_vu_id:
        nhiem_vu = get_object_or_404(
            _lay_nhiem_vu_duoc_phep_xem(request),
            pk=thong_bao.nhiem_vu_id
        )

        context = {
            'la_nhiem_vu': True,
            'nhiem_vu': nhiem_vu,
            'thong_bao': thong_bao,
        }

    else:
        context = {
            'la_nhiem_vu': False,
            'thong_bao': thong_bao,
        }

    return render(
        request,
        'dashboard/notification_detail.html',
        context
    )


@login_required
@require_POST
def notification_mark_read(request, ma_thong_bao):

    # HỖ TRỢ LIÊN KẾT CŨ
    if ma_thong_bao.startswith('NV__'):
        return redirect('dashboard:notification_list')

    # LẤY VÀ KIỂM TRA VAI TRÒ ĐƯỢC GỬI TỪ BIỂU MẪU
    ma_vai_tro = request.POST.get('vai_tro', '').strip()

    if ma_vai_tro:
        vai_tro_hop_le = VaiTro.objects.filter(
            ma_vai_tro=ma_vai_tro
        ).exists()

        if not vai_tro_hop_le:
            ma_vai_tro = ''

    # LẤY THÔNG BÁO ĐƯỢC PHÉP XEM
    thong_bao = get_object_or_404(
        _lay_thong_bao_duoc_phep_xem(
            request,
            ma_vai_tro
        ),
        pk=ma_thong_bao
    )

    # THÔNG BÁO CÁ NHÂN
    if thong_bao.nguoi_nhan_id == request.user.pk:
        if not thong_bao.da_doc:
            thong_bao.da_doc = True
            thong_bao.save(update_fields=['da_doc'])

    # THÔNG BÁO CÔNG KHAI HOẶC THEO VAI TRÒ
    else:
        ThongBaoDaDoc.objects.get_or_create(
            thong_bao=thong_bao,
            nguoi_dung=request.user
        )

    messages.success(
        request,
        'Đã đánh dấu thông báo là đã đọc.'
    )

    # GIỮ LẠI TAB VÀ BỘ LỌC ĐANG SỬ DỤNG
    from urllib.parse import urlencode

    tab_dang_chon = request.POST.get('tab', 'all')

    if tab_dang_chon not in [
        'all',
        'QUA_HAN',
        'SAP_DEN_HAN',
        'HE_THONG'
    ]:
        tab_dang_chon = 'all'

    tham_so = urlencode({
        'tab': tab_dang_chon,
        'vai_tro': ma_vai_tro
    })

    return redirect(
        f'/dashboard/thong-bao/?{tham_so}'
    )




@login_required
@require_POST
def notification_mark_all_read(request):

    # CHỈ ĐÁNH DẤU CÁC THÔNG BÁO CÁ NHÂN CỦA NGƯỜI DÙNG

    ThongBao.objects.filter(
        nguoi_nhan=request.user,
        da_doc=False
    ).update(
        da_doc=True
    )

    messages.success(
        request,
        'Đã đánh dấu tất cả thông báo cá nhân là đã đọc.'
    )

    return redirect('dashboard:notification_list')
