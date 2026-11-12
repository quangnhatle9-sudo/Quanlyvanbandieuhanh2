
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # ==========================
    # TRANG TỔNG QUAN
    # ==========================
    path('', views.dashboard_home, name='home'),

    # ==========================
    # TRANG CHỦ QUẢN TRỊ HỆ THỐNG
    # ==========================
    path(
        'quan-tri/',
        views.system_management_home,
        name='system_management_home'
    ),

    # ==========================
    # QUẢN LÝ NGƯỜI DÙNG
    # ==========================
    path('nguoi-dung/', views.user_list, name='user_list'),
    path('nguoi-dung/them/', views.user_create, name='user_create'),
    path(
        'nguoi-dung/<int:user_id>/sua/',
        views.user_update,
        name='user_update'
    ),

    # ==========================
    # QUẢN LÝ VAI TRÒ
    # ==========================
    path('vai-tro/', views.role_list, name='role_list'),
    path('vai-tro/them/', views.role_create, name='role_create'),
    path(
        'vai-tro/<str:ma_vai_tro>/sua/',
        views.role_update,
        name='role_update'
    ),

    # ==========================
    # QUẢN LÝ PHÒNG BAN
    # ==========================
    path('phong-ban/', views.department_list, name='department_list'),
    path('phong-ban/them/', views.department_create, name='department_create'),
    path(
        'phong-ban/<str:ma_phong_ban>/sua/',
        views.department_update,
        name='department_update'
    ),

    # ==========================
    # QUẢN LÝ LOẠI VĂN BẢN
    # ==========================
    path(
        'loai-van-ban/',
        views.document_type_list,
        name='document_type_list'
    ),
    path(
        'loai-van-ban/them/',
        views.document_type_create,
        name='document_type_create'
    ),
    path(
        'loai-van-ban/<str:ma_loai>/sua/',
        views.document_type_update,
        name='document_type_update'
    ),

    # ==========================
    # KHO MẪU VĂN BẢN
    # ==========================
    path(
        'kho-mau-van-ban/',
        views.template_list,
        name='template_list'
    ),
    path(
        'kho-mau-van-ban/them/',
        views.template_create,
        name='template_create'
    ),
    path(
        'kho-mau-van-ban/<str:ma_mau>/',
        views.template_detail,
        name='template_detail'
    ),
    path(
        'kho-mau-van-ban/<str:ma_mau>/sua/',
        views.template_update,
        name='template_update'
    ),
    path(
        'kho-mau-van-ban/<str:ma_mau>/xoa/',
        views.template_delete,
        name='template_delete'
    ),
    path(
        'kho-mau-van-ban/<str:ma_mau>/tai-xuong/',
        views.template_download,
        name='template_download'
    ),

    # ==========================
    # THÔNG BÁO VÀ CẢNH BÁO
    # ==========================
    path(
        'thong-bao/',
        views.notification_list,
        name='notification_list'
    ),

    # Đường dẫn cố định phải đặt trước đường dẫn động
    path(
        'thong-bao/danh-dau-tat-ca-da-doc/',
        views.notification_mark_all_read,
        name='notification_mark_all_read'
    ),

    path(
        'thong-bao/<str:ma_thong_bao>/da-doc/',
        views.notification_mark_read,
        name='notification_mark_read'
    ),
    path(
        'thong-bao/<str:ma_thong_bao>/',
        views.notification_detail,
        name='notification_detail'
    ),
]
