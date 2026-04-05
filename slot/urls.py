from django.urls import path

from .views import (
    admin_dashboard,
    book_appointment,
    cancel_appointment,
    dashboard,
    home,
    login_view,
    logout_view,
    manage_appointments,
    manage_schedules,
    manage_services,
    my_appointments,
    register_view,
    services_view,
)

urlpatterns = [
    path("", home, name="home"),
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard, name="dashboard"),
    path("services/", services_view, name="services"),
    path("book/", book_appointment, name="book_appointment"),
    path("appointments/", my_appointments, name="my_appointments"),
    path("appointments/cancel/<int:appointment_id>/", cancel_appointment, name="cancel_appointment"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    path("manage-services/", manage_services, name="manage_services"),
    path("manage-schedules/", manage_schedules, name="manage_schedules"),
    path("manage-appointments/", manage_appointments, name="manage_appointments"),
]
