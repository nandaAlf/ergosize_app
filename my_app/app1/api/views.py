from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from app1.models import Person, Measurement, Study, Dimension, StudyDimension
from app1.api.serializer import  PersonSerializer, MeasurementSerializer, StudyDimensionSerializer, StudySerializer, DimensionSerializer, StudyDetailWithPersonsSerializer
from django.http import Http404, HttpResponse, JsonResponse
from django.views import View
from django.db import connection
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.cell.cell import MergedCell
from django.utils import timezone
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from openpyxl import load_workbook
from django.views.decorators.csrf import csrf_exempt
import io
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from accounts.api.permissions import HasRole, IsAdmin, IsAdminOrInvestigator, IsCreatorOrAdmin, IsInvestigator, IsInvestigatorOfPerson
# IsAdmin, IsCreator, IsGeneralUser, IsInvestigator
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied


class PersonViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
   
   
    def get_permissions(self):
        # list & retrieve
        if self.action in ['list', 'retrieve','update','partial_update','destroy']:
        #     # admin ve todo, investigador también pasa permiso pero
        #     # el queryset limita, y detail pasa a has_object_permission
            return [IsAuthenticated(),  IsInvestigatorOfPerson()]
        # create
        if self.action == 'create':
            return [IsAuthenticated(), IsAdminOrInvestigator()]
        # update / partial_update / destroy
        # if self.action in ['update','partial_update','destroy']:
        #     return [IsAuthenticated(), IsInvestigatorOfPerson()]
        # fallback: bloqueo
        return [IsAuthenticated(),IsInvestigatorOfPerson()]

    def get_queryset(self):
        user = self.request.user
        qs = Person.objects.all()
        if user.role == 'admin':
            return qs
        if user.role == 'investigador':
            # solo personas con mediciones en estudios supervisados
            return qs.filter(
                measurements__study__supervisor=user
            ).distinct()
        # usuarios generales no tienen acceso
        return Person.objects.none()

    def perform_create(self, serializer):
    
        user = self.request.user
        measurements = self.request.data.get('measurements', [])
        roles=['investigador','admin']
        if user.role in roles:
            if not measurements:
                raise PermissionDenied("Debes proporcionar al menos una medición.")

            # Extraer los IDs de estudios desde las mediciones
            study_ids = []
            for m in measurements:
                study_id = m.get('study_id')
                if not study_id:
                    raise PermissionDenied("Cada medición debe incluir un study_id.")
                study_ids.append(study_id)

            # Verificar que el usuario supervisa todos los estudios
            unauthorized = Study.objects.filter(
                id__in=study_ids
            ).exclude(supervisor=user)

            if unauthorized.exists():
                raise PermissionDenied("No puedes crear personas con mediciones de estudios que no supervisas.")

        serializer.save()
    # def perform_create(self, serializer):
    #     user = self.request.user
    #     measurements = self.request.data.get('measurements', [])
    #     print("Mes",measurements)
        
    #     if user.role == 'investigador':
    #         print("ES inv")
    #         # Extraer todos los IDs de estudio del payload
    #         study_ids = [m.get('study_id') for m in measurements]
    #         print("Study id",study_ids)
    #         # from studies.models import Study
    #         # Detectar estudios que NO supervisa
    #         unauthorized = Study.objects.filter(
    #             id__in=study_ids
    #         ).exclude(supervisor=user)
    #         if unauthorized.exists():
    #             raise PermissionDenied(
    #                 "No puedes crear personas con mediciones de estudios que no supervisas."
    #             )
    #     # Si es admin, o investigador validado, guardamos todo
    #     serializer.save()
   
   
    # def get_permissions(self):
    #     base = [IsAuthenticated()]
    #     if self.action in ['list', 'retrieve']:
    #         # Admin ve todo; investigador ve solo sus vinculados (que se filtran en get_queryset)
    #         return [IsAdmin(), IsInvestigator()]
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         # Solo admin o investigador pueden gestionar personas/mediciones
    #         return [IsAdmin(), IsInvestigator()]
    #     return [IsAuthenticated()]

    # def get_queryset(self):
    #     user = self.request.user
    #     qs = Person.objects.all()
    #     if user.role == 'admin':
    #         return qs
    #     # Investigador: obtener solo persons con measurements en estudios supervisados por user
    #     # Suponiendo Measurement tiene FK study with supervisor
    #     return qs.filter(
    #         measurements__study__supervisor=user
    #     ).distinct()

    # def perform_create(self, serializer):
    #     """
    #     Verifica que, para investigadores, todas las mediciones
    #     referencian estudios que supervisa.
    #     """
    #     user = self.request.user
    #     data = self.request.data.get('measurements', [])
    #     if user.role == 'investigador':
    #         # extraer todos los study IDs del payload
    #         study_ids = {m.get('study') for m in data}
    #         # comprobar supervisión
    #         not_owned = Study.objects.filter(id__in=study_ids).exclude(supervisor=user)
    #         if not_owned.exists():
    #             raise PermissionDenied("No puedes añadir personas para estudios que no supervisas.")
    #     serializer.save()

    # def perform_update(self, serializer):
    #     """
    #     Igual que create: verifica que el investigador solo modifique
    #     mediciones en sus propios estudios.
    #     """
    #     user = self.request.user
    #     data = self.request.data.get('measurements', [])
    #     if user.role == 'investigador':
    #         study_ids = {m.get('study') for m in data}
           
    #         not_owned = Study.objects.filter(id__in=study_ids).exclude(supervisor=user)
    #         if not_owned.exists():
    #             raise PermissionDenied("No puedes modificar personas con mediciones de estudios que no supervisas.")
    #     serializer.save() 
   
class DimensionViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = Dimension.objects.all()
    serializer_class = DimensionSerializer

class MeasurementViewSet(viewsets.ModelViewSet):
    queryset = Measurement.objects.all()
    authentication_classes = [JWTAuthentication]
    serializer_class = MeasurementSerializer
    # permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden eliminar

    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         return [IsCreatorOrAdmin()]
    #     return [IsAuthenticated()]
    
    def get_permissions(self):
        # Para destruir mediciones en bloque, comprobamos permiso sobre el estudio
        if self.action == 'destroy':
            return [IsAuthenticated(), IsCreatorOrAdmin()]
        # Resto de acciones: cualquier usuario autenticado
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/measurements/study_id/?&person_id=Y
        Borra todas las mediciones de esa persona en ese estudio,
        y si la persona no tiene más mediciones en otros estudios,
        elimina también el registro de Person.
        """
        # study_id  = request.query_params.get('study_id')
        study_id=self.kwargs.get('pk')
        person_id = request.query_params.get('person_id')

        if not study_id or not person_id:
            return Response(
                {"error": "Se requieren 'study_id' y 'person_id' como query params."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar permiso: simulamos un objeto Study para IsCreatorOrAdmin
        # from studies.models import Study
        try:
            study = Study.objects.get(id=study_id)
        except Study.DoesNotExist:
            return Response(
                {"error": "Estudio no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Chequear permiso de objeto
        self.check_object_permissions(request, study)

        # Borrar mediciones en ese estudio
        deleted_count, _ = Measurement.objects.filter(
            study_id=study_id,
            person_id=person_id
        ).delete()

        if deleted_count == 0:
            return Response(
                {"error": "No se encontraron mediciones para ese estudio y persona."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Si la persona ya no tiene mediciones en ningún estudio, borrarla
        remaining = Measurement.objects.filter(person_id=person_id).exists()
        if not remaining:
            try:
                person = Person.objects.get(id=person_id)
                person.delete()
            except Person.DoesNotExist:
                pass  # ya puede no existir

        return Response(
            {"message": "Mediciones eliminadas correctamente."},
            status=status.HTTP_204_NO_CONTENT
        )
    
    # def destroy(self, request, *args, **kwargs):
    #     # Obtener el study_id y person_id de la solicitud
    #     study_id=self.kwargs.get('pk')
    #     person_id = request.data.get('person_id')

    #     if not study_id or not person_id:
    #         return Response(
    #             {"error": "Se requieren study_id y person_id"},
    #             status=status.HTTP_400_BAD_REQUEST,
    #         )

    #     # # Verificar permisos adicionales si es necesario
    #     # if not request.user.has_perm('app.delete_measurement'):
    #     #     return Response(
    #     #         {"error": "No tienes permisos para eliminar estas mediciones"},
    #     #         status=status.HTTP_403_FORBIDDEN,
    #     #     )

    #     # Verificar si existen mediciones para el estudio y persona especificados
    #     if not Measurement.objects.filter(study_id=study_id, person_id=person_id).exists():
    #         return Response(
    #             {"error": "No se encontraron mediciones para el estudio y persona especificados"},
    #             status=status.HTTP_404_NOT_FOUND,
    #         )
    #     # Eliminar todos los registros de Measurement que coincidan
    #     Measurement.objects.filter(study_id=study_id, person_id=person_id).delete()

    #     # Puedes usar señales (signals) de Django para ejecutar acciones adicionales antes o después de la eliminación.

    #     return Response(
    #         {"message": "Mediciones eliminadas correctamente"},
    #         status=status.HTTP_204_NO_CONTENT,
    #     )
class StudyViewSet(viewsets.ModelViewSet):
    # queryset = Study.objects.all()
    # serializer_class = StudySerializer
    authentication_classes = [JWTAuthentication]
    queryset = Study.objects.all()
    serializer_class = StudySerializer
    permission_classes = [IsAuthenticated]
    


    def get_queryset(self):   
        qs = super().get_queryset()
        # Si se pasa ?mine=true, filtra por supervisor
        if self.request.query_params.get('mine') == 'true':
            return qs.filter(supervisor=self.request.user)
        return qs
    
    def get_permissions(self):
        if   self.action == 'create':
            # Solo admin e investigadores pueden crear
            return [IsAdminOrInvestigator()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Solo el creador (supervisor) o admin pueden modificar o eliminar
            return [IsCreatorOrAdmin()]
        elif self.action == 'members':
            # Solo el creador o admin pueden ver las personas y sus mediciones
            return [IsCreatorOrAdmin()]
        # Listar y recuperar: cualquier usuario autenticado
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['get'], url_path='members')
    def members(self, request, pk=None):
        """
        GET /api/studies/{pk}/members/
        devuelve el estudio con la lista de personas y sus valores de medición.
        """
        study = self.get_object()
        serializer = StudyDetailWithPersonsSerializer(study, context={'request': request})
        return Response(serializer.data)
    
    # def get_permissions(self):
    #     if self.action in ['create']:
    #         # sólo admin e investigadores
    #         permission_classes = [IsAdmin|IsInvestigator]
    #     elif self.action in ['delete']:
    #         permission_classes = [IsAdmin|IsCreator]
    #     elif self.action in['update', 'partial_update'] :
    #         permission_classes=[IsCreator]
    #     else:
    #         # listar y retrieve permitidos a todos autenticados
    #         permission_classes = [IsAdmin|IsInvestigator|IsGeneralUser]
    #     return [perm() for perm in permission_classes]
class StudyDimensionViewSet(viewsets.ModelViewSet):
    queryset = StudyDimension.objects.all()
    serializer_class = StudyDimensionSerializer
    
    # def get_permissions(self):
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         # sólo admin e investigadores
    #         permission_classes = [IsAdmin|IsInvestigator]
    #     else:
    #         # listar y retrieve permitidos a todos autenticados
    #         permission_classes = [IsAdmin|IsInvestigator|IsGeneralUser]
    #     return [perm() for perm in permission_classes]

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


# class StudyDataView(View):
#     """
#     Vista para obtener los datos de un estudio específico, incluyendo las personas
#     y sus mediciones en las dimensiones asociadas.
#     """
#     def get(self, request, study_id):
#         """
#         Maneja las solicitudes GET para obtener los datos del estudio.
        
