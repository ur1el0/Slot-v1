from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AdminAppointmentForm, AppointmentForm, LoginForm, RegisterForm, ScheduleForm, ServiceForm
from .models import Appointment, Schedule, Service


def paginate_queryset(request, queryset, per_page):
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))
    return page_obj

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
    appointments_qs = request.user.appointments.select_related("service", "schedule").order_by(
        "schedule__date", "schedule__start_time", "-created_at"
    )
    active_services_qs = Service.objects.filter(is_active=True).order_by("name")
    upcoming_appointments = appointments_qs.filter(status__in=["pending", "confirmed"])
    context = {
        "total_count": appointments_qs.count(),
        "pending_count": appointments_qs.filter(status="pending").count(),
        "confirmed_count": appointments_qs.filter(status="confirmed").count(),
        "active_service_count": active_services_qs.count(),
        "featured_services": active_services_qs.prefetch_related("schedules")[:3],
        "upcoming_appointments": upcoming_appointments[:5],
        "next_appointment": upcoming_appointments.first(),
    }
    return render(request, "slot/user_dashboard.html", context)


def services_view(request):
    services_qs = Service.objects.filter(is_active=True).prefetch_related("schedules").order_by("name")
    page_obj = paginate_queryset(request, services_qs, 6)
    return render(request, "slot/services.html", {"services": page_obj.object_list, "page_obj": page_obj})


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
    appointments_qs = request.user.appointments.select_related("service", "schedule").order_by("-created_at")
    page_obj = paginate_queryset(request, appointments_qs, 10)
    return render(request, "slot/my_appointments.html", {"appointments": page_obj.object_list, "page_obj": page_obj})


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
    recent_appointments = Appointment.objects.select_related("user", "service", "schedule").order_by("-created_at")
    available_schedules = Schedule.objects.select_related("service").filter(is_available=True).order_by(
        "date", "start_time"
    )
    context = {
        "service_count": Service.objects.count(),
        "active_service_count": Service.objects.filter(is_active=True).count(),
        "inactive_service_count": Service.objects.filter(is_active=False).count(),
        "schedule_count": Schedule.objects.count(),
        "available_schedule_count": available_schedules.count(),
        "appointment_count": Appointment.objects.count(),
        "pending_count": Appointment.objects.filter(status="pending").count(),
        "confirmed_count": Appointment.objects.filter(status="confirmed").count(),
        "completed_count": Appointment.objects.filter(status="completed").count(),
        "recent_appointments": recent_appointments[:5],
        "upcoming_schedules": available_schedules[:5],
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

    services_qs = Service.objects.order_by("-created_at")
    page_obj = paginate_queryset(request, services_qs, 15)
    return render(
        request,
        "slot/manage_services.html",
        {"form": form, "services": page_obj.object_list, "page_obj": page_obj, "editing_service": service_instance},
    )


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

    schedules_qs = Schedule.objects.select_related("service").order_by("-date", "-start_time")
    page_obj = paginate_queryset(request, schedules_qs, 15)
    return render(
        request,
        "slot/manage_schedules.html",
        {"form": form, "schedules": page_obj.object_list, "page_obj": page_obj, "editing_schedule": schedule_instance},
    )


@staff_required
def manage_appointments(request):
    if request.method == "POST":
        if request.POST.get("appointment_id"):
            # Status update
            appointment = get_object_or_404(Appointment, pk=request.POST["appointment_id"])
            new_status = request.POST.get("new_status")
            if new_status in dict(Appointment.STATUS_CHOICES):
                appointment.status = new_status
                appointment.save(update_fields=["status", "updated_at"])
                messages.success(request, "Appointment updated.")
            return redirect("manage_appointments")
        else:
            # New appointment creation
            create_form = AdminAppointmentForm(request.POST)
            if create_form.is_valid():
                appt = create_form.save(commit=False)
                appt.status = "confirmed"
                appt.save()
                messages.success(request, "Appointment created.")
                return redirect("manage_appointments")
    else:
        create_form = AdminAppointmentForm()

    appointments_qs = Appointment.objects.select_related("user", "service", "schedule").order_by("-created_at")
    page_obj = paginate_queryset(request, appointments_qs, 15)
    return render(request, "slot/manage_appointments.html", {
        "appointments": page_obj.object_list,
        "page_obj": page_obj,
        "create_form": create_form,
    })

