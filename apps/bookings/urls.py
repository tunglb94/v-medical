from django.urls import path
from . import views

app_name = "bookings"

urlpatterns = [

    # =========================
    # DASHBOARD LỄ TÂN
    # =========================
    path(
        "reception/",
        views.reception_dashboard,
        name="reception_home"
    ),

    # =========================
    # TIẾP NHẬN & LÊN LỊCH
    # =========================

    # Khách vãng lai (FIX lỗi 500)
    path(
        "reception/walkin/add/",
        views.add_walkin_appointment,
        name="add_walkin_appointment"
    ),

    # Lên lịch nhanh từ tra cứu
    path(
        "reception/appointment/create/",
        views.create_appointment_reception,
        name="create_appointment_reception"
    ),

    # =========================
    # API – CALENDAR
    # =========================
    path(
        "api/appointments/",
        views.get_appointments_api,
        name="get_appointments_api"
    ),

    # =========================
    # XỬ LÝ TRẠNG THÁI LỊCH HẸN
    # =========================

    # Check-in khách
    path(
        "appointment/<int:appointment_id>/checkin/",
        views.checkin_appointment,
        name="checkin"
    ),

    # Chốt đơn / kết thúc lịch hẹn
    path(
        "appointment/finish/",
        views.finish_appointment,
        name="finish_appointment"
    ),

    # Hủy / cập nhật trạng thái (POST ẩn)
    path(
        "appointment/update-status/",
        views.update_appointment_status,
        name="update_appointment_status"
    ),
]