#         Args:
#             request: La solicitud HTTP.
#             study_id: El ID del estudio.
        
#         Returns:
#             JsonResponse: Un JSON con los datos del estudio.
#         """
#         # Verificar que el estudio existe
#         study = get_object_or_404(Study, id=study_id)

#         # Obtener los datos del estudio
#         try:
#             data = self.get_study_data_json(study_id)
#             return JsonResponse(data, safe=False, status=200)
#         except Exception as e:
#             # Manejar errores en la consulta o procesamiento
#             return JsonResponse({"error": str(e)}, status=500)
    
#     def get_study_dimensions(self, study_id):
#         """
#         Obtiene todas las dimensiones asociadas al estudio desde la tabla StudyDimension.
        
#         Args:
#             study_id: El ID del estudio.
        
#         Returns:
#             list: Una lista de nombres de dimensiones.
#         """
#         # dimensions = StudyDimension.objects.filter(id_study_id=study_id).values_list('id_dimension__name', flat=True)
#         # return list(dimensions)
#         dimensions = StudyDimension.objects.filter(id_study_id=study_id).values_list('id_dimension__name', 'id_dimension__id','id_dimension__initial')
#         return list(dimensions)
    
#     def get_study_data(self, study_id):
#         """
#         Obtiene los datos del estudio desde la base de datos.
        
#         Args:
#             study_id: El ID del estudio.
        
#         Returns:
#             list: Una lista de tuplas con los datos de las personas y sus mediciones.
#         """
#         query = """
#         SELECT
#             p.id AS person_id,
#             p.name AS person_name,
#             d.name AS dimension_name,
#             m.value AS measurement_value
#         FROM
#             app1_person p
#         JOIN
#             app1_measurement m ON p.id = m.person_id
#         JOIN
#             app1_dimension d ON m.dimension_id = d.id
#         JOIN
#             app1_studyDimension sd ON d.id = sd.id_dimension_id
#         WHERE
#             m.study_id = %s
#         ORDER BY
#             p.id, d.name;
#         """
        
