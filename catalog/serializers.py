from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile
from .models import Category, Ticket, UserProfile, get_user_role

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "role_display",
            "is_staff",
            "is_superuser",
        ]

    def get_role(self, obj):
        return get_user_role(obj)

    def get_role_display(self, obj):
        role = get_user_role(obj)
        role_map = dict(UserProfile.ROLE_CHOICES)
        return role_map.get(role, "Khách")


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Tên đăng nhập hoặc mật khẩu không chính xác.")

        if not user.is_active:
            raise serializers.ValidationError("Tài khoản người dùng đã bị vô hiệu hóa.")

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        default=UserProfile.ROLE_GUEST,
        required=False,
    )

    class Meta:
        model = User
        fields = ["id", "username", "password", "email", "role"]

    def create(self, validated_data):
        role = validated_data.pop("role", UserProfile.ROLE_GUEST)
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)

        if role == UserProfile.ROLE_STAFF:
            user.is_staff = True
            user.save(update_fields=["is_staff"])
        elif role == UserProfile.ROLE_MANAGER:
            user.is_staff = True
            user.save(update_fields=["is_staff"])

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.save()
        return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
            "is_active",
        ]
        read_only_fields = ["id"]


class TicketSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source="created_by.username")

    class Meta:
        model = Ticket
        fields = [
            "id",
            "category",
            "title",
            "department",
            "description",
            "priority",
            "sla_hours",
            "estimated_cost",
            "is_active",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def validate_estimated_cost(self, value):
        if value < 0:
            raise serializers.ValidationError("Gia khong duoc am.")
        return value
class TicketListSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source="category.name")
    assignee_name = serializers.ReadOnlyField(source="assignee.username")
    created_by_name = serializers.ReadOnlyField(source="created_by.username")

    class Meta:
        model = Ticket
        fields = [
            "id",
            "title",
            "category",
            "category_name",
            "department",
            "description",
            "priority",
            "status",
            "assignee",
            "assignee_name",
            "created_by",
            "created_by_name",
            "estimated_cost",
            "created_at",
            "updated_at",
        ]
class AssigneeSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="profile.role", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "role",
        ]