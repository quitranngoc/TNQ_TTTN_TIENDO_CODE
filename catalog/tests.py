from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Ticket, UserProfile

User = get_user_model()


class AuthAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="demouser",
            password="Password123!",
            email="demo@ticketdesk.local",
        )
        self.profile = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={"role": UserProfile.ROLE_GUEST},
        )[0]

        self.login_url = "/api/v1/auth/login/"
        self.logout_url = "/api/v1/auth/logout/"
        self.me_url = "/api/v1/auth/me/"
        self.register_url = "/api/v1/auth/register/"

    # 1. Dang ky tai khoan khach moi
    def test_register_guest_user(self):
        data = {
            "username": "newguest",
            "password": "GuestPassword123!",
            "email": "guest@company.com",
            "role": "guest",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["role"], "guest")
        self.assertTrue(User.objects.filter(username="newguest").exists())

    # 2. Dang nhap thanh cong nhan token va vai tro
    def test_login_success(self):
        data = {
            "username": "demouser",
            "password": "Password123!",
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["username"], "demouser")
        self.assertEqual(response.data["user"]["role"], "guest")

    # 3. Dang nhap that bai khi sai mat khau
    def test_login_invalid_credentials(self):
        data = {
            "username": "demouser",
            "password": "WrongPassword!",
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    # 4. Xem thong tin ban than khi da dang nhap
    def test_get_current_user_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "demouser")
        self.assertEqual(response.data["user"]["role"], "guest")

    # 5. Dang xuat huy bo token
    def test_logout_success(self):
        # Dang nhap lay token
        login_res = self.client.post(
            self.login_url,
            {"username": "demouser", "password": "Password123!"},
            format="json",
        )
        token = login_res.data["token"]

        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])


