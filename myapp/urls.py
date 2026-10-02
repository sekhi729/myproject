from django.urls import path
from . import views


urlpatterns = [

    path(
        '',
        views.home,
        name='home'
    ),

    path(
        'cake/<int:cake_id>/',
        views.cake_detail,
        name='cake_detail'
    ),

    path(
        'cart/add/<int:cake_id>/',
        views.add_to_cart,
        name='add_to_cart'
    ),

    path(
        'cart/',
        views.cart,
        name='cart'
    ),

    path(
        'checkout/',
        views.checkout,
        name='checkout'
    ),

    path(
        'place-order/',
        views.place_order,
        name='place_order'
    ),

    path(
        'wishlist/<int:cake_id>/',
        views.toggle_wishlist,
        name='toggle_wishlist'
    ),

    path(
        'wishlist/',
        views.wishlist,
        name='wishlist'
    ),

    path(
        'register/',
        views.register,
        name='register'
    ),

    path(
        'login/',
        views.user_login,
        name='login'
    ),

    path(
        'logout/',
        views.user_logout,
        name='logout'
    ),

    path('orders/', views.orders, name='orders'),

    path(
    'order-now/<int:cake_id>/',
    views.order_now,
    name='order_now'
),
]