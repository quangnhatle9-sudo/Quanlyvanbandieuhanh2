from django.urls import path
from . import views

urlpatterns = [
    # UC3.2: Phân bổ nhiệm vụ chi tiết (Tổ trưởng)
    path('tu-bgh/', views.nhiem_vu_tu_bgh_view, name='nhiem_vu_tu_bgh'),
    path('phan-bo/<str:ma_phan_cong>/', views.giao_viec_view, name='giao_viec'),

    # UC3.3: Bàn làm việc & Nộp báo cáo (Giáo viên / Nhân viên)
    path('ban-lam-viec/', views.ban_lam_viec_ca_nhan_view, name='ban_lam_viec_ca_nhan'),
    path('<str:ma_nhiem_vu>/tiep-nhan/', views.tiep_nhan_nhiem_vu_view, name='tiep_nhan_nhiem_vu'),
    path('<str:ma_nhiem_vu>/nop-bao-cao/', views.nop_bao_cao_view, name='nop_bao_cao'),

    # UC3.4: Kiểm duyệt 2 cấp (Tổ trưởng & Ban Giám hiệu)
    path('kiem-duyet/', views.kiem_duyet_danh_sach_view, name='kiem_duyet_danh_sach'),
    path('<str:ma_nhiem_vu>/tham-dinh/', views.chi_tiet_duyet_view, name='chi_tiet_duyet'),
]
