from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class MockAPIModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CustomerStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LEAD = "lead"


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class StoredRecord(MockAPIModel):
    id: str
    created_at: datetime
    updated_at: datetime


class NonEmptyPatch(MockAPIModel):
    @model_validator(mode="after")
    def require_a_change(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


# Customers


class CustomerCreate(MockAPIModel):
    name: str = Field(min_length=2, max_length=100, examples=["Jordan Lee"])
    email: EmailStr = Field(examples=["jordan.lee@example.com"])
    phone: str = Field(default="", max_length=30, examples=["+1-555-0199"])
    company: str = Field(default="", max_length=120, examples=["Northstar Labs"])
    status: CustomerStatus = CustomerStatus.ACTIVE


class CustomerReplace(MockAPIModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(max_length=30)
    company: str = Field(max_length=120)
    status: CustomerStatus


class CustomerUpdate(NonEmptyPatch):
    name: str = Field(default=None, min_length=2, max_length=100)
    email: EmailStr = None
    phone: str = Field(default=None, max_length=30)
    company: str = Field(default=None, max_length=120)
    status: CustomerStatus = None


class CustomerResponse(StoredRecord, CustomerCreate):
    pass


# Products


class ProductCreate(MockAPIModel):
    sku: str = Field(min_length=2, max_length=40, pattern=r"^[A-Za-z0-9_-]+$", examples=["KB-100"])
    name: str = Field(min_length=2, max_length=120, examples=["Wireless Keyboard"])
    description: str = Field(default="", max_length=2000)
    category: str = Field(default="General", min_length=2, max_length=80)
    price_cents: int = Field(ge=0, le=100_000_000, examples=[7999])
    stock_quantity: int = Field(default=0, ge=0, le=10_000_000)
    active: bool = True


class ProductReplace(MockAPIModel):
    sku: str = Field(min_length=2, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(max_length=2000)
    category: str = Field(min_length=2, max_length=80)
    price_cents: int = Field(ge=0, le=100_000_000)
    stock_quantity: int = Field(ge=0, le=10_000_000)
    active: bool


class ProductUpdate(NonEmptyPatch):
    sku: str = Field(default=None, min_length=2, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(default=None, min_length=2, max_length=120)
    description: str = Field(default=None, max_length=2000)
    category: str = Field(default=None, min_length=2, max_length=80)
    price_cents: int = Field(default=None, ge=0, le=100_000_000)
    stock_quantity: int = Field(default=None, ge=0, le=10_000_000)
    active: bool = None


class ProductResponse(StoredRecord, ProductCreate):
    pass


# Orders


class OrderItem(MockAPIModel):
    product_id: str = Field(min_length=1)
    quantity: int = Field(ge=1, le=1000)


class OrderCreate(MockAPIModel):
    customer_id: str = Field(min_length=1)
    items: list[OrderItem] = Field(min_length=1, max_length=100)
    status: OrderStatus = OrderStatus.PENDING
    shipping_address: str = Field(min_length=5, max_length=500)
    notes: str = Field(default="", max_length=1000)


class OrderReplace(MockAPIModel):
    customer_id: str = Field(min_length=1)
    items: list[OrderItem] = Field(min_length=1, max_length=100)
    status: OrderStatus
    shipping_address: str = Field(min_length=5, max_length=500)
    notes: str = Field(max_length=1000)


class OrderUpdate(NonEmptyPatch):
    customer_id: str = Field(default=None, min_length=1)
    items: list[OrderItem] = Field(default=None, min_length=1, max_length=100)
    status: OrderStatus = None
    shipping_address: str = Field(default=None, min_length=5, max_length=500)
    notes: str = Field(default=None, max_length=1000)


class OrderResponse(StoredRecord, OrderCreate):
    total_cents: int = Field(ge=0)


# Support tickets


class TicketCreate(MockAPIModel):
    customer_id: str = Field(min_length=1)
    subject: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=3, max_length=4000)
    status: TicketStatus = TicketStatus.OPEN
    priority: Priority = Priority.MEDIUM
    assignee: str = Field(default="", max_length=100)


class TicketReplace(MockAPIModel):
    customer_id: str = Field(min_length=1)
    subject: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=3, max_length=4000)
    status: TicketStatus
    priority: Priority
    assignee: str = Field(max_length=100)


class TicketUpdate(NonEmptyPatch):
    customer_id: str = Field(default=None, min_length=1)
    subject: str = Field(default=None, min_length=3, max_length=160)
    description: str = Field(default=None, min_length=3, max_length=4000)
    status: TicketStatus = None
    priority: Priority = None
    assignee: str = Field(default=None, max_length=100)


class TicketResponse(StoredRecord, TicketCreate):
    pass


# Product reviews


class ReviewCreate(MockAPIModel):
    customer_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5)
    title: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=2, max_length=2000)


class ReviewReplace(MockAPIModel):
    customer_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5)
    title: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=2, max_length=2000)


class ReviewUpdate(NonEmptyPatch):
    customer_id: str = Field(default=None, min_length=1)
    product_id: str = Field(default=None, min_length=1)
    rating: int = Field(default=None, ge=1, le=5)
    title: str = Field(default=None, min_length=2, max_length=120)
    body: str = Field(default=None, min_length=2, max_length=2000)


class ReviewResponse(StoredRecord, ReviewCreate):
    pass


class MockPage[RecordT: StoredRecord](MockAPIModel):
    items: list[RecordT]
    total: int
    limit: int
    offset: int


class MockResetResponse(MockAPIModel):
    message: str
    counts: dict[str, int]
    reset_at: datetime
