from rest_framework import viewsets
from app1.models import AnthropometricStatistic, AnthropometricTable, Person, Measurement, Study, MeasurementType
from app1.api.serializer import AnthropometricStatisticSerializer, AnthropometricTableSerializer, PersonSerializer, MeasurementSerializer, StudySerializer, MeasurementTypeSerializer

class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer

class MeasurementTypeViewSet(viewsets.ModelViewSet):
    queryset = MeasurementType.objects.all()
    serializer_class = MeasurementTypeSerializer

class MeasurementViewSet(viewsets.ModelViewSet):
    queryset = Measurement.objects.all()
    serializer_class = MeasurementSerializer

class StudyViewSet(viewsets.ModelViewSet):
    queryset = Study.objects.all()
    serializer_class = StudySerializer

class AnthropometricTableViewSet(viewsets.ModelViewSet):
    queryset = AnthropometricTable.objects.all()
    serializer_class = AnthropometricTableSerializer

class AnthropometricStatisticViewSet(viewsets.ModelViewSet):
    queryset = AnthropometricStatistic.objects.all()
    serializer_class = AnthropometricStatisticSerializer