#         with connection.cursor() as cursor:
#             cursor.execute(query, [study_id])
#             results = cursor.fetchall()
        
#         return results

#     def get_study_data_json(self, study_id):
#         """
#         Convierte los datos del estudio en un formato JSON.
        
#         Args:
#             study_id: El ID del estudio.
        
#         Returns:
#             dict: Un diccionario con los datos del estudio, incluyendo las dimensiones y las personas.
#         """
    
#         # Obtener todas las dimensiones asociadas al estudio (nombre e ID)
#         dimensions = self.get_study_dimensions(study_id)
        
#         # Obtener los datos de las personas y sus mediciones
#         results = self.get_study_data(study_id)
        
#         # Crear un diccionario para agrupar los datos por persona
#         data = {}
#         for row in results:
#             person_id, person_name, dimension_name, measurement_value = row
            
#             if person_id not in data:
#                 data[person_id] = {
#                     "id": person_id,
#                     "name": person_name,
#                     "dimensions": {dimension[0]: None for dimension in dimensions}  # Inicializar todas las dimensiones con valor None
#                 }
            
#             # Actualizar el valor de la medición para la dimensión correspondiente
#             data[person_id]["dimensions"][dimension_name] = measurement_value
#         # Convertir el diccionario a un formato JSON
#         return {
#             "dimensions": [{"name": dimension[0], "id": dimension[1],"initial":dimension[2]} for dimension in dimensions],  # Lista de todas las dimensiones con nombre e ID
#             "persons": list(data.values())  # Lista de personas con sus mediciones
#         }
        
#MOVER A UTILS
# def calculate_percentiles_for_study(study_id, gender=None, age_min=None, age_max=None, dimensions_filter=None, percentiles_list=None):
#         # Obtener el estudio
#         study = Study.objects.get(id=study_id)
    
#         # Si no se indica percentiles, se usan los siguientes valores por defecto.
#         if percentiles_list is None:
#             percentiles_list = [5, 10, 25, 50, 75, 90, 95]

#         dimensions_qs = Dimension.objects.filter(dimension_study__id_study=study)
#         # print(dimensions_qs)
#         if dimensions_filter:
#             dimensions_qs = dimensions_qs.filter(id__in=dimensions_filter)
#         print(dimensions_filter)
      
#         results = []  # Lista para almacenar los resultados
        
#         for dimension in dimensions_qs:
#             # Obtener todas las mediciones para esta dimensión en el estudio
#             measurements = Measurement.objects.filter(study=study, dimension=dimension)
#             filtered_values = []
#             # Procesar cada medición para aplicar filtros adicionales sobre la persona asociada
#             for measurement in measurements:
#                 person = measurement.person
#                 # print(person or "kkk")

#                 # Filtrar por género si se indicó
#                 if gender and person.gender != gender:
#                     continue

#                 # Filtrar por rango de edad (calculado a partir de date_of_birth)
#                 if (age_min or age_max) and person.date_of_birth  and measurement.date:
#                     measurement_date = measurement.date.date() 
#                     birth_date = person.date_of_birth
                
#                     age = measurement_date.year - birth_date.year - (
#                         (measurement_date.month, measurement_date.day) < (birth_date.month, birth_date.day)
#                     )
#                     if age_min and age < age_min:
#                         continue
#                     if age_max and age > age_max:
#                         continue
            
#                 filtered_values.append(measurement.value)
             
#             if filtered_values:
#                 mean = float(np.mean(filtered_values))
#                 sd = float(np.std(filtered_values))
#                 # Calcular los percentiles según la lista especificada
#                 percentiles = np.percentile(filtered_values, percentiles_list)
#                 # Convertir el resultado a un diccionario con claves como strings
#                 percentiles_dict = {str(p): float(val) for p, val in zip(percentiles_list, percentiles)}

#                 results.append({
#                     'dimension': dimension.name,
#                     'dimension_id': dimension.id,	
#                     'mean': mean,
#                     'sd': sd,
#                     'percentiles': percentiles_dict
#                 })
        
#         return results

