from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from products.models import Product
from products.seriallizers import ProductSerializer
from .models import Order, OrderDetail


class CreateOrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = ['product', 'quantity']


class OrderDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderDetail
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    order_details = OrderDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'order_details', 'name', 'phone', 'address', 'total_amount', 'created_at']


class CreateOrderSerializer(serializers.ModelSerializer):
    order_details = CreateOrderDetailSerializer(many=True)
    total_amount = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Order
        fields = ['id', 'user', 'order_details', 'name', 'phone', 'address', 'total_amount', 'created_at']

    def create(self, validated_data):
        order_details_data = validated_data.pop('order_details')

        with transaction.atomic():
            total_amount = 0
            order = Order.objects.create(**validated_data)

            for order_detail_data in order_details_data:
                product = order_detail_data['product']
                quantity = order_detail_data['quantity']

                if product.quantity < quantity:
                    raise ValidationError(f"Số lượng sản phẩm {product.name} không đủ.")

                product.quantity -= quantity
                product.save()

                total_amount += product.price * quantity
                OrderDetail.objects.create(order=order, **order_detail_data)

            order.total_amount = total_amount
            order.save()
        return order
