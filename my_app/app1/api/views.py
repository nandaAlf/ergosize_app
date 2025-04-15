from datetime import date
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from app1.models import Person, Measurement, Study, Dimension, StudyDimension
from app1.api.serializer import  PersonSerializer, MeasurementSerializer, StudyDimensionSerializer, StudySerializer, DimensionSerializer
from django.http import JsonResponse
from django.views import View
from django.db import connection
import numpy as np

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

        # Verificar si existen mediciones para el estudio y persona especificados
        if not Measurement.objects.filter(study_id=study_id, person_id=person_id).exists():
            return Response(
                {"error": "No se encontraron mediciones para el estudio y persona especificados"},
                status=status.HTTP_404_NOT_FOUND,
            )
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

# class AnthropometricTableViewSet(viewsets.ModelViewSet):
    # queryset = AnthropometricTable.objects.all()
    # serializer_class = AnthropometricTableSerializer
    
    # def create(self, request, *args, **kwargs):
    #     study_id = request.data.get("study")
    #     statistics_data = request.data.get("statistics", [])

    #     try:
    #         study = Study.objects.get(id=study_id)
    #         table = AnthropometricTable.objects.create(study=study)

    #         for stat in statistics_data:
    #             measurement_type = Dimension.objects.get(id=stat["measurement_type"])
    #             AnthropometricStatistic.objects.create(
    #                 table=table,
    #                 measurement_type=measurement_type,
    #                 mean=stat["mean"],
    #                 sd=stat["sd"],
    #                 percentile_5=stat.get("percentile_5"),
    #                 percentile_10=stat.get("percentile_10"),
    #                 percentile_25=stat.get("percentile_25"),
    #                 percentile_50=stat.get("percentile_50"),
    #                 percentile_75=stat.get("percentile_75"),
    #                 percentile_90=stat.get("percentile_90"),
    #                 percentile_95=stat.get("percentile_95")
    #             )

    #         return Response({"message": "Tabla creada correctamente"}, status=status.HTTP_201_CREATED)
    #     except Study.DoesNotExist:
    #         return Response({"error": "El estudio no existe"}, status=status.HTTP_400_BAD_REQUEST)
    #     except Dimension.DoesNotExist:
    #         return Response({"error": "El tipo de medición no existe"}, status=status.HTTP_400_BAD_REQUEST)

# class AnthropometricStatisticViewSet(viewsets.ModelViewSet):
#     queryset = AnthropometricStatistic.objects.all()
#     serializer_class = AnthropometricStatisticSerializer


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
        # dimensions = StudyDimension.objects.filter(id_study_id=study_id).values_list('id_dimension__name', flat=True)
        # return list(dimensions)
        dimensions = StudyDimension.objects.filter(id_study_id=study_id).values_list('id_dimension__name', 'id_dimension__id','id_dimension__initial')
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
    
        # Obtener todas las dimensiones asociadas al estudio (nombre e ID)
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
                    "dimensions": {dimension[0]: None for dimension in dimensions}  # Inicializar todas las dimensiones con valor None
                }
            
            # Actualizar el valor de la medición para la dimensión correspondiente
            data[person_id]["dimensions"][dimension_name] = measurement_value
        # Convertir el diccionario a un formato JSON
        return {
            "dimensions": [{"name": dimension[0], "id": dimension[1],"initial":dimension[2]} for dimension in dimensions],  # Lista de todas las dimensiones con nombre e ID
            "persons": list(data.values())  # Lista de personas con sus mediciones
        }
        


