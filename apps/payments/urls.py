from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('record/<int:order_id>/', views.record_payment, name='record_payment'),
]

