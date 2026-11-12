
from django.db import models


class MauVanBan(models.Model):
    ma_mau = models.CharField(
        max_length=10,
        primary_key=True,
        verbose_name='Mã mẫu'
    )

    ten_mau = models.CharField(
        max_length=200,
        verbose_name='Tên mẫu văn bản'
    )

    ma_loai = models.ForeignKey(
        'quanly.LoaiVanBan',
        on_delete=models.PROTECT,
        related_name='cac_mau_van_ban',
        verbose_name='Loại văn bản'
    )

    can_cu = models.CharField(
        max_length=200,
        default='Nghị định 30/2020/NĐ-CP',
        verbose_name='Căn cứ pháp lý'
    )

    file_mau = models.FileField(
        upload_to='mau_van_ban/',
        blank=True,
        null=True,
        verbose_name='File mẫu'
    )

    mo_ta = models.TextField(
        blank=True,
        null=True,
        verbose_name='Mô tả'
    )

    ngay_cap_nhat = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )

    def __str__(self):
        return self.ten_mau

    class Meta:
        verbose_name = 'Mẫu văn bản'
        verbose_name_plural = 'Kho mẫu văn bản'
        ordering = ['-ngay_cap_nhat']


class ThongBao(models.Model):
    LOAI_THONG_BAO = [
        ('QUA_HAN', 'Văn bản quá hạn'),
        ('SAP_DEN_HAN', 'Sắp đến hạn'),
        ('HE_THONG', 'Thông báo hệ thống'),
    ]

    ma_thong_bao = models.CharField(
        max_length=10,
        primary_key=True,
        verbose_name='Mã thông báo'
    )

    tieu_de = models.CharField(
        max_length=255,
        verbose_name='Tiêu đề thông báo'
    )

    noi_dung = models.TextField(
        verbose_name='Nội dung thông báo'
    )

    loai_thong_bao = models.CharField(
        max_length=20,
        choices=LOAI_THONG_BAO,
        verbose_name='Loại thông báo'
    )

    nguoi_nhan = models.ForeignKey(
        'quanly.NguoiDung',
        on_delete=models.CASCADE,
        related_name='cac_thong_bao',
        null=True,
        blank=True,
        verbose_name='Người nhận'
    )

    cong_khai = models.BooleanField(
        default=False,
        verbose_name='Thông báo công khai'
    )

    vai_tro_nhan = models.ManyToManyField(
        'quanly.VaiTro',
        blank=True,
        related_name='cac_thong_bao',
        verbose_name='Vai trò nhận thông báo'
    )

    nhiem_vu = models.ForeignKey(
        'quanly.NhiemVu',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cac_thong_bao',
        verbose_name='Nhiệm vụ liên quan'
    )

    mau_van_ban = models.ForeignKey(
        'dashboard.MauVanBan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cac_thong_bao',
        verbose_name='Mẫu văn bản liên quan'
    )

    # Giữ lại để tương thích với chức năng thông báo cá nhân hiện tại.
    da_doc = models.BooleanField(
        default=False,
        verbose_name='Đã đọc'
    )

    ngay_tao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )

    def __str__(self):
        return self.tieu_de

    class Meta:
        verbose_name = 'Thông báo'
        verbose_name_plural = 'Thông báo hệ thống'
        ordering = ['-ngay_tao']


class ThongBaoDaDoc(models.Model):
    """
    Lưu trạng thái đã đọc của từng người dùng đối với từng thông báo.
    Mỗi người dùng có trạng thái đọc độc lập.
    """

    thong_bao = models.ForeignKey(
        'dashboard.ThongBao',
        on_delete=models.CASCADE,
        related_name='trang_thai_da_doc',
        verbose_name='Thông báo'
    )

    nguoi_dung = models.ForeignKey(
        'quanly.NguoiDung',
        on_delete=models.CASCADE,
        related_name='cac_thong_bao_da_doc',
        verbose_name='Người dùng'
    )

    ngay_doc = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày đọc'
    )

    def __str__(self):
        return f'{self.nguoi_dung} - {self.thong_bao}'

    class Meta:
        verbose_name = 'Trạng thái đọc thông báo'
        verbose_name_plural = 'Trạng thái đọc thông báo'
        constraints = [
            models.UniqueConstraint(
                fields=['thong_bao', 'nguoi_dung'],
                name='unique_thong_bao_nguoi_dung_da_doc'
            )
        ]