def calculate_percentiles_for_study(
    study_id: int,
    gender: str = None,                  # 'M', 'F' o 'mixto'
    age_ranges: list[tuple[int,int]] = None,
    dimensions_filter: list[int] = None,
    percentiles_list: list[float] = None
) -> list:
    """Calcula media, desviación y percentiles por dimensión,
       por género y por cada rango de edad."""
    # Obtener el estudio o lanzar 404
    try:
        study = Study.objects.get(id=study_id)
    except Study.DoesNotExist:
        raise Http404(f"Study with id {study_id} not found")

    # Percentiles por defecto
    percentiles = percentiles_list or [5, 10, 25, 50, 75, 90, 95]

    # Filtrar dimensiones
    dims_qs = Dimension.objects.filter(dimension_study__id_study=study)
    if dimensions_filter:
        dims_qs = dims_qs.filter(id__in=dimensions_filter)

    # Determinar géneros a procesar
    if gender == 'mixto':
        genders_to_process = ['M', 'F']
    elif gender in ('M', 'F'):
        genders_to_process = [gender]
    else:
        genders_to_process = [None]  # todos juntos si no especifica

    results = []

    for dim in dims_qs:
        entry = {
            'dimension': dim.name,
            'dimension_id': dim.id,
            'by_gender': {}
        }

        for g in genders_to_process:
            # Preparamos buckets de edad
            buckets = age_ranges or [(None, None)]
            age_buckets_stats = {}

            for amin, amax in buckets:
                vals = _collect_measurements(
                    study=study,
                    dimension=dim,
                    gender_filter=g,
                    age_min=amin,
                    age_max=amax
                )
                if not vals:
                    continue
                stats = _compute_stats(vals, percentiles)
                key = f"{amin}-{amax}" if amin is not None else "all"
                age_buckets_stats[key] = stats

            if age_buckets_stats:
                age_key = g or 'all'
                entry['by_gender'][age_key] = age_buckets_stats

        if entry['by_gender']:
            results.append(entry)

    return results

def _collect_measurements(study, dimension, gender_filter, age_min, age_max):
    """
    Devuelve lista de valores filtrados según:
      - género (M/F/None),
      - rango de edad [age_min, age_max] (si se pasan),
      - pertenecen al estudio y dimensión dados.
    """
    qs = Measurement.objects.filter(
        study=study,
        dimension=dimension
    ).select_related('person')

    vals = []
    for m in qs:
        p = m.person
        # Filtrar por género
        if gender_filter and p.gender != gender_filter:
            continue

        # Filtrar por rango de edad
        if (age_min is not None or age_max is not None) and p.date_of_birth and m.date:
            md = m.date.date()
            bd = p.date_of_birth
            age = md.year - bd.year - ((md.month, md.day) < (bd.month, bd.day))
            if age_min is not None and age < age_min:
                continue
            if age_max is not None and age > age_max:
                continue

        vals.append(m.value)

    return vals

def _compute_stats(values, percentiles_list):
    """
    Calcula media, desviación estándar y percentiles de la lista de valores.
    """
    arr = np.array(values, dtype=float)
    mean = float(arr.mean())
    sd = float(arr.std(ddof=0))
    perc_vals = np.percentile(arr, percentiles_list)
    perc_dict = {str(int(p)): float(v) for p, v in zip(percentiles_list, perc_vals)}

    return {
        'mean': mean,
        'sd': sd,
        'percentiles': perc_dict
    }


class Perceptil(View):
    """Vista para obtener percentiles de un estudio."""
    def get(self, request, study_id):
        if not study_id:
            return JsonResponse(
                {"status": "error", "message": "El parámetro 'study_id' es requerido."},
                status=400
            )

        # Parámetros GET
        gender = request.GET.get('gender')           # 'M', 'F' o 'mixto'
        age_ranges_param = request.GET.get('age_ranges')   # e.g. "10-12,12-14,14-16"
        # print("aaa",age_ranges)
        dimensions = request.GET.get('dimensions')   # e.g. "1,2,3"
        percentiles_param = request.GET.get('percentiles') # e.g. "5,95"

        # Validaciones básicas
        if gender and gender not in ('M', 'F', 'mixto'):
            return JsonResponse({'status':'error','message':'Valor gender inválido.'}, status=400)

        # Parsear age_ranges
        try:
            age_ranges = [
                tuple(map(int, r.split('-')))
                for r in age_ranges_param.split(',')
            ] if age_ranges_param else None
        except Exception:
            return JsonResponse(
                {'status':'error','message':"'age_ranges' debe ser lista de rangos 'min-max'."},
                status=400
            )

        # Parsear dimensions
        try:
            dims_filter = [int(d) for d in dimensions.split(',')] if dimensions else None
        except ValueError:
            return JsonResponse(
                {'status':'error','message':"'dimensions' debe ser lista de IDs enteros."},
                status=400
            )

        # Parsear percentiles
        try:
            perc_list = [float(p) for p in percentiles_param.split(',')] if percentiles_param else None
        except ValueError:
            return JsonResponse(
                {'status': 'error', 'message': "'percentiles' debe ser lista de números."},
                status=400
            )

        # Llamada a la lógica de cálculo
        try:
            results = calculate_percentiles_for_study(
                study_id=study_id,
                gender=gender,
                age_ranges=age_ranges,
                dimensions_filter=dims_filter,
                percentiles_list=perc_list
            )
            return JsonResponse({'status': 'success', 'study_id': study_id, 'results': results})
        except Http404 as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



