from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, MetodoPago, Resena
from config.serializer_fields import MediaFileField
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    def validate_password(self, value):
        validate_password(value, user=self.instance)
        return value

    def update(self, instance, validated_data):
        # Password changes must use the dedicated endpoint and verify the old secret.
        if 'password' in validated_data:
            raise serializers.ValidationError({'password': 'Usa la operación cambiar-password.'})
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not request or request.user.pk != instance.pk:
            data.pop('email', None)
        return data

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        # extra_kwargs oculta la contraseña para que nunca se envíe de regreso al Frontend por seguridad
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # ¡LA SOLUCIÓN! Usamos create_user() en lugar de un guardado normal
        # Esto obliga a Django a encriptar (hashear) la contraseña en la base de datos
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class ProfileSerializer(serializers.ModelSerializer):
    avatar = MediaFileField(required=False, allow_null=True)

    def validate_biografia(self, value):
        return value.strip()

    class Meta:
        model = Profile
        fields = ["id", "user", "biografia", "ubicacion", "reputacion", "perfil_publico", "avatar", "fecha_registro"]
        read_only_fields = ['user', 'reputacion']

class MetodoPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetodoPago
        fields = '__all__'
        read_only_fields = ['user']

class ResenaSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        emisor = self.context['request'].user
        receptor = attrs.get('receptor', getattr(self.instance, 'receptor', None))
        if receptor == emisor:
            raise serializers.ValidationError("No puedes reseñarte a ti mismo.")
        duplicate = Resena.objects.filter(emisor=emisor, receptor=receptor)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError("Ya reseñaste a este usuario.")
        return attrs

    class Meta:
        model = Resena
        fields = '__all__'
        read_only_fields = ['emisor']
