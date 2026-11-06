from decimal import Decimal
from django.db import transaction
from django.db.models import Count, Sum, Avg
from .models import Ticket


@transaction.atomic
def create_ticket(
    *,
    title,
    estimated_cost=Decimal("0.00"),
    department="",
    description="",
    sla_hours=None,
    priority="MEDIUM",
    is_active=True,
    category=None,
    created_by=None,
):
    estimated_cost = Decimal(str(estimated_cost))

    if estimated_cost < 0:
        raise ValueError("Gia khong duoc am.")

    ticket = Ticket.objects.create(
        title=title,
        estimated_cost=estimated_cost,
        department=department,
        description=description,
        sla_hours=sla_hours,
        priority=priority,
        is_active=is_active,
        category=category,
        created_by=created_by,
    )

    return ticket
def get_ticket_statistics():

    # 1. Thong ke tong quan bang aggregate()
    overview = Ticket.objects.aggregate(
        total_tickets=Count("id"),
        total_cost=Sum("estimated_cost"),
        average_cost=Avg("estimated_cost")
    )

    # 2. Thong ke ticket theo trang thai bang annotate()
    status_statistics = (
        Ticket.objects
        .values("status")
        .annotate(total=Count("id"))
        .order_by("status")
    )

    # 3. Thong ke ticket theo nguoi xu ly bang annotate()
    assignee_statistics = (
        Ticket.objects
        .values("assignee__username")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    return {
        "overview": overview,
        "by_status": list(status_statistics),
        "by_assignee": list(assignee_statistics)
    }
def get_ticket_list(processed=None, status=None):

    tickets = Ticket.objects.select_related(
        "category",
        "assignee",
        "created_by"
    ).order_by("-created_at")

    # Loc theo trang thai xu ly
    if processed is True:
        tickets = tickets.filter(
            status__in=["RESOLVED", "CLOSED"]
        )

    elif processed is False:
        tickets = tickets.exclude(
            status__in=["RESOLVED", "CLOSED"]
        )

    # Loc theo trang thai cu the
    if status:
        tickets = tickets.filter(status=status)

    return tickets