def export_excel_percentiles(request, study_id):
    try:
        study = Study.objects.get(id=study_id)
        name_study = request.GET.get('name', f"Estudio {study_id}")
        gender = request.GET.get('gender')
        age_min = int(request.GET.get('age_min')) if request.GET.get('age_min') else None
        age_max = int(request.GET.get('age_max')) if request.GET.get('age_max') else None
        dimensions_filter = request.GET.get('dimensions')
        if dimensions_filter:
            dimensions_filter = [int(x) for x in dimensions_filter.split(',')]

        percentiles = request.GET.get('percentiles')
        if percentiles:
            percentiles_list = [float(p) for p in percentiles.split(',')]
        else:
            percentiles_list = [5, 10, 25, 50, 75, 90, 95]

        results = calculate_percentiles_for_study(
            study_id,
            gender=gender,
            age_min=age_min,
            age_max=age_max,
            dimensions_filter=dimensions_filter,
            percentiles_list=percentiles_list
        )

        wb = Workbook()
        ws = wb.active
        ws.title = "Percentiles"

        # --- Estilos
        header_font = Font(bold=True)
        title_font = Font(size=14, bold=True)
        center_align = Alignment(horizontal="center")
        left_align = Alignment(horizontal="left")
        fill_gray = PatternFill("solid", fgColor="DDDDDD")
        border_thin = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )

        total_columnas = 3 + len(percentiles_list)
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_columnas)
        title_cell = ws.cell(row=1, column=1)
        title_cell.value = f"Tabla antropométrica: {name_study}"
        title_cell.font = title_font
        title_cell.alignment = center_align
        title_cell.fill = fill_gray  # Azul claro


        ws.append(["Fecha inicio:", study.start_date, "Fecha fin:",study.end_date])
        ws.append(["Muestra:", study.size,"Genero:", gender if gender else "Mixto"])
        ws.append(["Edad mínima:", age_min if age_min is not None else "—","Edad máxima:", age_max if age_max is not None else "—"])
        ws.append(["Descripción:"])
        # Escribir la descripción en la fila siguiente, fusionando columnas desde B en adelante
        desc_row = ws.max_row 
        ws.merge_cells(start_row=desc_row, start_column=2, end_row=desc_row, end_column=total_columnas)
        desc_cell = ws.cell(row=desc_row, column=2)
        desc_cell.value = study.description
        desc_cell.alignment = Alignment(wrap_text=True, vertical="top")  # Ajuste de texto
        ws.append([]) 

        # Aplicar formato a metadatos
        for row in ws.iter_rows(min_row=2, max_row=6):
            for cell in row:
                cell.alignment = left_align
                cell.font = Font(bold=isinstance(cell.value, str) and cell.value.endswith(':'))

        # --- Encabezados
        headers = ["Dimensión", "Media", "SD"] + [f"P{p}" for p in percentiles_list]
        ws.append(headers)
        for i, header in enumerate(headers, start=1):
            cell = ws.cell(row=ws.max_row, column=i)
            cell.font = header_font
            cell.alignment = center_align
            cell.fill = fill_gray
            cell.border = border_thin

        # --- Datos
        for res in results:
            row = [
                res["dimension"],
                res["mean"],
                res["sd"],
            ] + [res["percentiles"].get(str(p), '') for p in percentiles_list]
            ws.append(row)
            for i, val in enumerate(row, start=1):
                cell = ws.cell(row=ws.max_row, column=i)
                cell.alignment = center_align
                cell.border = border_thin

        # --- Ajustar ancho de columnas automáticamente
        for column_cells in ws.columns:
            for cell in column_cells:
                if not isinstance(cell, MergedCell):
                    col_letter = get_column_letter(cell.column)
                    break
            else:
                continue
            max_length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
            ws.column_dimensions[col_letter].width = max_length + 2

        # --- Respuesta
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="percentiles_study_{study_id}.xlsx"'
        wb.save(response)
        return response
    except Study.DoesNotExist:
          return HttpResponse("Estudio no encontrado.", status=404)
     
