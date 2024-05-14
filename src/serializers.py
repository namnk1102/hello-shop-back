from rest_framework import serializers
from django.contrib.auth.models import User

from carts.models import Cart
from carts.serializers import CartSerializer


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    cart = serializers.SerializerMethodField(read_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    class Meta:
        model = User
        fields = ['id', 'is_superuser', 'username', 'date_joined', 'is_active',
                  'last_login', 'email', 'first_name', 'last_name', 'password', 'cart']

    def get_cart(self, user):
        cart = Cart.objects.filter(user_id=user.id)
        if cart.exists():
            return cart.get().id
        return None


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
