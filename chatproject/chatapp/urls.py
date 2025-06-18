from django.urls import path

from . import views

urlpatterns = [
    path("chat/", views.ChatHistory.as_view(), name="chat"),
    path(
        "chat/<str:thread_id>/",
        views.ChatHistory.as_view(),
        name="get_chat_conversations",
    ),
    path("thread/", views.ChatThread.as_view(), name="chat_threads"),
    path("bookmark/", views.ChatBookmark.as_view(), name="chat_bookmark"),
      path(
        'create-checkout-session/', 
        views.CreateCheckoutSessionView.as_view(), 
        name='create-checkout-session'
    ),
     path('webhook/',
          views.StripeWebhookView.as_view(), 
          name='stripe-webhook'
    ),
     path('payment/', views.payment_page, name='payment_page'),
     path('poster/', views.poster_render, name='poster'),

]
