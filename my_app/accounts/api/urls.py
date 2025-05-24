from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PasswordChangeView, PasswordResetConfirmView, PasswordResetRequestView, UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
     path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # path('ppp', UserViewSet.as_view({'get':'list'}), name='a'),
]