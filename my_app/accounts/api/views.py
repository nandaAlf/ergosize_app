from rest_framework import viewsets, permissions
# from accounts.models import User
from accounts.models import User
from accounts.api.serializers import MyTokenObtainPairSerializer, UserSerializer, UserCreateSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class MyTokenObtainPairView(TokenObtainPairView):
    print("there not wono")
    serializer_class = MyTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    # Elegimos el serializer según la acción
    def get_serializer_class(self):
        if self.action in ['create']:
            return UserCreateSerializer
        return UserSerializer

    # Controla permisos por acción
    def get_permissions(self):
        if self.action in ['list', 'destroy', 'create']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]