from django.contrib import admin

from .models import Appointment, Schedule, Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
	list_display = ("name", "duration", "is_active", "created_at")
	list_filter = ("is_active",)
	search_fields = ("name",)

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
	list_display = ("service", "date", "start_time", "end_time", "slot_limit", "is_available")
	list_filter = ("is_available", "date", "service")
	search_fields = ("service__name",)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
	list_display = ("user", "service", "schedule", "status", "created_at")
	list_filter = ("status", "service", "schedule__date")
	search_fields = ("user__username", "service__name", "reason")