@csrf_exempt
def preview_excel_percentiles(request):
    print(request.method)
    print(request.FILES)
    print("Archivo recibido:", request.FILES.get("archivo"))
    if request.method == "POST" and request.FILES.get("archivo"):
        archivo = request.FILES["archivo"]
        wb = load_workbook(archivo)
        ws = wb["Percentiles"]

        data = []
        headers = []
        for i, row in enumerate(ws.iter_rows(min_row=8, values_only=True), start=8):
            if i == 8:
                headers = row
                continue
            if not any(row):
                continue

            item = {
                "dimension": row[0],
                "mean": row[1],
                "sd": row[2],
                "percentiles": {}
            }
            for j, value in enumerate(row[3:], start=3):
                if headers[j]:
                    key = str(headers[j]).replace("P", "")
                    item["percentiles"][key] = value
            data.append(item)

        return JsonResponse(data, safe=False)

    return JsonResponse({"error": "Archivo no proporcionado o método incorrecto"}, status=400)

def export_pdf_percentiles(request, study_id):
    try:
        # Obtener parámetros y estudio de igual forma que en Excel
        study = Study.objects.get(id=study_id)
        name_study = request.GET.get('name', f"Estudio {study_id}")
        gender = request.GET.get('gender')
        age_min = request.GET.get('age_min')
        age_max = request.GET.get('age_max')
        age_min = int(age_min) if age_min else None
        age_max = int(age_max) if age_max else None

        dimensions_filter = request.GET.get('dimensions')
        dimensions_filter = [int(x) for x in dimensions_filter.split(',')] if dimensions_filter else None

        percentiles = request.GET.get('percentiles')
        percentiles_list = [float(p) for p in percentiles.split(',')] if percentiles else [5, 10, 25, 50, 75, 90, 95]

        results = calculate_percentiles_for_study(
            study_id,
            gender=gender,
            age_min=age_min,
            age_max=age_max,
            dimensions_filter=dimensions_filter,
            percentiles_list=percentiles_list
        )

        # Preparar el documento PDF en memoria
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Tabla antropométrica: {name_study}")

        styles = getSampleStyleSheet()
        # Estilos personalizados
        title_style = styles["Title"]
        title_style.alignment = 1  # Centrado

        header_style = styles["Heading4"]
        normal_style = styles["Normal"]
        normal_style.spaceAfter = 8

        elements = []

        # Título
        elements.append(Paragraph(f"Tabla antropométrica: {name_study}", title_style))
        elements.append(Spacer(1, 12))

        # Metadatos (usamos una tabla para organizarlos, de 4 columnas)
        meta_data = [
            ["Fecha inicio:", str(study.start_date), "Fecha fin:", str(study.end_date)],
            ["Muestra:", str(study.size), "Género:", gender if gender else "Mixto"],
            ["Edad mínima:", str(age_min) if age_min is not None else "—", "Edad máxima:", str(age_max) if age_max is not None else "—"],
        ]
        meta_table = Table(meta_data, hAlign="LEFT", colWidths=[80, 120, 80, 120])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 12))

        # Descripción: cabecera y texto en un párrafo aparte
        elements.append(Paragraph("Descripción:", header_style))
        elements.append(Paragraph(study.description, normal_style))
        elements.append(Spacer(1, 12))

        # Preparar datos para la tabla de resultados
        # Encabezados
        headers = ["Dimensión", "Media", "SD"] + [f"P{p}" for p in percentiles_list]
        data_table = [headers]
        
        # Agregar cada fila de resultados
        for res in results:
            row = [
                res["dimension"],
                round(res["mean"], 2),
                round(res["sd"], 2),
            ]
            row += [res["percentiles"].get(str(p), '') for p in percentiles_list]
            data_table.append(row)
        
        # Crear tabla con estilos
        table = Table(data_table, hAlign="CENTER")
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        # Construir el documento
        doc.build(elements)

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="percentiles_study_{study_id}.pdf"'
        return response

    except Study.DoesNotExist:
        return HttpResponse("Estudio no encontrado.", status=404)
    except Exception as e:
        return HttpResponse(f"Ocurrió un error: {str(e)}", status=500)

