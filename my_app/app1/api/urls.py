from django.urls import path, include
from rest_framework import routers
from .views import Perceptil, PersonViewSet, MeasurementViewSet, StudyDimensionViewSet, StudyViewSet, DimensionViewSet, export_excel_percentiles, export_pdf_percentiles, generar_pdf_ficha

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
    # path('study-data/<int:study_id>/', StudyDataView.as_view(), name='study-data'),
    path('test-percentiles/<int:study_id>/', Perceptil.as_view(), name='test_percentiles'),
    path('export/excel/<int:study_id>/', export_excel_percentiles, name='export_excel'),
    path('export/pdf/<int:study_id>/', export_pdf_percentiles, name='export_pdf'),
    # path('import/excel/', preview_excel_percentiles, name='import_excel'),
    path('report/', generar_pdf_ficha, name='b'),
]
