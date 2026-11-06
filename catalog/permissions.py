from rest_framework import permissions
from .models import UserProfile, get_user_role


class IsGuestUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsSupportStaffUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        role = get_user_role(request.user)
        return role in [UserProfile.ROLE_STAFF, UserProfile.ROLE_MANAGER] or request.user.is_staff or request.user.is_superuser


class IsManagerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        role = get_user_role(request.user)
        return role == UserProfile.ROLE_MANAGER or request.user.is_superuser


class TicketPermission(permissions.BasePermission):
    """
    Phân quyền thao tác trên Ticket:
    - GET (Xem): Công khai cho mọi người
    - POST (Tạo yêu cầu): Người dùng đã đăng nhập (Khách, Nhân viên hỗ trợ, Quản lý)
    - PUT / PATCH (Cập nhật tiến độ, chi phí, đóng phiếu): Chỉ Nhân viên hỗ trợ và Quản lý
    - DELETE (Xóa phiếu): Chỉ Quản lý
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not (request.user and request.user.is_authenticated):
            return False

        role = get_user_role(request.user)

        if request.method == "POST":
            # Khach, nhan vien va quan ly deu duoc gui ticket
            return True

        if request.method in ["PUT", "PATCH"]:
            # Chi nhan vien ho tro va quan ly duoc cap nhat tien do xu ly
            return role in [UserProfile.ROLE_STAFF, UserProfile.ROLE_MANAGER] or request.user.is_staff or request.user.is_superuser

        if request.method == "DELETE":
            # Chi quan ly duoc phep xoa ticket
            return role == UserProfile.ROLE_MANAGER or request.user.is_superuser

        return False


class CategoryPermission(permissions.BasePermission):
    """
    Phân quyền thao tác trên Danh mục sự cố:
    - GET (Xem): Công khai
    - POST / PUT / PATCH / DELETE: Chỉ Quản lý
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not (request.user and request.user.is_authenticated):
            return False

        role = get_user_role(request.user)
        return role == UserProfile.ROLE_MANAGER or request.user.is_superuser

