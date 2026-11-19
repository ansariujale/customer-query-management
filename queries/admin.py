from django.contrib import admin

from .models import CustomerQuery


@admin.register(CustomerQuery)
class CustomerQueryAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'customer_name', 'category', 'priority', 'status', 'created_at']
    list_filter = ['category', 'priority', 'status']
    search_fields = ['customer_name', 'email', 'subject']
