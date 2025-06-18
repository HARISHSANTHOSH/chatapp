import uuid

from django.contrib.auth.models import User
from django.db import models
from pgvector.django import HnswIndex, VectorField

# Create your models here.


class ChatThread(models.Model):
    """
    Table for storing chat thread
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.CharField(
        max_length=10000, blank=True, null=True, default=""
    )
    response = models.TextField(blank=True, null=True, default="")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return f"chat_id:{self.id}--{self.user.username}"

    class Meta:
        db_table = "chat_thread"


class ChatHistory(models.Model):
    """
    Table for storing chat history
    """

    chat_thread = models.ForeignKey(
        ChatThread, on_delete=models.CASCADE, related_name="chat_thread"
    )
    query = models.CharField(
        max_length=10000, blank=True, null=True, default=""
    )
    standalone_question = models.CharField(
        max_length=10000, blank=True, null=True, default=""
    )
    response = models.TextField(blank=True, null=True, default="")
    is_active = models.BooleanField(default=True)
    is_bookamarked = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        self.id

    def __str__(self):
        return f"thread_id: {self.chat_thread.id} | chat_id: {self.id} | {self.chat_thread.user.username}"

    class Meta:
        db_table = "chat_history"


class Person(models.Model):
    id = models.AutoField(primary_key=True)  # Automatically generated ID
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    address = models.TextField()
    embedding = VectorField(dimensions=1536)
    created_on = models.DateTimeField(
        auto_now_add=True
    )  # Timestamp when record is created
    updated_on = models.DateTimeField(
        auto_now=True
    )  # Timestamp when record is updated

    def __str__(self):
        return f"{self.name} ({self.email})"

    class Meta:
        db_table = "user_details"


class UserSubscription(models.Model):
    user_email = models.EmailField(max_length=255)
    customer_name = models.CharField(max_length=255)
    order_reference = models.UUIDField(null=True, db_index=True)
    plan = models.CharField(
        max_length=50
    )  # Plan type (Standard, Premium, etc.)
    start_date = models.DateTimeField()  # Subscription start date
    current_period_end = (
        models.DateTimeField()
    )  # End of the current billing cycle
    status = models.CharField(
        max_length=50,
        choices=[
            ("active", "Active"),
            (
                "inactive",
                "Inactive",
            ),  # When the user downgrades or the plan becomes inactive
            ("cancelled", "Cancelled"),
        ],
        default="active",
    )  #

    created_at = models.DateTimeField(
        auto_now_add=True
    )  # When the subscription was created
    updated_at = models.DateTimeField(
        auto_now=True
    )  # When the subscription was last updated

    def __str__(self):
        return f"{self.customer_name} - {self.plan}"


class UserPayment(models.Model):
    user_subscription = models.ForeignKey(
        UserSubscription, related_name="payments", on_delete=models.PROTECT
    )
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )  # Amount in dollars
    currency = models.CharField(
        max_length=10, null=True, blank=True
    )  # Currency code (e.g., USD)
    payment_status = models.CharField(
        max_length=50,
        choices=[
            ("paid", "Paid"),
            ("unpaid", "Unpaid"),
            ("pending", "Pending"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    payment_date = models.DateTimeField(
        null=True, blank=True
    )  # Payment date (if available)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.payment_id} - {self.payment_status}"


class OneTimePayment(models.Model):
    order_reference = models.CharField(max_length=100, unique=True)
    payment_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="usd")
    payment_status = models.CharField(max_length=20)
    payment_date = models.DateTimeField(auto_now_add=True)
    user_email = models.EmailField(null=True, blank=True)
    customer_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return (
            f"Payment {self.order_reference} - {self.amount} {self.currency}"
        )

    class Meta:
        db_table = "chatapp_one_time_payment"
