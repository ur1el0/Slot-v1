from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Appointment, Schedule, Service

ROLE_CHOICES = [("user", "User"), ("admin", "Admin")]


def validate_service_schedule_pair(form, service, schedule):
    if service and schedule and schedule.service_id != service.id:
        form.add_error("schedule", "Selected schedule does not belong to the selected service.")
    if schedule and not schedule.bookable:
        form.add_error("schedule", "Selected schedule is no longer available.")

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial="user", widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("role") == "admin":
            user.is_staff = True
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    pass

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ("name", "description", "duration", "is_active")

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ("service", "date", "start_time", "end_time", "slot_limit", "is_available")

class AppointmentForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["service"].queryset = Service.objects.filter(is_active=True).order_by("name")

        schedules = Schedule.objects.filter(is_available=True).select_related("service")
        service_id = self.data.get("service") or self.initial.get("service")
        if service_id:
            schedules = schedules.filter(service_id=service_id)
        self.fields["schedule"].queryset = schedules.order_by("date", "start_time")

    class Meta:
        model = Appointment
        fields = ("service", "schedule", "reason")

    def clean(self):
        cleaned_data = super().clean()
        validate_service_schedule_pair(self, cleaned_data.get("service"), cleaned_data.get("schedule"))
        return cleaned_data

class AdminAppointmentForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True).order_by("username"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(is_active=True).order_by("name")
        schedules = Schedule.objects.filter(is_available=True).select_related("service")
        service_id = self.data.get("service") or self.initial.get("service")
        if service_id:
            schedules = schedules.filter(service_id=service_id)
        self.fields["schedule"].queryset = schedules.order_by("date", "start_time")

    class Meta:
        model = Appointment
        fields = ("user", "service", "schedule", "reason")

    def clean(self):
        cleaned_data = super().clean()
        validate_service_schedule_pair(self, cleaned_data.get("service"), cleaned_data.get("schedule"))
        return cleaned_data
