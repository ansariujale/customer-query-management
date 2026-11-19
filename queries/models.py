from django.contrib.auth.models import User
from django.db import models


class CustomerQuery(models.Model):

    CATEGORY_CHOICES = [
        ('Technical', 'Technical'),
        ('Billing', 'Billing'),
        ('General', 'General'),
        ('Account Related', 'Account Related'),
    ]

    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]

    # the logged in user who added this query
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='queries')

    customer_name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    description = models.TextField()

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='General')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    # filled after AI analysis
    suggested_response = models.TextField(blank=True)
    analysed_by = models.CharField(max_length=20, blank=True)  # "gemini" or "fallback"
    analysed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Customer queries'

    def __str__(self):
        return f'{self.subject} ({self.customer_name})'