class Perceptil(View):

    def calculate_percentiles_for_study(self, study_id, gender=None, age_min=None, age_max=None, dimensions_filter=None, percentiles_list=None):
        # Obtener el estudio
        study = Study.objects.get(id=study_id)
    
        # Si no se indica percentiles, se usan los siguientes valores por defecto.
        if percentiles_list is None:
            percentiles_list = [5, 10, 25, 50, 75, 90, 95]


        # Crear o obtener la tabla antropométrica asociada al estudio
        # table, created = AnthropometricTable.objects.get_or_create(study=study)
        
        # Obtener todas las dimensiones asociadas al estudio
        # Se filtran por 'dimensions_filter' si éste es proporcionado (se espera una lista de nombres).
        dimensions_qs = Dimension.objects.filter(dimension_study__id_study=study)
        # print(dimensions_qs)
        if dimensions_filter:
            dimensions_qs = dimensions_qs.filter(id__in=dimensions_filter)
        print(dimensions_filter)
        # dimensions = Dimension.objects.filter(dimension_study__id_study=study)
        # Obtener todas las dimensiones asociadas al estudio

    
        # print(dimensions.id_dimension or "n")
        results = []  # Lista para almacenar los resultados
        
        for dimension in dimensions_qs:
            # Obtener todas las mediciones para esta dimensión en el estudio
            measurements = Measurement.objects.filter(study=study, dimension=dimension)
            filtered_values = []
            # Procesar cada medición para aplicar filtros adicionales sobre la persona asociada
            for measurement in measurements:
                person = measurement.person
                # print(person or "kkk")

                # Filtrar por género si se indicó
                if gender and person.gender != gender:
                    continue

                # Filtrar por rango de edad (calculado a partir de date_of_birth)
                if (age_min or age_max) and person.date_of_birth  and measurement.date:
                    measurement_date = measurement.date.date() 
                    birth_date = person.date_of_birth
                
                    age = measurement_date.year - birth_date.year - (
                        (measurement_date.month, measurement_date.day) < (birth_date.month, birth_date.day)
                    )
                    if age_min and age < age_min:
                        continue
                    if age_max and age > age_max:
                        continue
            
                filtered_values.append(measurement.value)
             
            if filtered_values:
                mean = float(np.mean(filtered_values))
                sd = float(np.std(filtered_values))
                # Calcular los percentiles según la lista especificada
                percentiles = np.percentile(filtered_values, percentiles_list)
                # Convertir el resultado a un diccionario con claves como strings
                percentiles_dict = {str(p): float(val) for p, val in zip(percentiles_list, percentiles)}

                results.append({
                    'dimension': dimension.name,
                    'mean': mean,
                    'sd': sd,
                    'percentiles': percentiles_dict
                })
            
        
            
            # values = measurements.values_list('value', flat=True)
            
            # if values:  # Solo calcular si hay mediciones
            #     # Calcular estadísticas
            #     mean = np.mean(values)
            #     sd = np.std(values)
            #     percentiles = np.percentile(values, [5, 10, 25, 50, 75, 90, 95])
                
                # Crear o actualizar la estadística en AnthropometricStatistic
                # stat, created = AnthropometricStatistic.objects.get_or_create(
                    # table=table,
                #     dimension=dimension,
                #     defaults={
                #         'mean': mean,
                #         'sd': sd,
                #         'percentile_5': percentiles[0],
                #         'percentile_10': percentiles[1],
                #         'percentile_25': percentiles[2],
                #         'percentile_50': percentiles[3],
                #         'percentile_75': percentiles[4],
                #         'percentile_90': percentiles[5],
                #         'percentile_95': percentiles[6],
                #     }
                # )
                
                # if not created:
                    # Si ya existe, actualizar los valores
                    # stat.mean = mean
                    # stat.sd = sd
                    # stat.percentile_5 = percentiles[0]
                    # stat.percentile_10 = percentiles[1]
                    # stat.percentile_25 = percentiles[2]
                    # stat.percentile_50 = percentiles[3]
                    # stat.percentile_75 = percentiles[4]
                    # stat.percentile_90 = percentiles[5]
                    # stat.percentile_95 = percentiles[6]
                    # stat.save()
                
                # Agregar los resultados a la lista
                # results.append({
                #     'dimension': dimension.name,
                #     'mean': mean,
                #     'sd': sd,
                #     'percentiles': {
                #         '5': percentiles[0],
                #         '10': percentiles[1],
                #         '25': percentiles[2],
                #         '50': percentiles[3],
                #         '75': percentiles[4],
                #         '90': percentiles[5],
                #         '95': percentiles[6],
                #     }
                # })
        
        return results

    def get(self, request,study_id):
        # Obtener el ID del estudio desde los parámetros de la solicitud GET
        # study_id = request.GET.get('study_id')
        if not study_id:
            return JsonResponse(
                {"status": "error", "message": "El parámetro 'study_id' es requerido."}, 
                status=400)
        
        # Extracción de parámetros vía GET:
        #   gender: "M" o "F"
        gender = request.GET.get('gender', None)
        if gender and gender not in ['M', 'F']:
            return JsonResponse({"status": "error", "message": "Valor de género inválido. Use 'M' o 'F'."}, status=400)

        #   age_min y age_max: se convierten a entero si están proporcionados
        age_min = request.GET.get('age_min', None)
        age_max = request.GET.get('age_max', None)
        try:
            age_min = int(age_min) if age_min else None
            age_max = int(age_max) if age_max else None
        except ValueError:
            return JsonResponse({"status": "error", "message": "age_min y age_max deben ser números enteros."}, status=400)

        #   dimensions: se espera una lista separada por comas (por ejemplo: "Altura,Peso")
        dimensions_filter = request.GET.get('dimensions', None)
        if dimensions_filter:
            dimensions_filter = [d.strip() for d in dimensions_filter.split(',')]

        #   percentiles: lista separada por comas (por ejemplo: "5,95"). Se convierten a float.
        percentiles_param = request.GET.get('percentiles', None)
        if percentiles_param:
            try:
                percentiles_list = [float(p.strip()) for p in percentiles_param.split(',')]
            except ValueError:
                return JsonResponse({"status": "error", "message": "El parámetro 'percentiles' debe contener números separados por comas."}, status=400)
        else:
            percentiles_list = None

  
        
        try:
            # Calcular los percentiles y obtener los resultados
            results = self.calculate_percentiles_for_study(study_id, gender=gender,
                age_min=age_min,
                age_max=age_max,
                dimensions_filter=dimensions_filter,
                percentiles_list=percentiles_list
                )
            
            # Devolver los resultados en formato JSON
            return JsonResponse({
                "status": "success",
                "study_id": study_id,
                "results": results
            })
        except Study.DoesNotExist:
            return JsonResponse({"status": "error", "message": f"El estudio con ID {study_id} no existe."}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
