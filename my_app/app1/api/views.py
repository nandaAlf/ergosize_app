from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from app1.models import AnthropometricStatistic, AnthropometricTable, Person, Measurement, Study, Dimension, StudyDimension
from app1.api.serializer import AnthropometricStatisticSerializer, AnthropometricTableSerializer, PersonSerializer, MeasurementSerializer, StudyDimensionSerializer, StudySerializer, DimensionSerializer
from django.http import JsonResponse
from django.views import View
from django.db import connection

class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer

class DimensionViewSet(viewsets.ModelViewSet):
    queryset = Dimension.objects.all()
    serializer_class = DimensionSerializer

class MeasurementViewSet(viewsets.ModelViewSet):
    queryset = Measurement.objects.all()
    serializer_class = MeasurementSerializer
    # permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden eliminar

    def destroy(self, request, *args, **kwargs):
        # Obtener el study_id y person_id de la solicitud
        study_id=self.kwargs.get('pk')
        person_id = request.data.get('person_id')

        if not study_id or not person_id:
            return Response(
                {"error": "Se requieren study_id y person_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # # Verificar permisos adicionales si es necesario
        # if not request.user.has_perm('app.delete_measurement'):
        #     return Response(
        #         {"error": "No tienes permisos para eliminar estas mediciones"},
        #         status=status.HTTP_403_FORBIDDEN,
        #     )

        # Eliminar todos los registros de Measurement que coincidan
        Measurement.objects.filter(study_id=study_id, person_id=person_id).delete()

        # Puedes usar señales (signals) de Django para ejecutar acciones adicionales antes o después de la eliminación.

        return Response(
            {"message": "Mediciones eliminadas correctamente"},
            status=status.HTTP_204_NO_CONTENT,
        )

class StudyViewSet(viewsets.ModelViewSet):
    queryset = Study.objects.all()
    serializer_class = StudySerializer

class StudyDimensionViewSet(viewsets.ModelViewSet):
    queryset = StudyDimension.objects.all()
    serializer_class = StudyDimensionSerializer


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
                measurement_type = Dimension.objects.get(id=stat["measurement_type"])
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
        except Dimension.DoesNotExist:
            return Response({"error": "El tipo de medición no existe"}, status=status.HTTP_400_BAD_REQUEST)

class AnthropometricStatisticViewSet(viewsets.ModelViewSet):
    queryset = AnthropometricStatistic.objects.all()
    serializer_class = AnthropometricStatisticSerializer


from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.shortcuts import get_object_or_404

class StudyDataView(View):
    """
    Vista para obtener los datos de un estudio específico, incluyendo las personas
    y sus mediciones en las dimensiones asociadas.
    """

    def get(self, request, study_id):
        """
        Maneja las solicitudes GET para obtener los datos del estudio.
        
        Args:
            request: La solicitud HTTP.
            study_id: El ID del estudio.
        
        Returns:
            JsonResponse: Un JSON con los datos del estudio.
        """
        # Verificar que el estudio existe
        study = get_object_or_404(Study, id=study_id)

        # Obtener los datos del estudio
        try:
            data = self.get_study_data_json(study_id)
            return JsonResponse(data, safe=False, status=200)
        except Exception as e:
            # Manejar errores en la consulta o procesamiento
            return JsonResponse({"error": str(e)}, status=500)

    
    def get_study_dimensions(self, study_id):
        """
        Obtiene todas las dimensiones asociadas al estudio desde la tabla StudyDimension.
        
        Args:
            study_id: El ID del estudio.
        
        Returns:
            list: Una lista de nombres de dimensiones.
        """
        dimensions = StudyDimension.objects.filter(id_study_id=study_id).values_list('id_dimension__name', flat=True)
        return list(dimensions)
    
    def get_study_data(self, study_id):
        """
        Obtiene los datos del estudio desde la base de datos.
        
        Args:
            study_id: El ID del estudio.
        
        Returns:
            list: Una lista de tuplas con los datos de las personas y sus mediciones.
        """
        query = """
        SELECT
            p.id AS person_id,
            p.name AS person_name,
            d.name AS dimension_name,
            m.value AS measurement_value
        FROM
            app1_person p
        JOIN
            app1_measurement m ON p.id = m.person_id
        JOIN
            app1_dimension d ON m.dimension_id = d.id
        JOIN
            app1_studyDimension sd ON d.id = sd.id_dimension_id
        WHERE
            m.study_id = %s
        ORDER BY
            p.id, d.name;
        """
        
        with connection.cursor() as cursor:
            cursor.execute(query, [study_id])
            results = cursor.fetchall()
        
        return results

    def get_study_data_json(self, study_id):
        """
        Convierte los datos del estudio en un formato JSON.
        
        Args:
            study_id: El ID del estudio.
        
        Returns:
            dict: Un diccionario con los datos del estudio, incluyendo las dimensiones y las personas.
        """
        
         # Obtener todas las dimensiones asociadas al estudio
        dimensions = self.get_study_dimensions(study_id)
       
        # Obtener los datos de las personas y sus mediciones
        results = self.get_study_data(study_id)
        
        # Crear un diccionario para agrupar los datos por persona
        data = {}
        for row in results:
            person_id, person_name, dimension_name, measurement_value = row
            
            if person_id not in data:
                data[person_id] = {
                    "id": person_id,
                    "name": person_name,
                    # "dimensions": {}
                    "dimensions": {dimension: None for dimension in dimensions}  # Inicializar todas las dimensiones
                }
            
            data[person_id]["dimensions"][dimension_name] = measurement_value
        
        # Convertir el diccionario a una lista
        # return list(data.values())
        return {
            "dimensions": dimensions,  # Lista de todas las dimensiones
            "persons": list(data.values())  # Lista de personas con sus mediciones
        }