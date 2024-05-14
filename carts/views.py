from django.db import transaction
from django.shortcuts import redirect
from rest_framework import viewsets, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from django_filters import rest_framework as filters

from carts.models import Cart, CartItem
from carts.serializers import CartSerializer, CartItemSerializer, CartItemWriteSerializer
from products.models import Product


class IsSuperUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        return request.user and request.user.is_authenticated


class BasePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'pageSize'


# class CartViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsSuperUserOrReadOnly, IsAuthenticated]
#     queryset = Cart.objects.all().order_by('-id')
#     serializer_class = CartSerializer
#     pagination_class = BasePagination
#     # search_fields = ['user__username', 'product__name', 'product__price']
#     ordering_fields = '__all__'
#     #
#     # def get_queryset(self):
#     #     user = self.request.user
#     #     return Cart.objects.filter(user=user)
#
#
# class CartItemViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsSuperUserOrReadOnly]
#     queryset = CartItem.objects.all()
#     serializer_class = CartItemSerializer
#
    # def create(self, request, *args, **kwargs):
    #     user = request.user
    #     cart = Cart.objects.filter(user=user)
    #
    #     if cart.exists():
    #         request.data['cart'] = cart.get().id
    #         return super().create(request, *args, **kwargs)
    #
    #     new_cart = CartSerializer(instance=user).data
    #     request.data['cart'] = new_cart.get().id
    #     return super().create(request, *args, **kwargs)
#
#     # def perform_create(self, serializer):
#     #     user = self.request.user
#     #     cart = Cart.objects.filter(user=user)
#     #
#     #     if cart.exists():
#     #         serializer['cart'] = cart.get().id
#     #         return super().perform_create(serializer)
#     #
#     #     new_cart = CartSerializer(instance=user).data
#     #     serializer['cart'] = new_cart.get().id
#     #     return super().perform_create(serializer)


class CartViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSuperUserOrReadOnly]
    pagination_class = BasePagination
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        with transaction.atomic():
            products = instance.items.all()
            for product in products:
                product.delete()

            self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSuperUserOrReadOnly]
    pagination_class = BasePagination
    queryset = CartItem.objects.all()
    serializer_class_by_actions = {
        "GET": CartItemSerializer,
        "POST": CartItemWriteSerializer,
        "PATCH": CartItemSerializer,
        "DELETE": CartItemSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_class_by_actions[self.request.method]

    def create(self, request, *args, **kwargs):
        user = request.user
        cart = Cart.objects.filter(user=user)
        product = Product.objects.get(id=request.data['product'])

        if request.data['quantity'] > product.quantity:
            return Response("Quantity in stock is not enough", status=status.HTTP_400_BAD_REQUEST)

        if cart.exists():
            request.data['cart'] = cart.get().id
            cart_item = CartItem.objects.filter(cart=cart.get(), product_id=request.data['product'])

            if cart_item.exists():
                request.data['quantity'] += cart_item.get().quantity

                if request.data['quantity'] > product.quantity:
                    return Response("Quantity in stock is not enough", status=status.HTTP_400_BAD_REQUEST)

                serializer = self.get_serializer(cart_item.get(), data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                if getattr(cart_item.get(), '_prefetched_objects_cache', None):
                    # If 'prefetch_related' has been applied to a queryset, we need to
                    # forcibly invalidate the prefetch cache on the instance.
                    cart_item.get()._prefetched_objects_cache = {}
                return Response(serializer.data)

            return super().create(request, *args, **kwargs)

        new_cart = CartSerializer(data={
            "user": request.user.id
        })
        if new_cart.is_valid():
            new_cart.save()
            request.data['cart'] = new_cart.instance.id
            return super().create(request, *args, **kwargs)

        return Response("User not found", status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        quantity = request.data.get('quantity', 0)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if quantity > instance.product.quantity:
            return Response("Quantity in stock is not enough", status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
