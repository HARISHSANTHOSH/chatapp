from dataclasses import dataclass
from datetime import datetime
from chatapp import models
from django.db import transaction
from dateutil.relativedelta import relativedelta
from rest_framework import permissions, response, status
from django.utils import timezone
from django.utils.timezone import make_aware
import stripe
from typing import Optional

@dataclass
class CustomerInfo:
    email: str
    name: str

@dataclass
class PaymentInfo:
    amount: float
    currency: str
    status: str
    payment_intent_id: str
    payment_date: datetime

@dataclass
class SubscriptionInfo:
    plan_id: str
    order_reference: str
    start_date: datetime
    current_period_end: datetime

class StripeSessionProcessor:
    def __init__(self, event):
        self.session = event["data"]["object"]
        self.now = timezone.now()

    def extract_customer_info(self) -> CustomerInfo:
        """Extract customer details from the session."""
        customer_details = self.session.get("customer_details", {})
        return CustomerInfo(
            email=customer_details.get("email", ""),
            name=customer_details.get("name", "")
        )

    def extract_payment_info(self) -> PaymentInfo:
        """Extract payment related information."""
        # Get subscription and invoice details
        subscription_id = self.session.get("subscription")
        subscription = stripe.Subscription.retrieve(subscription_id)
        latest_invoice_id = subscription.latest_invoice
        invoice = stripe.Invoice.retrieve(latest_invoice_id)
        payment_intent_id = invoice.payment_intent

        # Get payment details
        timestamp = self.session.get("created")
        payment_date = make_aware(datetime.fromtimestamp(timestamp)) if timestamp else self.now

        return PaymentInfo(
            amount=self.session.get("amount_total", 0) / 100,  # Convert cents to dollars
            currency=self.session.get("currency", "usd"),
            status=self.session["payment_status"],
            payment_intent_id=payment_intent_id,
            payment_date=payment_date
        )

    def extract_subscription_info(self) -> SubscriptionInfo:
        """Extract subscription related information."""
        return SubscriptionInfo(
            plan_id=self.session["metadata"].get("plan_id", "unknown"),
            order_reference=self.session.get("client_reference_id"),
            start_date=self.now - relativedelta(months=1),
            current_period_end=self.now + relativedelta(months=1)
        )

class StripeWebhookHandler:
    @staticmethod
    def verify_webhook(payload, sig_header, cli_secret, webhook_secret):
        """Verify the webhook using CLI and webhook secrets."""
        try:
            event = None
            try:
                event = stripe.Webhook.construct_event(payload, sig_header, cli_secret)
            except stripe.error.SignatureVerificationError:
                try:
                    event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
                except stripe.error.SignatureVerificationError as e:
                    return response.Response({'error': 'Invalid signature'}, status=400)
            return event
        except Exception as e:
            return response.Response({'error': str(e)}, status=500)
    @staticmethod
    def handle_checkout_session(event):
        """Handle the 'checkout.session.completed' event."""
        try:
            # Process the session data
            processor = StripeSessionProcessor(event)
            customer_info = processor.extract_customer_info()
            payment_info = processor.extract_payment_info()
            subscription_info = processor.extract_subscription_info()

            # Check for existing order
            if models.UserSubscription.objects.filter(
                order_reference=subscription_info.order_reference
            ).exists():
                return response.Response(
                    {"status": "Order already processed"},
                    status=status.HTTP_200_OK,
                )

            with transaction.atomic():
                # Handle subscription
                subscription = SubscriptionManager.handle_subscription(
                    customer_info, subscription_info
                )

                # Create payment record
                PaymentManager.create_payment(
                    subscription, payment_info
                )

            return response.Response(
                {"status": "Subscription created/updated successfully"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return response.Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SubscriptionManager:
    @staticmethod
    def handle_subscription(customer_info: CustomerInfo, 
                          subscription_info: SubscriptionInfo) -> models.UserSubscription:
        """Handle subscription creation or upgrade."""
        # Check for existing subscription
        existing_subscription = models.UserSubscription.objects.filter(
            user_email=customer_info.email
        ).first()

        if existing_subscription:
            return SubscriptionManager._handle_upgrade(
                existing_subscription, customer_info, subscription_info
            )
        
        return SubscriptionManager._create_new_subscription(
            customer_info, subscription_info
        )

    @staticmethod
    def _handle_upgrade(existing_subscription: models.UserSubscription,
                       customer_info: CustomerInfo,
                       subscription_info: SubscriptionInfo) -> models.UserSubscription:
        """Handle subscription upgrade scenario."""
        if existing_subscription.plan != subscription_info.plan_id:
            existing_subscription.status = "inactive"
            existing_subscription.save()

        return models.UserSubscription.objects.create(
            user_email=customer_info.email,
            customer_name=customer_info.name,
            order_reference=subscription_info.order_reference,
            plan=subscription_info.plan_id,
            status="active",
            start_date=subscription_info.start_date,
            current_period_end=subscription_info.current_period_end,
        )

    @staticmethod
    def _create_new_subscription(customer_info: CustomerInfo,
                               subscription_info: SubscriptionInfo) -> models.UserSubscription:
        """Create a new subscription."""
        return models.UserSubscription.objects.create(
            user_email=customer_info.email,
            customer_name=customer_info.name,
            order_reference=subscription_info.order_reference,
            plan=subscription_info.plan_id,
            status="active",
            start_date=subscription_info.start_date,
            current_period_end=subscription_info.current_period_end,
        )


class PaymentManager:
    @staticmethod
    def create_payment(subscription: models.UserSubscription, 
                      payment_info: PaymentInfo) -> models.UserPayment:
        """Create a payment record."""
        return models.UserPayment.objects.create(
            user_subscription=subscription,
            payment_id=payment_info.payment_intent_id,
            amount=payment_info.amount,
            currency=payment_info.currency,
            payment_status=payment_info.status,
            payment_date=payment_info.payment_date,
        )