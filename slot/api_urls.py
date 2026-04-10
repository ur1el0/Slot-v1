from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import (
    AdminScheduleViewSet,
    AdminServiceViewSet,
    AdminSlotViewSet,
    UserScheduleViewSet,
    UserServiceViewSet,
    UserSlotViewSet,
)

user_router = DefaultRouter()
user_router.register(r"services", UserServiceViewSet, basename="api-user-services")
user_router.register(r"schedules", UserScheduleViewSet, basename="api-user-schedules")
user_router.register(r"slots", UserSlotViewSet, basename="api-user-slots")

admin_router = DefaultRouter()
admin_router.register(r"services", AdminServiceViewSet, basename="api-admin-services")
admin_router.register(r"schedules", AdminScheduleViewSet, basename="api-admin-schedules")
admin_router.register(r"slots", AdminSlotViewSet, basename="api-admin-slots")

urlpatterns = [
    path("user/", include(user_router.urls)),
    path("admin/", include(admin_router.urls)),
]
