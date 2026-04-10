from rest_framework import serializers

from .models import Appointment, Schedule, Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "description", "duration", "is_active", "created_at"]


class ScheduleSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    remaining_slots = serializers.IntegerField(read_only=True)
    bookable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Schedule
        fields = [
            "id",
            "service",
            "service_name",
            "date",
            "start_time",
            "end_time",
            "slot_limit",
            "is_available",
            "remaining_slots",
            "bookable",
            "created_at",
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "user",
            "user_username",
            "service",
            "service_name",
            "schedule",
            "reason",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]


class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["id", "service", "schedule", "reason", "status", "created_at", "updated_at"]
        read_only_fields = ["status", "created_at", "updated_at"]

    def validate(self, attrs):
        service = attrs.get("service")
        schedule = attrs.get("schedule")

        if service and schedule and schedule.service_id != service.id:
            raise serializers.ValidationError({"schedule": "Selected schedule does not belong to the selected service."})

        if schedule and not schedule.bookable:
            raise serializers.ValidationError({"schedule": "Selected schedule is not available for booking."})

        return attrs

    def create(self, validated_data):
        return Appointment.objects.create(
            user=self.context["request"].user,
            status="pending",
            **validated_data,
        )


class AppointmentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["status"]

    def validate_status(self, value):
        allowed = {"pending", "confirmed", "cancelled", "completed", "rejected"}
        if value not in allowed:
            raise serializers.ValidationError("Invalid status.")
        return value
