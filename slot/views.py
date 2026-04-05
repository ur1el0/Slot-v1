from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AppointmentForm, LoginForm, RegisterForm, ScheduleForm, ServiceForm
from .models import Appointment, Schedule, Service


def health_check(request):
    return render(request, "slot/home.html", {"services": Service.objects.filter(is_active=True).order_by("name")[:6]})


def home(request):
    services = Service.objects.filter(is_active=True).order_by("name")
    return render(request, "slot/home.html", {"services": services})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "slot/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Logged in successfully.")
            return redirect("dashboard")
    else:
        form = LoginForm(request)
    return render(request, "slot/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect("admin_dashboard")
    return render(request, "slot/user_dashboard.html")


def services_view(request):
    services = Service.objects.filter(is_active=True).prefetch_related("schedules")
    return render(request, "slot/services.html", {"services": services})


@login_required
def book_appointment(request):
    schedule_id = request.GET.get("schedule") or request.POST.get("schedule")
    initial = {}
    if schedule_id and request.method == "GET":
        schedule = get_object_or_404(Schedule, pk=schedule_id)
        initial = {"service": schedule.service_id, "schedule": schedule.id}

    if request.method == "POST":
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user
            appointment.status = "pending"
            appointment.save()
            messages.success(request, "Appointment booked and marked as pending.")
            return redirect("my_appointments")
    else:
        form = AppointmentForm(initial=initial, user=request.user)

    return render(request, "slot/book_appointment.html", {"form": form})


@login_required
def my_appointments(request):
    appointments = request.user.appointments.select_related("service", "schedule").order_by("-created_at")
    return render(request, "slot/my_appointments.html", {"appointments": appointments})


@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id, user=request.user)
    if appointment.status in {"cancelled", "completed", "rejected"}:
        messages.warning(request, "This appointment cannot be cancelled.")
    else:
        appointment.status = "cancelled"
        appointment.save(update_fields=["status", "updated_at"])
        messages.success(request, "Appointment cancelled.")
    return redirect("my_appointments")


def staff_required(view_func):
    return user_passes_test(lambda user: user.is_staff)(view_func)


@staff_required
def admin_dashboard(request):
    context = {
        "service_count": Service.objects.count(),
        "schedule_count": Schedule.objects.count(),
        "appointment_count": Appointment.objects.count(),
        "pending_count": Appointment.objects.filter(status="pending").count(),
        "confirmed_count": Appointment.objects.filter(status="confirmed").count(),
    }
    return render(request, "slot/admin_dashboard.html", context)


@staff_required
def manage_services(request):
    service_id = request.GET.get("service_id")
    service_instance = Service.objects.filter(pk=service_id).first() if service_id else None

    if request.method == "POST":
        if request.POST.get("delete_service_id"):
            Service.objects.filter(pk=request.POST["delete_service_id"]).delete()
            messages.success(request, "Service deleted.")
            return redirect("manage_services")

        form = ServiceForm(request.POST, instance=service_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Service saved.")
            return redirect("manage_services")
    else:
        form = ServiceForm(instance=service_instance)

    services = Service.objects.order_by("-created_at")
    return render(request, "slot/manage_services.html", {"form": form, "services": services, "editing_service": service_instance})


@staff_required
def manage_schedules(request):
    schedule_id = request.GET.get("schedule_id")
    schedule_instance = Schedule.objects.filter(pk=schedule_id).first() if schedule_id else None

    if request.method == "POST":
        if request.POST.get("delete_schedule_id"):
            Schedule.objects.filter(pk=request.POST["delete_schedule_id"]).delete()
            messages.success(request, "Schedule deleted.")
            return redirect("manage_schedules")

        form = ScheduleForm(request.POST, instance=schedule_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Schedule saved.")
            return redirect("manage_schedules")
    else:
        form = ScheduleForm(instance=schedule_instance)

    schedules = Schedule.objects.select_related("service").order_by("-date", "-start_time")
    return render(request, "slot/manage_schedules.html", {"form": form, "schedules": schedules, "editing_schedule": schedule_instance})


@staff_required
def manage_appointments(request):
    if request.method == "POST":
        appointment = get_object_or_404(Appointment, pk=request.POST.get("appointment_id"))
        new_status = request.POST.get("new_status")
        if new_status in dict(Appointment.STATUS_CHOICES):
            appointment.status = new_status
            appointment.save(update_fields=["status", "updated_at"])
            messages.success(request, "Appointment updated.")
            return redirect("manage_appointments")

    appointments = Appointment.objects.select_related("user", "service", "schedule").order_by("-created_at")
    return render(request, "slot/manage_appointments.html", {"appointments": appointments})
