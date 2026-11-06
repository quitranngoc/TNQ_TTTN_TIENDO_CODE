from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Category, Ticket, UserProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "Vai trò & Phân quyền"
    verbose_name_plural = "Vai trò & Phân quyền"


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "email",
        "get_role",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    def get_role(self, obj):
        if hasattr(obj, "profile"):
            return obj.profile.get_role_display()
        return "Quản lý" if obj.is_superuser else ("Nhân viên hỗ trợ" if obj.is_staff else "Khách")

    get_role.short_description = "Vai trò hệ thống"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    ordering = ("id",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "department",
        "priority",
        "sla_hours",
        "estimated_cost",
        "is_active",
        "created_by",
        "created_at",
    )
    list_filter = ("is_active", "priority", "category", "created_at")
    search_fields = ("title", "department", "description")
    ordering = ("-created_at",)