def generar_pdf_ficha(request):
    study_id = request.GET.get('study_id')
    person_id = request.GET.get('person_id')
    # 1) Recuperar objetos
    study  = Study.objects.get(id=study_id)
    person = Person.objects.get(id=person_id)
    print(person)
    print(study)

    # 2) Formatear datos básicos
    # datos = {
    #     "nombre": person.name,
    #     "sexo":   dict(Person.GENDER_CHOICES).get(person.gender, person.gender),
    #     "pais":   person.country,
    #     "estado": person.state,
    #     "fecha_nacimiento": if  person.date_of_birth:  person.date_of_birth.strftime("%Y/%m/%d") ,
    # }

    datos = {
        "nombre": person.name if person.name else "",  # o '' si prefieres string vacío
        "sexo": dict(Person.GENDER_CHOICES).get(person.gender, person.gender) if person.gender else "",
        "pais": person.country if person.country else "",
        "estado": person.state if person.state else "",
        "fecha_nacimiento": person.date_of_birth.strftime("%Y/%m/%d") if person.date_of_birth else ""
    }

    # 3) Traer todas las mediciones de este estudio y persona
    medidas = Measurement.objects.filter(person=person, study=study)
   
    for m in medidas:
        print(m.position)

    # 4) Separar erecto (P) y sentado (S)
    medidas_erecto  = [
        {"nombre": m.dimension.name, "valor": m.value}
        for m in medidas if m.position == "P"
    ]
    print("Erectp",medidas_erecto)
    medidas_sentado = [
        {"nombre": m.dimension.name, "valor": m.value}
        for m in medidas if m.position == "S"
    ]

    # 5) Tomar peso (dimensión "Peso") si existe
    peso_med = medidas.filter(dimension__name__iexact="Peso").first()
    peso = peso_med.value if peso_med else ""

    # 6) Control: fechas y responsables
    datos["medidas_erecto"]  = medidas_erecto
    datos["medidas_sentado"] = medidas_sentado
    datos["control"] = {
        "fecha":      timezone.now().date().strftime("%Y/%m/%d"),
        "inicio":     study.start_date.strftime("%Y/%m/%d"),
        "fin":        study.end_date.strftime("%Y/%m/%d"),
        "responsable": getattr(study, "responsible", ""),
        "supervisor":  getattr(study, "supervisor", ""),
        "dimensiones": "mm",
        "peso":        peso,
    }

    # 7) Generar PDF
    buffer = io.BytesIO()
    doc     = SimpleDocTemplate(buffer, pagesize=A4)
    styles  = getSampleStyleSheet()
    styleN  = styles["Normal"]
    styleB  = styles["Heading4"]

    def p(texto, estilo=styleN):
        return Paragraph(texto, estilo)

    # Construcción de filas
    tabla = []
    tabla.append([p("<b>Ficha de recolección de datos antropométricos</b>"), "", ""])
    tabla.append([p(f"Nombre: {datos['nombre']}"), p(f"Sexo: {datos['sexo']}"), ""])
    tabla.append([
        p(f"País: {datos['pais']}"),
        p(f"Estado: {datos['estado']}"),
        p(f"Fecha de nacimiento: {datos['fecha_nacimiento']}"),
    ])

    # Erecto
    tabla.append([p("<b>Medidas en posición erecto</b>"), "", ""])
    tabla.append([p("<b>No</b>"), p("<b>Nombre</b>"), p("<b>Valor (mm)</b>")])
    for i, m in enumerate(datos["medidas_erecto"], start=1):
        tabla.append([str(i), m["nombre"], str(m["valor"])])

    # Sentado
    idx_sent =  5 + len(datos["medidas_erecto"])
    tabla.append([p("<b>Medidas en posición sentado</b>"), "", ""])
    tabla.append([p("<b>No</b>"), p("<b>Nombre</b>"), p("<b>Valor (mm)</b>")])
    for i, m in enumerate(datos["medidas_sentado"], start=1):
        tabla.append([str(i), m["nombre"], str(m["valor"])])

    # Control
    idx_ctrl = idx_sent + 2 + len(datos["medidas_sentado"])
    tabla.append([p("<b>Control</b>"), "", ""])
    tabla.append([
        p(f"Fecha: {datos['control']['fecha']}"),
        p(f"Inicio: {datos['control']['inicio']}"),
        p(f"Fin: {datos['control']['fin']}"),
    ])
    tabla.append([
        p(f"Responsable: {datos['control']['responsable']}"),
        p(f"Supervisor: {datos['control']['supervisor']}"),
        "",
    ])
    tabla.append([
        p(f"Dimensiones: {datos['control']['dimensiones']}"),
        p(f"Peso: {datos['control']['peso']} kg"),
        "",
    ])

    # Crear tabla y estilo
    t = Table(tabla, colWidths=[180, 180, 180])
    estilo = TableStyle([
        ('GRID',    (0,0), (-1,-1), 0.8, colors.black),
        ('SPAN',    (0,0), (-1,0)),   # Título
        ('SPAN',    (0,3), (-1,3)),   # Subtítulo erecto
        ('SPAN',    (0, idx_sent), (-1, idx_sent)),  # Subtítulo sentado
        ('SPAN',    (0, idx_ctrl),   (-1, idx_ctrl)),# Subtítulo control
        ('ALIGN',   (0,0), (-1,0),   'CENTER'),
        ('VALIGN',  (0,0), (-1,-1),  'MIDDLE'),
    ])
    t.setStyle(estilo)

    doc.build([t])
    buffer.seek(0)

    return HttpResponse(
        buffer,
        content_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="ficha_{person.name}.pdf"'}
    )

