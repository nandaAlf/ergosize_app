from rest_framework import viewsets, permissions
# from accounts.models import User
from accounts.models import User
from accounts.api.serializers import MyTokenObtainPairSerializer, PasswordChangeSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, UserSerializer, UserCreateSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_bytes, smart_str
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from rest_framework.decorators import action

class MyTokenObtainPairView(TokenObtainPairView):
    print("there not wono")
    serializer_class = MyTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]  
    queryset = User.objects.all()
    # Elegimos el serializer según la acción
    def get_serializer_class(self):
        if self.action in ['create']:
            return UserCreateSerializer
        return UserSerializer

    # Controla permisos por acción
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action in ['list', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        GET /api/users/me/
        Devuelve los datos del usuario autenticado.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
class PasswordChangeView(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    serializer_class    = PasswordChangeSerializer
    permission_classes  = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Si es válido, cambiar la contraseña
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({"detail": "Contraseña actualizada correctamente."}, status=status.HTTP_200_OK)
    
class PasswordResetRequestView(GenericAPIView):
    """
    Recibe {email} y envía un link de reseteo por email.
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]  # Permite acceso sin autenticación
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
             # Devuelve éxito aunque el usuario no exista por razones de seguridad
            return Response({"detail": "Si existe una cuenta con este email, se ha enviado un enlace de recuperación"}, 
                           status=status.HTTP_200_OK)
      
        uidb64 = urlsafe_base64_encode(smart_bytes(user.pk))
        token  = default_token_generator.make_token(user)

        reset_link = f"{settings.FRONTEND_URL}reset-password?uidb64={uidb64}&token={token}"
        print("reset_link",reset_link)
        # Envío de email
        send_mail(
            subject="Restablecer contraseña",
            message=f"Usa este enlace para restablecer tu contraseña:\n\n{reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return Response({"detail": "Email de reseteo enviado."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(GenericAPIView):
    """
    Recibe {uidb64, token, new_password, confirm_password}
    y cambia la contraseña.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Contraseña restablecida correctamente."}, status=status.HTTP_200_OK)