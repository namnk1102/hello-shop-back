from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters import rest_framework as filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response

from products.models import Product
from products.seriallizers import ProductSerializer


class IsSuperUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        if request.method in SAFE_METHODS:
            return True

        if request.user == 'PUT' or request.method == 'PATCH':
            return request.user == view.get_object().user

        return False


class BasePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'pageSize'


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSuperUserOrReadOnly]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = BasePagination
    filter_backends = [SearchFilter, OrderingFilter, filters.DjangoFilterBackend]
    filterset_fields = ['type']
    search_fields = ['name', 'price', 'type']
    ordering_fields = '__all__'

    def list(self, request, *args, **kwargs):
        if 'query_all' in request.query_params:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        else:
            return super().list(request, *args, **kwargs)