class RolePermissionTestCase(APITestCase):

    def setUp(self):
        # 1. Khach (Guest)
        self.guest = User.objects.create_user(
            username="guest_user",
            password="Password123!",
        )
        UserProfile.objects.filter(user=self.guest).update(role=UserProfile.ROLE_GUEST)

        # 2. Nhan vien ho tro (Staff)
        self.staff = User.objects.create_user(
            username="staff_user",
            password="Password123!",
            is_staff=True,
        )
        UserProfile.objects.filter(user=self.staff).update(role=UserProfile.ROLE_STAFF)

        # 3. Quan ly (Manager)
        self.manager = User.objects.create_superuser(
            username="manager_user",
            password="Password123!",
            email="manager@ticketdesk.local",
        )
        UserProfile.objects.filter(user=self.manager).update(role=UserProfile.ROLE_MANAGER)

        self.category = Category.objects.create(
            name="Phan cung",
            description="Loi phan cung",
            is_active=True,
        )

        self.ticket = Ticket.objects.create(
            title="Hu chuot may tinh",
            department="Phong Marketing",
            category=self.category,
            priority="LOW",
            sla_hours=4,
            estimated_cost="100000.00",
            created_by=self.guest,
        )

        self.ticket_detail_url = f"/api/v1/tickets/{self.ticket.id}/"
        self.category_list_url = "/api/v1/categories/"

    # Khach: Co the gui yeu cau ho tro
    def test_guest_can_create_ticket(self):
        self.client.force_authenticate(user=self.guest)
        data = {
            "title": "Loi mang wifi phong hop",
            "department": "Phong Hop 1",
            "category": self.category.id,
        }
        response = self.client.post("/api/v1/tickets/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # Khach: KHONG duoc cap nhat tien do xu ly cua ticket
    def test_guest_cannot_update_ticket(self):
        self.client.force_authenticate(user=self.guest)
        response = self.client.patch(
            self.ticket_detail_url,
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Khach: KHONG duoc xoa ticket
    def test_guest_cannot_delete_ticket(self):
        self.client.force_authenticate(user=self.guest)
        response = self.client.delete(self.ticket_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Khach: KHONG duoc tao danh muc he thong
    def test_guest_cannot_create_category(self):
        self.client.force_authenticate(user=self.guest)
        response = self.client.post(
            self.category_list_url,
            {"name": "Danh muc moi"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Nhan vien ho tro: Co the cap nhat tien do, chi phi va dong ticket
    def test_support_staff_can_update_ticket(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(
            self.ticket_detail_url,
            {"is_active": False, "estimated_cost": "150000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.is_active)
        self.assertEqual(str(self.ticket.estimated_cost), "150000.00")

    # Nhan vien ho tro: KHONG duoc xoa ticket
    def test_support_staff_cannot_delete_ticket(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.delete(self.ticket_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Nhan vien ho tro: KHONG duoc tao danh muc
    def test_support_staff_cannot_create_category(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.post(
            self.category_list_url,
            {"name": "Danh muc moi"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Quan ly: Co toan quyen xoa ticket
    def test_manager_can_delete_ticket(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.delete(self.ticket_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ticket.objects.filter(id=self.ticket.id).exists())

    # Quan ly: Co toan quyen tao, sua, xoa danh muc
    def test_manager_can_create_category(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            self.category_list_url,
            {"name": "Danh muc do quan ly tao"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TicketAPITestCase(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Phan cung",
            description="Cac su co ve phan cung may tinh va thiet bi ngoai vi",
            is_active=True,
        )

        self.ticket = Ticket.objects.create(
            title="Loi khong khoi dong duoc may tinh ban",
            department="Phong Ke toan",
            description="May tinh phong ke toan bi sap nguon, mo khong len man hinh",
            sla_hours=4,
            priority="HIGH",
            estimated_cost="350000.00",
            is_active=True,
            category=self.category,
        )

        self.list_url = "/api/v1/tickets/"
        self.detail_url = f"/api/v1/tickets/{self.ticket.id}/"

        # Nhan vien ho tro de cap nhat va xu ly ticket
        self.user = User.objects.create_user(
            username="ithelpdesk",
            password="TestPassword123!",
            is_staff=True,
        )
        UserProfile.objects.filter(user=self.user).update(role=UserProfile.ROLE_STAFF)

        # Quan ly de xoa ticket
        self.manager = User.objects.create_superuser(
            username="itmanager",
            password="TestPassword123!",
            email="manager@ticketdesk.local",
        )
        UserProfile.objects.filter(user=self.manager).update(role=UserProfile.ROLE_MANAGER)

    def test_get_ticket_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_ticket_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["title"],
            "Loi khong khoi dong duoc may tinh ban",
        )

    def test_create_ticket_requires_login(self):
        data = {
            "title": "Ket noi may in mang bi loi",
            "department": "Phong Kinh doanh",
            "description": "May in bao offline khong nhan lenh in",
            "sla_hours": 2,
            "estimated_cost": "0.00",
            "priority": "MEDIUM",
            "is_active": True,
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_update_ticket_requires_login(self):
        response = self.client.patch(
            self.detail_url,
            {"estimated_cost": "500000.00"},
            format="json",
        )
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_delete_ticket_requires_login(self):
        response = self.client.delete(self.detail_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_authenticated_user_can_create_ticket(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "title": "Ket noi may in mang bi loi",
            "department": "Phong Kinh doanh",
            "description": "May in bao offline khong nhan lenh in",
            "sla_hours": 2,
            "estimated_cost": "0.00",
            "priority": "MEDIUM",
            "is_active": True,
            "category": self.category.id,
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Ticket.objects.filter(title="Ket noi may in mang bi loi").exists()
        )

    def test_authenticated_user_can_update_ticket(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            self.detail_url,
            {"estimated_cost": "500000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(str(self.ticket.estimated_cost), "500000.00")

    def test_authenticated_user_cannot_create_ticket_with_negative_cost(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "title": "Thay the card mang",
            "estimated_cost": "-100000",
            "department": "Phong Ky thuat",
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("estimated_cost", response.data["errors"])

    def test_authenticated_user_cannot_create_ticket_without_title(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "estimated_cost": "150000",
            "department": "Phong Ke toan",
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("title", response.data["errors"])

    def test_manager_can_delete_ticket(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Ticket.objects.filter(id=self.ticket.id).exists()
        )

    def test_filter_tickets_by_category_and_status(self):
        response = self.client.get(
            f"{self.list_url}?category={self.category.id}&is_active=true"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_search_tickets(self):
        response = self.client.get(f"{self.list_url}?search=sap+nguon")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)


class CategoryAPITestCase(APITestCase):

    def setUp(self):
        # Quan ly de quan ly Category
        self.user = User.objects.create_superuser(
            username="categorymanager",
            password="TestPassword123!",
            email="catmanager@ticketdesk.local",
        )
        UserProfile.objects.filter(user=self.user).update(role=UserProfile.ROLE_MANAGER)

        self.category = Category.objects.create(
            name="Mang & Ket noi",
            description="Cac su co ve ha tang mang, wifi va internet",
            is_active=True,
        )

        self.list_url = "/api/v1/categories/"
        self.detail_url = f"/api/v1/categories/{self.category.id}/"

        self.client.force_authenticate(user=self.user)

    def test_get_category_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_category_success(self):
        data = {
            "name": "Tai khoan & Phan quyen",
            "description": "Quan ly tai khoan va cap nhat mat khau he thong",
            "is_active": True,
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Category.objects.filter(name="Tai khoan & Phan quyen").exists()
        )

    def test_create_category_duplicate_name(self):
        data = {
            "name": "Mang & Ket noi",
            "description": "Danh muc bi trung",
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_category_missing_name(self):
        data = {
            "description": "Danh muc khong co ten",
            "is_active": True,
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_category_success(self):
        data = {
            "name": "Ha tang mang & Ket noi internet",
        }
        response = self.client.patch(
            self.detail_url,
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Ha tang mang & Ket noi internet")

    def test_delete_category_success(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Category.objects.filter(id=self.category.id).exists()
        )
