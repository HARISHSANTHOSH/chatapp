# import base64
# import os

# from django.template.loader import render_to_string
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Attachment, Mail, To

# from .exceptions import CustomException

# sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
# from_mail = os.getenv("FROM_EMAIL")


# def mail_engine(message):
#     try:
#         sg = SendGridAPIClient(sendgrid_api_key)
#         response = sg.send(message)
#         print(response)
#         print(response.status_code)
#         print(response.body)
#         print(response.headers)
#     except Exception as e:
#         print(f"Error sending email: {e}")
#         CustomException(
#             detail={
#                 "result": False,
#                 "msg": "Error sending email",
#             },
#             code="Email Error",
#         )


# def send_subscription_confirmation(user_subscription):
#     """
#     Sends email for new subscription
#     """
#     payment = user_subscription.payments.latest("payment_date")

#     # Prepare the context for rendering the email template
#     context = {
#         "customer_name": user_subscription.customer_name,
#         "plan": user_subscription.plan,
#         "email": user_subscription.user_email,
#         "start_date": user_subscription.start_date,
#         "current_period_end": user_subscription.current_period_end,
#         "is_upgrade": False,  # This is for a new subscription, change it to True for an upgrade
#         "payment_amount": (
#             payment.amount if payment else None
#         ),  # Payment amount (if available)
#         "payment_currency": (
#             payment.currency if payment else "INR"
#         ),  # Payment currency (if available)
#         "payment_id": (
#             payment.payment_id if payment else None
#         ),  # Payment ID (if available)
#         "payment_status": (
#             payment.payment_status if payment else None
#         ),  # Payment status (if available)
#         "payment_date": (
#             payment.payment_date if payment else None
#         ),  # Payment date (if available)
#     }

#     html_content = render_to_string("subscription.html", context)

#     email_message = Mail(
#         from_email="customer@ai4dei.ai",
#         to_emails=user_subscription.user_email,
#         subject=f"Welcome to Your New Subscription!",
#         html_content=html_content,
#     )

#     return mail_engine(email_message)


# def send_upgrade_email(user_subscription):
#     """
#     Sends email for subscription upgrade
#     """
#     # Get the latest payment for the upgrade
#     payment = user_subscription.payments.latest("payment_date")

#     context = {
#         "customer_name": user_subscription.customer_name,
#         "plan": user_subscription.plan,
#         "email": user_subscription.user_email,
#         "current_period_end": user_subscription.current_period_end,
#         "is_upgrade": True,
#         "payment_amount": (
#             payment.amount if payment else None
#         ),  # Payment amount (if available)
#         "payment_currency": (
#             payment.currency if payment else "INR"
#         ),  # Payment currency (if available)
#         "payment_id": (
#             payment.payment_id if payment else None
#         ),  # Payment ID (if available)
#         "payment_status": (
#             payment.payment_status if payment else None
#         ),  # Payment status (if available)
#         "payment_date": (
#             payment.payment_date if payment else None
#         ),  # Payment date (if available)
#     }

#     html_content = render_to_string("subscription.html", context)

#     email_message = Mail(
#         from_email="customer@ai4dei.ai",
#         to_emails=user_subscription.user_email,
#         subject=f"Your Subscription Has Been Updated!",
#         html_content=html_content,
#     )

#     return mail_engine(email_message)
