from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Appointment, Schedule, Service

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

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
    class Meta:
        model = Appointment
        fields = ("service", "schedule", "reason")