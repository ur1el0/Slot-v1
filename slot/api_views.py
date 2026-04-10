from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, F, Q

from .api_permissions import IsStaffUser
from .models import Appointment, Schedule, Service
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentSerializer,
    AppointmentStatusSerializer,
    ScheduleSerializer,
    ServiceSerializer,
)


class UserServiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ["name", "created_at"]
    search_fields = ["name", "description"]

    def get_queryset(self):
        return Service.objects.filter(is_active=True).order_by("name")

    @action(detail=False, methods=["get"])
    def featured(self, request):
        services = self.get_queryset()[:3]
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)


class UserScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ScheduleSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["date", "start_time", "created_at"]

    def get_queryset(self):
        queryset = Schedule.objects.select_related("service").filter(is_available=True, service__is_active=True)

        service_id = self.request.query_params.get("service")
        if service_id:
            queryset = queryset.filter(service_id=service_id)

        date_value = self.request.query_params.get("date")
        if date_value:
            queryset = queryset.filter(date=date_value)

        bookable = self.request.query_params.get("bookable")
        if bookable == "true":
            queryset = queryset.annotate(
                active_appointments=Count(
                    "appointments",
                    filter=Q(appointments__status__in=["pending", "confirmed"]),
                )
            ).filter(slot_limit__gt=F("active_appointments"))

        return queryset.order_by("date", "start_time")


class UserSlotViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.select_related("service", "schedule", "user").filter(user=self.request.user).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return AppointmentCreateSerializer
        return AppointmentSerializer

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        appointments = self.get_queryset().filter(status__in=["pending", "confirmed"])[:5]
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status in {"cancelled", "completed", "rejected"}:
            return Response({"detail": "This slot cannot be cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        appointment.status = "cancelled"
        appointment.save(update_fields=["status", "updated_at"])
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data)


class AdminServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all().order_by("-created_at")
    serializer_class = ServiceSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ["name", "created_at"]
    search_fields = ["name", "description"]


class AdminScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.select_related("service").all().order_by("-date", "-start_time")
    serializer_class = ScheduleSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["date", "start_time", "created_at"]


class AdminSlotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Appointment.objects.select_related("user", "service", "schedule").all().order_by("-created_at")
    serializer_class = AppointmentSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ["created_at", "updated_at", "status"]
    search_fields = ["user__username", "service__name", "reason"]

    @action(detail=True, methods=["patch"], permission_classes=[IsStaffUser])
    def status(self, request, pk=None):
        appointment = self.get_object()
        serializer = AppointmentStatusSerializer(appointment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AppointmentSerializer(appointment).data)
