from django.db import models

# Create your models here.

class Currency(models.Model):
    currency_code = models.CharField(max_length=10, null=False)
    currency_name = models.CharField(max_length=20, null=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_created=True)
    updated_at = models.DateTimeField(auto_now_add=True)


class Exchange(models.Model):
    exchange_code = models.CharField(max_length=10, null=False)
    exchange_name = models.CharField(max_length=100, null=False)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_created=True)
    updated_at = models.DateTimeField(auto_now_add=True)

class Stock(models.Model):
    name = models.CharField(max_length=100)
