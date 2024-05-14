from django.contrib.auth.models import User
from django.db import models

from products.models import Product


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, related_name='orders', through='OrderDetail')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=255)
    total_amount = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class OrderDetail(models.Model):
    order = models.ForeignKey(Order, related_name='order_details', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_details', on_delete=models.CASCADE)
    quantity = models.IntegerField()
