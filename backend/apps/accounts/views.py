from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import ScopedRateThrottle, AnonRateThrottle
from django.db.models import Q
from config.permissions import IsResourceOwnerOrReadOnly
from config.exceptions import InvalidCredentials

from .models import Profile, MetodoPago, Resena
from .serializers import UserSerializer, ProfileSerializer, MetodoPagoSerializer, ResenaSerializer
from .profile_insights import (
    accessible_profiles_for,
    build_profile_summary,
    profile_activity_queryset,
    serialize_profile_activity,
)


class ProfileActivityPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response({"count": self.page.paginator.count, "next": self.get_next_link(), "previous": self.get_previous_link(), "results": data})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]

    @action(detail=False, methods=['post'], url_path='cambiar-password')
    def change_password(self, request):
        user = request.user
        old_password = request.data.get('old_password', '')
        if not isinstance(old_password, str) or not user.check_password(old_password):
            raise ValidationError({'old_password': 'La contraseña actual es incorrecta.'})
        value = request.data.get('new_password', '')
        if not isinstance(value, str):
            raise ValidationError({'new_password': 'Introduce una contraseña válida.'})
        try:
            validate_password(value, user=user)
        except DjangoValidationError as exc:
            raise ValidationError({'new_password': exc.messages}) from exc
        user.set_password(value)
        user.save(update_fields=['password'])
        return Response({'mensaje': 'Contraseña actualizada. Inicia sesión de nuevo.'})

    def get_throttles(self):
        if self.action in ('create', 'change_password'):
            self.throttle_scope = 'authentication'
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def is_owner(self, obj, user):
        return obj == user

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return super().get_permissions()

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]

    def get_queryset(self):
        return accessible_profiles_for(self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def is_owner(self, obj, user):
        return obj.user_id == user.id

    @action(detail=True, methods=["get"])
    def resumen(self, request, pk=None):
        return Response(build_profile_summary(self.get_object(), request))

    @action(detail=True, methods=["get"])
    def actividad(self, request, pk=None):
        activity_type = request.query_params.get("tipo", "")
        queryset = profile_activity_queryset(self.get_object(), request.user, activity_type)
        paginator = ProfileActivityPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(serialize_profile_activity(page, activity_type))

class MetodoPagoViewSet(viewsets.ModelViewSet):
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer

    def get_queryset(self):
        return MetodoPago.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ResenaViewSet(viewsets.ModelViewSet):
    queryset = Resena.objects.all()
    serializer_class = ResenaSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]

    def get_queryset(self):
        return Resena.objects.filter(
            Q(emisor=self.request.user)
            | Q(receptor=self.request.user)
            | Q(receptor__profile__perfil_publico=True)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(emisor=self.request.user)

    def is_owner(self, obj, user):
        return obj.emisor_id == user.id

class AuthenticationThrottle(AnonRateThrottle):
    scope = 'authentication'


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthenticationThrottle])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            "mensaje": "Login exitoso",
            "username": user.username,
            "user_id": user.id,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)
    raise InvalidCredentials()
