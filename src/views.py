from rest_framework import status
from rest_framework.decorators import api_view, action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from src.serializers import UserSerializer, ChangePasswordSerializer
from django_filters import rest_framework as filters


@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    # Kiểm tra xác thực người dùng
    user = authenticate(username=username, password=password)
    if user is not None:
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'access_exp': refresh.access_token.payload['exp'],
                'user': UserSerializer(user).data
            }
        )
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def logout_view(request):
    # Đăng xuất
    refresh_token = request.data.get('refresh_token')
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logged out successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def register_view(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IsSuperUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated

        return False


class BasePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'pageSize'


class UserFilter(filters.FilterSet):
    date_joined_before = filters.DateFilter(field_name='date_joined', lookup_expr='gte')
    date_joined_after = filters.DateFilter(field_name='date_joined', lookup_expr='lte')

    class Meta:
        model = User
        fields = {
            'date_joined': ['range'],
            'is_superuser': ['exact'],
            'is_active': ['exact'],
        }


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsSuperUserOrReadOnly]
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserSerializer
    pagination_class = BasePagination
    filter_backends = [SearchFilter, OrderingFilter, filters.DjangoFilterBackend]
    filterset_class = UserFilter
    search_fields = ['username']
    ordering_fields = '__all__'

    def list(self, request, *args, **kwargs):
        if 'query_all' in request.query_params:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        else:
            return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def change_password(self, request, *args, **kwargs):
        password = request.data.get('new_password', None)

        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            validate_password(password)
        except Exception as e:
            error_message = 'invalid'
            if e and e.messages:
                error_message = ', '.join(e.messages)
            raise ValidationError(error_message)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': ['Incorrect password.']}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully.'})
