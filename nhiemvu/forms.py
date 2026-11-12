from django import forms
from django.utils import timezone
from quanly.models import NguoiDung, NhiemVu, BaoCaoKetQua

class PhanBoTaskForm(forms.Form):
    tieu_de = forms.CharField(
        label='Tên đầu việc / Nhiệm vụ cụ thể',
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ví dụ: Soạn ma trận đề thi học kỳ I môn Toán',
            'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none'
        }),
        required=True
    )
    noi_dung_yeu_cau = forms.CharField(
        label='Nội dung yêu cầu chi tiết',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Chi tiết yêu cầu chuyên môn, tiêu chí cần hoàn thành...',
            'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none'
        }),
        required=True
    )
    nguoi_nhan = forms.ModelChoiceField(
        label='Cán bộ phụ trách chính (Trong tổ)',
        queryset=NguoiDung.objects.none(),
        empty_label='-- Chọn Giáo viên / Nhân viên phụ trách chính --',
        widget=forms.Select(attrs={
            'class': 'w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none'
        }),
        required=True
    )
    nguoi_phoi_hop = forms.ModelChoiceField(
        label='Cán bộ phối hợp (tùy chọn)',
        queryset=NguoiDung.objects.none(),
        empty_label='-- Chọn Cán bộ phối hợp (Nếu có) --',
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none'
        })
    )
    han_xu_ly = forms.DateTimeField(
        label='Hạn xử lý của task',
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none'
        }),
        required=True
    )

    def __init__(self, *args, **kwargs):
        self.to_truong = kwargs.pop('to_truong', None)
        self.phan_cong = kwargs.pop('phan_cong', None)
        super().__init__(*args, **kwargs)

        # Lọc danh sách thành viên trong tổ của Tổ trưởng
        if self.to_truong and self.to_truong.phong_ban:
            members = NguoiDung.objects.filter(phong_ban=self.to_truong.phong_ban)
            self.fields['nguoi_nhan'].queryset = members
            self.fields['nguoi_phoi_hop'].queryset = members
        else:
            self.fields['nguoi_nhan'].queryset = NguoiDung.objects.all()
            self.fields['nguoi_phoi_hop'].queryset = NguoiDung.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        han_task = cleaned_data.get('han_xu_ly')

        # Business Rule E1: Hạn xử lý không được vượt quá hạn do BGH ấn định
        if han_task and self.phan_cong and self.phan_cong.han_xu_ly:
            if han_task > self.phan_cong.han_xu_ly:
                han_bgh_str = self.phan_cong.han_xu_ly.strftime('%H:%M %d/%m/%Y')
                self.add_error(
                    'han_xu_ly',
                    f'Hạn xử lý không được vượt quá hạn của Ban Giám hiệu ({han_bgh_str}). Vui lòng chọn lại.'
                )

        if han_task and han_task < timezone.now():
            self.add_error('han_xu_ly', 'Hạn xử lý không được trước thời điểm hiện tại.')

        return cleaned_data


class NopBaoCaoForm(forms.Form):
    noi_dung_bao_cao = forms.CharField(
        label='Nội dung báo cáo tóm tắt',
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Mô tả tóm tắt kết quả thực hiện nhiệm vụ, sản phẩm đính kèm...',
            'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none'
        }),
        required=True
    )
    file_ket_qua = forms.FileField(
        label='Tệp kết quả / Minh chứng đính kèm (PDF, Word, Excel, ZIP)',
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs'
        })
    )


class DuyetBaoCaoForm(forms.Form):
    CHOICES = [
        ('DAT', 'Xác nhận Đạt (Chuyển duyệt / Ký hoàn tất)'),
        ('TRA_LAI', 'Chưa đạt (Yêu cầu chỉnh sửa / Trả lại)'),
    ]
    quyet_dinh = forms.ChoiceField(
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'text-blue-600 focus:ring-blue-500'}),
        initial='DAT'
    )
    nhan_xet = forms.CharField(
        label='Ý kiến nhận xét / Lý do',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Nhập ý kiến nhận xét đánh giá hoặc lý do yêu cầu chỉnh sửa...',
            'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none'
        }),
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        quyet_dinh = cleaned_data.get('quyet_dinh')
        nhan_xet = cleaned_data.get('nhan_xet')

        # Business Rule: Trả lại bắt buộc kèm lý do (nhận xét)
        if quyet_dinh == 'TRA_LAI' and not nhan_xet:
            self.add_error('nhan_xet', 'Vui lòng nhập ý kiến nhận xét / lý do khi yêu cầu chỉnh sửa.')

        return cleaned_data
