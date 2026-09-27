from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, EmailStr


class LifecycleKind(str, Enum):
    checkout = "checkout"
    fulfillment = "fulfillment"
    receipt = "receipt"
    order_update = "order_update"


class OrderItem(BaseModel):
    name: str
    quantity: int


class OrderSnapshot(BaseModel):
    order_number: str
    customer_name: str
    customer_email: EmailStr
    currency: str
    total_amount: str
    tracking_url: str
    items: List[OrderItem]


class TemplateRegistrationRequest(BaseModel):
    store_name: str
    namespace: str


class TemplatePreviewRequest(BaseModel):
    kind: LifecycleKind
    template_id: str
    order: OrderSnapshot


class TemplateDefinition(BaseModel):
    kind: LifecycleKind
    name: str
    subject: str
    html: str


SUBJECTS = {
    LifecycleKind.checkout: "We received your order #{{order_number}}",
    LifecycleKind.fulfillment: "Your order #{{order_number}} has shipped",
    LifecycleKind.receipt: "Your receipt for order #{{order_number}}",
    LifecycleKind.order_update: "An update for order #{{order_number}}",
}


def build_template_definition(kind: LifecycleKind, store_name: str, namespace: str) -> TemplateDefinition:
    scoped_name = f"{namespace}-{kind.value}"

    html_map = {
        LifecycleKind.checkout: (
            f"<h1>{store_name} order received</h1>"
            "<p>Hi {{customer_name}}, we have your order <strong>#{{order_number}}</strong>.</p>"
            "<p>We will email again when it moves to fulfillment.</p>"
        ),
        LifecycleKind.fulfillment: (
            f"<h1>{store_name} shipment update</h1>"
            "<p>Your order <strong>#{{order_number}}</strong> is on the way.</p>"
            "<p>Track it here: <a href='{{tracking_url}}'>{{tracking_url}}</a></p>"
        ),
        LifecycleKind.receipt: (
            f"<h1>{store_name} receipt</h1>"
            "<p>Thanks, {{customer_name}}. Your payment for order <strong>#{{order_number}}</strong> is confirmed.</p>"
            "<p>Total: {{currency}} {{total_amount}}</p>"
        ),
        LifecycleKind.order_update: (
            f"<h1>{store_name} order update</h1>"
            "<p>There is a new update for order <strong>#{{order_number}}</strong>.</p>"
            "<p>Review details here: <a href='{{tracking_url}}'>{{tracking_url}}</a></p>"
        ),
    }

    return TemplateDefinition(
        kind=kind,
        name=scoped_name,
        subject=SUBJECTS[kind],
        html=html_map[kind],
    )


def order_template_vars(order: OrderSnapshot) -> dict:
    return {
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "customer_email": str(order.customer_email),
        "currency": order.currency,
        "total_amount": order.total_amount,
        "tracking_url": order.tracking_url,
        "items": [{"name": item.name, "quantity": item.quantity} for item in order.items],
    }
