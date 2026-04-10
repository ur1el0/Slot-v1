from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    duration = models.DurationField(default=timedelta(minutes=30))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Schedule(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="schedules")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_limit = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def remaining_slots(self):
        active_count = self.appointments.filter(status__in=["pending", "confirmed"]).count()
        return max(self.slot_limit - active_count, 0)

    @property
    def bookable(self):
        return self.is_available and self.remaining_slots > 0

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be later than start time.")

    def __str__(self):
        return f"{self.service.name} on {self.date} ({self.start_time}-{self.end_time})"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
        ("rejected", "Rejected")
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="appointments")
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name="appointments")
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "schedule"],
                condition=Q(status__in=["pending", "confirmed"]),
                name="unique_active_user_schedule_appointment",
            )
        ]

    def clean(self):
        if self.schedule_id and self.service_id and self.schedule.service_id != self.service_id:
            raise ValidationError("Selected schedule does not belong to the selected service.")
        if self.schedule_id and not self.schedule.bookable and self.status in {"pending", "confirmed"}:
            raise ValidationError("Selected schedule is not available for booking.")

    def __str__(self):
        return f"{self.user} - {self.service.name} ({self.schedule.date})"