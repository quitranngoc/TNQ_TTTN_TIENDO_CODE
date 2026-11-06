from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    TicketViewSet,
    DashboardStatisticsView,
    DashboardTicketListView,
    dashboard_page,
    AssigneeListView,
)

router = DefaultRouter()
router.register("tickets", TicketViewSet, basename="ticket")
router.register("categories", CategoryViewSet, basename="category")

urlpatterns = [
    # API Xac thuc & Phan quyen (Auth)
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    # API Dashboard
    path(
        "dashboard/statistics/",
        DashboardStatisticsView.as_view(),
        name="dashboard-statistics",
    ),
    path(
        "dashboard/tickets/",
        DashboardTicketListView.as_view(),
        name="dashboard-tickets",
    ),
    path("dashboard/", dashboard_page, 
         name="dashboard-page"),
    path("dashboard/statistics/", 
         DashboardStatisticsView.as_view(), 
         name="dashboard-statistics"),
    path("dashboard/tickets/", 
         DashboardTicketListView.as_view(), 
         name="dashboard-tickets"),
    path(
         "employees/",
         AssigneeListView.as_view(),
         name="employee-list",
),
    # API Nghiep vu TicketDesk
    path("", include(router.urls)),

]
