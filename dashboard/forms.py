
from django import forms
from quanly.models import NguoiDung, VaiTro, PhongBan, LoaiVanBan
from .models import MauVanBan

# ==========================
# FORM QUẢN LÝ NGƯỜI DÙNG
# ==========================

# Form thêm người dùng
class NguoiDungForm(forms.ModelForm):
    mat_khau = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput,
        min_length=8
    )

    xac_nhan_mat_khau = forms.CharField(
        label='Xác nhận mật khẩu',
        widget=forms.PasswordInput
    )

    class Meta:
        model = NguoiDung
        fields = [
            'ho_ten',
            'username',
            'email',
            'vai_tro',
            'phong_ban'
        ]

        labels = {
            'ho_ten': 'Họ và tên',
            'username': 'Tên đăng nhập',
            'email': 'Địa chỉ email',
            'vai_tro': 'Vai trò',
            'phong_ban': 'Phòng ban',
        }

        widgets = {
            'ho_ten': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập họ và tên'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tên đăng nhập'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập địa chỉ email'
            }),
            'vai_tro': forms.Select(attrs={
                'class': 'form-select'
            }),
            'phong_ban': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        mat_khau = cleaned_data.get('mat_khau')
        xac_nhan_mat_khau = cleaned_data.get('xac_nhan_mat_khau')

        if mat_khau and xac_nhan_mat_khau:
            if mat_khau != xac_nhan_mat_khau:
                self.add_error(
                    'xac_nhan_mat_khau',
                    'Mật khẩu xác nhận không khớp.'
                )

        return cleaned_data

    def save(self, commit=True):
        nguoi_dung = super().save(commit=False)
        nguoi_dung.set_password(self.cleaned_data['mat_khau'])

        if commit:
            nguoi_dung.save()

        return nguoi_dung


# Form chỉnh sửa người dùng
class NguoiDungUpdateForm(forms.ModelForm):

    class Meta:
        model = NguoiDung
        fields = [
            'ho_ten',
            'username',
            'email',
            'vai_tro',
            'phong_ban'
        ]

        labels = {
            'ho_ten': 'Họ và tên',
            'username': 'Tên đăng nhập',
            'email': 'Địa chỉ email',
            'vai_tro': 'Vai trò',
            'phong_ban': 'Phòng ban',
        }

        widgets = {
            'ho_ten': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập họ và tên'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tên đăng nhập'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập địa chỉ email'
            }),
            'vai_tro': forms.Select(attrs={
                'class': 'form-select'
            }),
            'phong_ban': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


# ==========================
# FORM QUẢN LÝ VAI TRÒ
# ==========================

class VaiTroForm(forms.ModelForm):

    class Meta:
        model = VaiTro
        fields = [
            'ma_vai_tro',
            'ten_vai_tro',
            'mo_ta'
        ]

        labels = {
            'ma_vai_tro': 'Mã vai trò',
            'ten_vai_tro': 'Tên vai trò',
            'mo_ta': 'Mô tả',
        }

        widgets = {
            'ma_vai_tro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập mã vai trò'
            }),
            'ten_vai_tro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tên vai trò'
            }),
            'mo_ta': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập mô tả vai trò',
                'rows': 3
            }),
        }


# ==========================
# FORM QUẢN LÝ PHÒNG BAN
# ==========================

class PhongBanForm(forms.ModelForm):

    class Meta:
        model = PhongBan
        fields = [
            'ma_phong_ban',
            'ten_phong_ban',
            'loai_don_vi',
            'ma_truong_bo_phan'
        ]

        labels = {
            'ma_phong_ban': 'Mã phòng ban',
            'ten_phong_ban': 'Tên phòng ban',
            'loai_don_vi': 'Loại đơn vị',
            'ma_truong_bo_phan': 'Trưởng bộ phận',
        }

        widgets = {
            'ma_phong_ban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập mã phòng ban'
            }),
            'ten_phong_ban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tên phòng ban'
            }),
            'loai_don_vi': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập loại đơn vị'
            }),
            'ma_truong_bo_phan': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['ma_truong_bo_phan'].empty_label = '-- Chọn trưởng bộ phận --'


# ==========================
# FORM QUẢN LÝ LOẠI VĂN BẢN
# ==========================

class LoaiVanBanForm(forms.ModelForm):

    class Meta:
        model = LoaiVanBan
        fields = [
            'ma_loai',
            'ten_loai',
            'mo_ta'
        ]

        labels = {
            'ma_loai': 'Mã loại văn bản',
            'ten_loai': 'Tên loại văn bản',
            'mo_ta': 'Mô tả',
        }

        widgets = {
            'ma_loai': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập mã loại văn bản'
            }),
            'ten_loai': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tên loại văn bản'
            }),
            'mo_ta': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập mô tả',
                'rows': 3
            }),
        }

# ==========================
# FORM QUẢN LÝ KHO MẪU VĂN BẢN
# ==========================

class MauVanBanForm(forms.ModelForm):

    class Meta:
        model = MauVanBan
        fields = [
            'ma_mau',
            'ten_mau',
            'ma_loai',
            'can_cu',
            'file_mau',
            'mo_ta'
        ]

        labels = {
            'ma_mau': 'Mã mẫu văn bản',
            'ten_mau': 'Tên mẫu văn bản',
            'ma_loai': 'Loại văn bản',
            'can_cu': 'Căn cứ pháp lý',
            'file_mau': 'File mẫu văn bản',
            'mo_ta': 'Mô tả',
        }

        widgets = {
            'ma_mau': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập mã mẫu văn bản'
            }),
            'ten_mau': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tên mẫu văn bản'
            }),
            'ma_loai': forms.Select(attrs={
                'class': 'form-select'
            }),
            'can_cu': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ví dụ: Nghị định 30/2020/NĐ-CP'
            }),
            'file_mau': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'mo_ta': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập mô tả mẫu văn bản',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['ma_loai'].empty_label = '-- Chọn loại văn bản --'
