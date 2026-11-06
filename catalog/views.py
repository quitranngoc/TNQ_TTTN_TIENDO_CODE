from decimal import Decimal
from django.contrib.auth import login, logout
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, views, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth import get_user_model
from .models import Category, Ticket, UserProfile
from django.contrib.auth import get_user_model
from .serializers import AssigneeSerializer
from .models import Category, Ticket
from .permissions import CategoryPermission, TicketPermission

from .serializers import (
    CategorySerializer,
    LoginSerializer,
    RegisterSerializer,
    TicketSerializer,
    TicketListSerializer,
    UserSerializer,
)
from .services import (
    create_ticket,
    get_ticket_statistics,
    get_ticket_list,
)
User = get_user_model()

class LoginView(views.APIView):
    """
    API Đăng nhập: Trả về Token xác thực và thông tin vai trò người dùng
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Dang nhap session va tao token
        login(request, user)
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "success": True,
                "message": "Đăng nhập thành công.",
                "token": token.key,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(views.APIView):
    """
    API Đăng xuất: Thu hồi Token và xóa session
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Thu hoi token
        Token.objects.filter(user=request.user).delete()
        # Xoa session
        logout(request)

        return Response(
            {
                "success": True,
                "message": "Đăng xuất thành công.",
            },
            status=status.HTTP_200_OK,
        )


class MeView(views.APIView):
    """
    API Xem thông tin tài khoản và vai trò của người dùng hiện tại
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "success": True,
                "user": UserSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(views.APIView):
    """
    API Đăng ký tài khoản mới (mặc định vai trò Khách)
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "success": True,
                "message": "Đăng ký tài khoản thành công.",
                "token": token.key,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [TicketPermission]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = ["title", "department", "description"]

    ordering_fields = [
        "title",
        "estimated_cost",
        "sla_hours",
        "priority",
        "created_at",
    ]

    ordering = ["id"]

    filterset_fields = [
        "category",
        "is_active",
        "priority",
    ]

    def perform_create(self, serializer):
        data = serializer.validated_data

        try:
            created_by = self.request.user if self.request.user.is_authenticated else None
            ticket = create_ticket(
                title=data["title"],
                department=data.get("department", ""),
                description=data.get("description", ""),
                sla_hours=data.get("sla_hours"),
                priority=data.get("priority", "MEDIUM"),
                estimated_cost=data.get("estimated_cost", 0),
                category=data.get("category"),
                is_active=data.get("is_active", True),
                created_by=created_by,
            )

            serializer.instance = ticket

        except ValueError as e:
            raise ValidationError({"estimated_cost": str(e)})


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [CategoryPermission]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = ["name", "description"]
    ordering_fields = ["name", "id"]
    ordering = ["id"]
class DashboardStatisticsView(views.APIView):
    """
    API thong ke Ticket
    """
    permission_classes = [TicketPermission]

    def get(self, request):
        data = get_ticket_statistics()

        return Response(
            {
                "success": True,
                "statistics": data,
            },
            status=status.HTTP_200_OK,
        )


class DashboardTicketListView(views.APIView):
    """
    API danh sach Ticket da xu ly va chua xu ly
    """
    permission_classes = [TicketPermission]

    def get(self, request):
        processed_param = request.query_params.get("processed")
        ticket_status = request.query_params.get("status")

        # Chuyen processed tu chuoi sang Boolean
        processed = None

        if processed_param is not None:
            if processed_param.lower() == "true":
                processed = True
            elif processed_param.lower() == "false":
                processed = False
            else:
                return Response(
                    {
                        "success": False,
                        "message": "processed chi nhan true hoac false."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        tickets = get_ticket_list(
            processed=processed,
            status=ticket_status,
        )

        serializer = TicketListSerializer(tickets, many=True)

        return Response(
            {
                "success": True,
                "count": tickets.count(),
                "tickets": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
    
def dashboard_page(request):
    return render(request, "catalog/dashboard.html")

class AssigneeListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        users = User.objects.filter(
            profile__role__in=[
                UserProfile.ROLE_STAFF,
                UserProfile.ROLE_MANAGER,
            ],
            is_active=True,
        ).select_related("profile").order_by("username")

        serializer = AssigneeSerializer(users, many=True)

        return Response(
            {
                "success": True,
                "count": users.count(),
                "employees": serializer.data,
            },
            status=status.HTTP_200_OK,
        )