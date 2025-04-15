from django.urls import path, include
from rest_framework import routers
from .views import Perceptil, PersonViewSet, MeasurementViewSet, StudyDataView, StudyDimensionViewSet, StudyViewSet, DimensionViewSet

router = routers.DefaultRouter()
router.register(r'persons', PersonViewSet)
router.register(r'measurements', MeasurementViewSet)
router.register(r'studies', StudyViewSet)
router.register(r'dimension', DimensionViewSet)
# router.register(r'table', AnthropometricTableViewSet)
# router.register(r'statistic', AnthropometricStatisticViewSet)
router.register(r'studydim', StudyDimensionViewSet)
urlpatterns = [
    path('', include(router.urls)),   
    path('study-data/<int:study_id>/', StudyDataView.as_view(), name='study-data'),
    path('test-percentiles/<int:study_id>/', Perceptil.as_view(), name='test_percentiles'),
]
