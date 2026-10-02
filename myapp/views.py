import razorpay

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q


from .models import (
    Cake,
    CartItem,
    Wishlist,
    Order,
    OrderItem,
    ContactMessage
)

from .recommendation import get_similar_cakes
from .personalize_recommendation import get_personalized_recommendations


User = get_user_model()


client = razorpay.Client(
    auth=(
        settings.RAZORPAY_API_KEY,
        settings.RAZORPAY_API_SECRET
    )
)


def home(request):

    if request.method == 'POST':

        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        if name and email and message:

            ContactMessage.objects.create(
                name=name,
                email=email,
                message=message
            )

            return redirect('home')

    cakes = Cake.objects.filter(available=True)

    category = request.GET.get('category')

    if category:
        cakes = cakes.filter(
            category__name__iexact=category
        )

    search = request.GET.get('q')

    if search:

        cakes = cakes.filter(
            Q(name__icontains=search) |
            Q(category__name__icontains=search) |
            Q(description__icontains=search)
        )

    if request.user.is_authenticated:

        wishlist_ids = set(
            Wishlist.objects.filter(
                user=request.user
            ).values_list('cake_id', flat=True)
        )

    else:

        wishlist_ids = set()
        personalized_cakes = []

    if request.user.is_authenticated:

        personalized_cakes = get_personalized_recommendations(
            request.user,
            limit=6
        )

    return render(request, 'home.html', {
    'cakes': cakes,
    'wishlist_ids': wishlist_ids,
    'personalized_cakes': personalized_cakes
})


def cake_detail(request, cake_id):

    cake = get_object_or_404(
        Cake,
        id=cake_id,
        available=True
    )

    recommendations = get_similar_cakes(
        cake_id=cake.id,
        limit=6
    )

    return render(request, 'cake_detail.html', {
        'cake': cake,
        'recommendations': recommendations
    })


def register(request):

    if request.method == 'POST':

        username = request.POST['username']
        email = request.POST['email']
        phone = request.POST['phone']
        address = request.POST['address']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:

            return render(request, 'register.html', {
                'error': 'Passwords do not match'
            })

        if User.objects.filter(username=username).exists():

            return render(request, 'register.html', {
                'error': 'Username already exists'
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone=phone,
            address=address
        )

        user.save()

        return redirect('login')

    return render(request, 'register.html')


def user_login(request):

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('home')

        return render(request, 'login.html', {
            'error': 'Invalid username or password'
        })

    return render(request, 'login.html')


@login_required
def add_to_cart(request, cake_id):

    cake = get_object_or_404(
        Cake,
        id=cake_id,
        available=True
    )

    if request.method == 'POST':

        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            cake=cake
        )

        if not created:

            cart_item.quantity += 1
            cart_item.save()

    return redirect('home')


@login_required
def cart(request):

    cart_items = CartItem.objects.filter(
        user=request.user
    ).select_related('cake')

    total_amount = sum(
        item.cake.price * item.quantity
        for item in cart_items
    )

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_amount': total_amount
    })


@login_required
def checkout(request):

    cart_items = CartItem.objects.filter(
        user=request.user
    ).select_related('cake')

    if not cart_items.exists():

        return redirect('cart')

    total_amount = sum(
        item.cake.price * item.quantity
        for item in cart_items
    )

    return render(request, 'checkout.html', {

        'cart_items': cart_items,

        'total_amount': total_amount,

        # Demo payment details
        'razorpay_order_id': 'demo_order_123',

        'razorpay_key_id': 'demo_key',

        'razorpay_amount': int(total_amount * 100)

    })


@login_required
def place_order(request):

    if request.method != 'POST':

        return redirect('cart')

    cart_items = CartItem.objects.filter(
        user=request.user
    ).select_related('cake')

    if not cart_items.exists():

        return redirect('cart')

    total_amount = sum(
        item.cake.price * item.quantity
        for item in cart_items
    )

    payment_method = request.POST.get(
        'payment_method',
        'COD'
    )

    if payment_method == 'RAZORPAY':

        payment_data = {
            'razorpay_order_id': request.POST.get(
                'razorpay_order_id'
            ),
            'razorpay_payment_id': request.POST.get(
                'razorpay_payment_id'
            ),
            'razorpay_signature': request.POST.get(
                'razorpay_signature'
            )
        }

        if not all(payment_data.values()):

            return render(request, 'checkout.html', {
                'cart_items': cart_items,
                'total_amount': total_amount,
                'error': 'Payment details are missing.'
            })

        try:

            client.utility.verify_payment_signature(
                payment_data
            )

        except razorpay.errors.SignatureVerificationError:

            return render(request, 'checkout.html', {
                'cart_items': cart_items,
                'total_amount': total_amount,
                'error': 'Payment verification failed.'
            })

        except Exception:

            return render(request, 'checkout.html', {
                'cart_items': cart_items,
                'total_amount': total_amount,
                'error': 'Something went wrong during payment verification.'
            })

    order = Order.objects.create(
        user=request.user,
        total_amount=total_amount,
        payment_method=payment_method
    )

    for item in cart_items:

        OrderItem.objects.create(
            order=order,
            cake=item.cake,
            quantity=item.quantity,
            price=item.cake.price
        )

    cart_items.delete()

    return render(request, 'order_success.html', {
        'order': order
    })


@login_required
def toggle_wishlist(request, cake_id):

    cake = get_object_or_404(
        Cake,
        id=cake_id,
        available=True
    )

    wishlist_items = Wishlist.objects.filter(
        user=request.user,
        cake=cake
    )

    if wishlist_items.exists():

        wishlist_items.delete()

    else:

        Wishlist.objects.create(
            user=request.user,
            cake=cake
        )

    return redirect('home')


@login_required
def wishlist(request):

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('cake')

    return render(request, 'wishlist.html', {
        'wishlist_items': wishlist_items
    })


def user_logout(request):

    logout(request)

    return redirect('login')


@login_required
def orders(request):

    user_orders = Order.objects.filter(
        user=request.user
    ).prefetch_related('items__cake').order_by('-ordered_at')

    return render(request, 'orders.html', {
        'orders': user_orders
    })


@login_required
def order_now(request, cake_id):

    cake = get_object_or_404(
        Cake,
        id=cake_id,
        available=True
    )

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        cake=cake
    )

    if not created:

        cart_item.quantity = 1
        cart_item.save()

    return redirect('checkout')