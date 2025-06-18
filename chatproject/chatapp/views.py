import json
import logging
import uuid
from rest_framework import permissions
import stripe
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import response, status
from rest_framework.response import Response
from rest_framework.views import APIView

from chatapp import constants, controllers, serializers

from .models import UserSubscription
from .serializers import UserPaySerializer
from .stripe_webhook import StripeWebhookHandler

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class ChatHistory(APIView):
    def post(self, request):
        user = request.user
        thread_id = request.data.get("chat_thread_id", None)
        user_query = request.data.get("user_query", None)

        char_history_controller = controllers.ChatHistoryController()

        # Check if user_query is provided
        if not user_query:
            return response.Response(
                {
                    "result": False,
                    "msg": "User query not provided.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If no thread_id is provided, create a new thread
        if not thread_id:
            chat_thread = char_history_controller.create_thread(
                user=user, query=user_query, is_active=False
            )
            # Mock the chat response based on the user query
            chat_response = char_history_controller.mockchat(user_query)

            # Save the chat history
            add_history = char_history_controller.save_chat_history(
                chat_thread=chat_thread,
                query=user_query,
                response=chat_response,
            )

            # Serialize the added chat history
            serialized_data = serializers.ChatHistorySerializers(
                add_history
            ).data

            return response.Response(
                {"result": True, "msg": "Success", "data": serialized_data},
                status=status.HTTP_201_CREATED,
            )
        else:
            # Validate the thread_id format
            try:
                uuid.UUID(thread_id)
            except ValueError:
                return response.Response(
                    {
                        "result": False,
                        "msg": "Invalid thread ID format.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Retrieve the existing chat thread
            chat_thread = char_history_controller.get_thread(
                user=user, thread_id=thread_id
            )

            # Mock the chat response based on the user query
            chat_response = char_history_controller.mockchat(user_query)

            # Save the chat history
            add_history = char_history_controller.save_chat_history(
                chat_thread=chat_thread,
                query=user_query,
                response=chat_response,
            )

            # Serialize the added chat history
            serialized_data = serializers.ChatHistorySerializers(
                add_history
            ).data

            return response.Response(
                {"result": True, "msg": "Success", "data": serialized_data},
                status=status.HTTP_200_OK,
            )

    def get(self, request, thread_id=None):
        user = request.user
        chat_history_controller = controllers.ChatHistoryController()

        # Fetch chat history based on the thread_id
        chat_history_data = chat_history_controller.get_chat_history(
            user=user, thread_id=thread_id
        )

        # Serialize the retrieved chat history
        serialized_data = serializers.ChatHistorySerializers(
            chat_history_data
        ).data

        return response.Response(
            {"result": True, "msg": "Success", "data": serialized_data},
            status=status.HTTP_200_OK,
        )


class ChatBookmark(APIView):
    def get(self, request):
        user = request.user
        search_text = request.query_params.get("search_text", None)
        char_history_controller = controllers.ChatHistoryController()

        if search_text:
            chat_data = char_history_controller.search_bookmark(
                user=user, search_text=search_text
            )
        else:
            chat_data = char_history_controller.get_bookmark(user=user)
        serialized_data = serializers.ChatHistorySerializers(chat_data).data

        return response.Response(
            {"result": True, "msg": "success", "data": serialized_data}
        )

    def put(self, request):
        chat_id = request.data.get("chat_id", None)
        is_bookmark = request.data.get("is_bookmarked", False)
        char_history_controller = controllers.ChatHistoryController()

        data = char_history_controller.bookmark_chat_history(
            chat_id=chat_id, is_bookmark=is_bookmark
        )

        return response.Response(
            {
                "result": True,
                "msg": f"Successfully set bookmark to {is_bookmark}",
                "data": data,
            },
            status=status.HTTP_200_OK,
        )


class ChatThread(APIView):
    def get(self, request):
        char_history_controller = controllers.ChatHistoryController()
        user = request.user
        search_text = request.query_params.get("search_text", None)

        if search_text:
            chat_thread = char_history_controller.search_chat_thread(
                user=user, search_text=search_text
            )
        else:
            chat_thread = char_history_controller.get_all_threads(user=user)

            return response.Response(
                {"result": True, "msg": "good", "data": chat_thread}
            )
        
def payment_page(request):
    return render(request, 'payment.html', {
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLISHABLE_KEY
    })
def poster_render(request):
    return render(request,"poster.html")

@method_decorator(csrf_exempt, name='dispatch')
class CreateCheckoutSessionView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, *args, **kwargs):
        plan_id = request.data.get('plan_id')

        stripe.api_key = settings.STRIPE_SECRET_KEY

        PRICE_IDS = {
            'standard': constants.PricePlans.STANDARD,
            'premium': constants.PricePlans.PREMIUM,  
            'basic': constants.PricePlans.BASIC,  
        }

        if plan_id not in PRICE_IDS:
            return response.Response(
                {"result": False, "message": "Invalid plan ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            order_reference = str(uuid.uuid4())
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': PRICE_IDS[plan_id],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=request.build_absolute_uri('http://127.0.0.1:8000/api/v1/chatapp/poster/'),
                cancel_url=request.build_absolute_uri('/cancel/'),
                client_reference_id=order_reference,
                metadata={"payment_type": "subscription","plan_id": plan_id}
            )

            return response.Response(
                {"result": True, "sessionId": checkout_session.id, "orderReference": order_reference},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return response.Response(
                {"result": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, *args, **kwargs):
        try:
            payload = request.body
            sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
            
            if not sig_header:
                logger.error("No Stripe signature found in request headers")
                return JsonResponse({'error': 'No signature header'}, status=400)

            cli_secret = settings.STRIPE_CLI_SECRET
            webhook_secret = settings.STRIPE_WEBHOOK_SECRET
            
            # Verify the webhook
            event = StripeWebhookHandler.verify_webhook(payload, sig_header, cli_secret, webhook_secret)
            if isinstance(event, JsonResponse):
                return event

            # Handle different events based on event type
            event_type = event['type']
            metadata = event['data']['object'].get('metadata', {})

            # Check payment type to handle events separately
            payment_type = metadata.get('payment_type', 'unknown')

            # Handle subscription event (checkout.session.completed)
            if event_type == 'checkout.session.completed' and payment_type == 'subscription':
                return StripeWebhookHandler.handle_checkout_session(event)

            # Handle one-time payment event (payment_intent.succeeded)
            elif event_type == 'checkout.session.completed' and payment_type == 'one_time':
                return StripeWebhookHandler.handle_payment_intent(event)

            return JsonResponse({'status': 'Event not handled'}, status=200)

        except Exception as e:
            logger.error(f"Webhook error: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)