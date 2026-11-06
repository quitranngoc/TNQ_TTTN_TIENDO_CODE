
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


# =====================================================
# 1. USER PROFILE - HO SO VA PHAN QUYEN NGUOI DUNG
# =====================================================

class UserProfile(models.Model):
    ROLE_GUEST = "guest"
    ROLE_STAFF = "staff"
    ROLE_MANAGER = "manager"

    ROLE_CHOICES = [
        (ROLE_GUEST, "Khach"),
        (ROLE_STAFF, "Nhan vien ho tro"),
        (ROLE_MANAGER, "Quan ly"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Tai khoan nguoi dung",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_GUEST,
        verbose_name="Vai tro nguoi dung",
    )

    class Meta:
        verbose_name = "Ho so nguoi dung"
        verbose_name_plural = "Ho so nguoi dung"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


# =====================================================
# 2. HAM XAC DINH VAI TRO NGUOI DUNG
# =====================================================

def get_user_role(user):
    if not user or not user.is_authenticated:
        return UserProfile.ROLE_GUEST

    if user.is_superuser:
        return UserProfile.ROLE_MANAGER

    if hasattr(user, "profile"):
        return user.profile.role

    if user.is_staff:
        return UserProfile.ROLE_STAFF

    return UserProfile.ROLE_GUEST


# =====================================================
# 3. SIGNAL TU DONG TAO USER PROFILE
# =====================================================

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_superuser:
            role = UserProfile.ROLE_MANAGER
        elif instance.is_staff:
            role = UserProfile.ROLE_STAFF
        else:
            role = UserProfile.ROLE_GUEST

        UserProfile.objects.get_or_create(
            user=instance,
            defaults={"role": role},
        )

    else:
        if not hasattr(instance, "profile"):
            if instance.is_superuser:
                role = UserProfile.ROLE_MANAGER
            elif instance.is_staff:
                role = UserProfile.ROLE_STAFF
            else:
                role = UserProfile.ROLE_GUEST

            UserProfile.objects.get_or_create(
                user=instance,
                defaults={"role": role},
            )


# =====================================================
# 4. CATEGORY - DANH MUC SU CO
# =====================================================

class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Ten phan loai",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Mo ta phan loai",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Dang hoat dong",
    )

    class Meta:
        verbose_name = "Danh muc su co"
        verbose_name_plural = "Danh muc su co"
        ordering = ["id"]

    def __str__(self):
        return self.name


# =====================================================
# 5. TICKET - PHIEU YEU CAU HO TRO
# =====================================================

class Ticket(models.Model):

    # Cac trang thai Ticket
    STATUS_OPEN = "OPEN"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_PENDING = "PENDING"
    STATUS_RESOLVED = "RESOLVED"
    STATUS_CLOSED = "CLOSED"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Moi tiep nhan"),
        (STATUS_IN_PROGRESS, "Dang xu ly"),
        (STATUS_PENDING, "Cho phan hoi"),
        (STATUS_RESOLVED, "Da giai quyet"),
        (STATUS_CLOSED, "Da dong"),
    ]

    # Muc do uu tien
    PRIORITY_CHOICES = [
        ("LOW", "Thap"),
        ("MEDIUM", "Trung binh"),
        ("HIGH", "Cao"),
        ("URGENT", "Khan cap"),
    ]

    # Danh muc su co
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="tickets",
        null=True,
        blank=True,
        verbose_name="Danh muc su co",
    )

    # Thong tin yeu cau
    title = models.CharField(
        max_length=200,
        verbose_name="Tieu de yeu cau / su co",
    )

    department = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Phong ban / Don vi yeu cau",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Mo ta chi tiet su co",
    )

    # Thoi gian xu ly SLA
    sla_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Thoi gian xu ly SLA (gio)",
    )

    # Chi phi du kien
    estimated_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Chi phi sua chua du kien (VND)",
    )

    # Muc do uu tien
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="MEDIUM",
        verbose_name="Muc do uu tien",
    )

    # Trang thai Ticket
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
        db_index=True,
        verbose_name="Trang thai yeu cau",
    )

    # Nhan vien duoc phan cong xu ly
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        verbose_name="Nhan vien xu ly",
    )

    # Trang thai hoat dong cu - giu lai de tuong thich
    is_active = models.BooleanField(
        default=True,
        verbose_name="Dang hoat dong",
    )

    # Nguoi gui yeu cau
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tickets",
        verbose_name="Nguoi gui yeu cau",
    )

    # Thoi gian
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Thoi gian tiep nhan",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Thoi gian cap nhat",
    )

    class Meta:
        verbose_name = "Phieu yeu cau su co"
        verbose_name_plural = "Phieu yeu cau su co"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["assignee"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title}"
