from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from accounts.models import User
from django.contrib.auth import password_validation
from django.utils.http import  urlsafe_base64_decode
from django.utils.encoding import smart_bytes, smart_str
from django.contrib.auth.tokens import default_token_generator
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Añadimos el campo `role` al payload
        token['role'] = user.role  
        return token


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email','first_name','last_name' ,'role',
            'institucion', 'profesion',
        ]
       
        
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['password']

    def create(self, validated_data):
        validated_data['role'] = User.USUARIO  # Fuerza a ser 'usuario' al registrarse
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user


class PasswordChangeSerializer(serializers.Serializer):
    old_password     = serializers.CharField(write_only=True)
    new_password     = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual no es correcta.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Las nuevas contraseñas no coinciden.")
        # Opcional: aplicar validadores de Django (longitud, complejidad, etc.)
        password_validation.validate_password(attrs['new_password'], self.context['request'].user)
        return attrs
    
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("No existe ningún usuario con ese email.")
        return email

class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64     = serializers.CharField()
    token      = serializers.CharField()
    new_password     = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        try:
            uid = smart_str(urlsafe_base64_decode(attrs['uidb64']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("UID inválido.")

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError("Token inválido o expirado.")

        attrs['user'] = user
        return attrs    
