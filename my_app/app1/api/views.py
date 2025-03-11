from rest_framework import viewsets, status
from rest_framework.response import Response
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
    
    def create(self, request, *args, **kwargs):
        study_id = request.data.get("study")
        statistics_data = request.data.get("statistics", [])

        try:
            study = Study.objects.get(id=study_id)
            table = AnthropometricTable.objects.create(study=study)

            for stat in statistics_data:
                measurement_type = MeasurementType.objects.get(id=stat["measurement_type"])
                AnthropometricStatistic.objects.create(
                    table=table,
                    measurement_type=measurement_type,
                    mean=stat["mean"],
                    sd=stat["sd"],
                    percentile_5=stat.get("percentile_5"),
                    percentile_10=stat.get("percentile_10"),
                    percentile_25=stat.get("percentile_25"),
                    percentile_50=stat.get("percentile_50"),
                    percentile_75=stat.get("percentile_75"),
                    percentile_90=stat.get("percentile_90"),
                    percentile_95=stat.get("percentile_95")
                )

            return Response({"message": "Tabla creada correctamente"}, status=status.HTTP_201_CREATED)
        except Study.DoesNotExist:
            return Response({"error": "El estudio no existe"}, status=status.HTTP_400_BAD_REQUEST)
        except MeasurementType.DoesNotExist:
            return Response({"error": "El tipo de medición no existe"}, status=status.HTTP_400_BAD_REQUEST)

class AnthropometricStatisticViewSet(viewsets.ModelViewSet):
    queryset = AnthropometricStatistic.objects.all()
    serializer_class = AnthropometricStatisticSerializer

