from django.urls import path, include
from rest_framework import routers
from .views import AnthropometricStatisticViewSet, AnthropometricTableViewSet, PersonViewSet, MeasurementViewSet, StudyViewSet, MeasurementTypeViewSet

router = routers.DefaultRouter()
router.register(r'persons', PersonViewSet)
router.register(r'measurements', MeasurementViewSet)
router.register(r'studies', StudyViewSet)
router.register(r'measurement-types', MeasurementTypeViewSet)
router.register(r'table', AnthropometricTableViewSet)
router.register(r'statistic', AnthropometricStatisticViewSet)
urlpatterns = [
    path('', include(router.urls)),   
]
