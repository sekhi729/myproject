from django.contrib import admin
from .models import (
    CustomUser,
    Category,
    Cake,
    Order,
    OrderItem,
    ContactMessage
)


admin.site.register(CustomUser)
admin.site.register(Category)


@admin.register(Cake)
class CakeAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'category',
        'price',
        'available'
    )

    search_fields = (
        'name',
        'category__name'
    )


admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ContactMessage)