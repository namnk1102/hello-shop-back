from rest_framework import serializers

from products.seriallizers import ProductSerializer
from .models import Cart, CartItem


class CartSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Cart
        fields = ['user', 'products']

    def get_products(self, cart):
        cart_items = CartItem.objects.filter(cart=cart)

        serializer = CartItemSerializer(cart_items, many=True)

        serialized_data = serializer.data

        cart_items_array = []
        for item in serialized_data:
            cart_items_array.append(item)

        return cart_items_array


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = '__all__'


class CartItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'
