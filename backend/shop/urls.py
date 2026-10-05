from django.urls import path

from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('koszyk/', views.cart_detail, name='cart'),
    path('koszyk/zmien/', views.cart_update, name='cart_update'),
    path('koszyk/dodaj/<slug:slug>/', views.cart_add, name='cart_add'),
    path('zamowienie/', views.checkout, name='checkout'),
    path('zamowienie/<uuid:token>/', views.order_detail, name='order_detail'),
    path('platnosc/<uuid:token>/', views.payment_dummy, name='payment_dummy'),
    # Na końcu: adres produktu łapie każdy pojedynczy segment
    path('<slug:slug>/', views.product_detail, name='detail'),
]
