from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from app1.models import Person, Measurement, Study, Dimension, StudyDimension
from app1.api.serializer import  PersonSerializer, MeasurementSerializer, StudyDimensionSerializer, StudySerializer, DimensionSerializer
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.db import connection
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.cell.cell import MergedCell
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from openpyxl import load_workbook
from django.views.decorators.csrf import csrf_exempt
import io


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
        
#MOVER A UTILS
def calculate_percentiles_for_study(study_id, gender=None, age_min=None, age_max=None, dimensions_filter=None, percentiles_list=None):
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
                    'dimension_id': dimension.id,	
                    'mean': mean,
                    'sd': sd,
                    'percentiles': percentiles_dict
                })
        
        return results

class Perceptil(View):
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
            results = calculate_percentiles_for_study(study_id, gender=gender,
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
    datos = {
        "nombre": "Fernanda Alfonso",
        "sexo": "Femenino",
        "pais": "Cuba",
        "estado": "UCLV",
        "fecha_nacimiento": "2000/01/01",
        # "lugar_de_medicion": "Cuba",
        # "objetivo_medicion": "Evaluación de la salud",
        "medidas_erecto": [
            {"nombre": "Altura", "valor": 160},
            {"nombre": "Distancia entre ojos", "valor": 20},
            {"nombre": "Altura", "valor": 160},
            {"nombre": "Distancia entre ojos", "valor": 20}
        ],
        "medidas_sentado": [
            {"nombre": "Circunferencia de la cadera", "valor": 60},
            {"nombre": "Distancia entre ojos", "valor": 4}
        ],
        "control": {
            "fecha": "2025/04/30",
            "inicio": "2020/01/02",
            "fin": "2023/03/03",
            "responsable": "Pedro Suarez",
            "supervisor": "Roberto Carlos",
            "dimensiones": "en mm",
            "peso": "50"
        }
    }

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    styleB = styles["Heading4"]

    contenido = []

    def p(texto, estilo=styleN):
        return Paragraph(texto, estilo)

    # Construimos todas las filas de una sola tabla
    tabla = []

    # Título principal (fila combinada)
    # tabla.append([p("<b>Ficha de recoleción de datos </b>", styleB), '', ''])
    tabla.append([p("<b>Ficha de recoleccion de datos antropométricos</b>"), '', ''])

    # Fila: nombre y sexo
    tabla.append([
        p("Nombre: {}".format(datos["nombre"])),
        p("Sexo: {}".format(datos["sexo"])),
        ''
    ])

    # Fila: país, estado, fecha de nacimiento
    tabla.append([
        p("País: {}".format(datos["pais"])),
        p("Estado: {}".format(datos["estado"])),
        p("Fecha de nacimiento: {}".format(datos["fecha_nacimiento"]))
    ])

    # Subtítulo: Medidas en posición erecto
    tabla.append([p("<b>Medidas en posición erecto</b>"), '', ''])

    # Encabezado tabla erecto
    tabla.append([p("<b>No</b>"), p("<b>Nombre</b>"), p("<b>Valor (mm)</b>")])

    # Datos erecto
    for i, m in enumerate(datos["medidas_erecto"], start=1):
        tabla.append([str(i), m["nombre"], str(m["valor"])])

    # Subtítulo: Medidas en posición sentado
    tabla.append([p("<b>Medidas en posición sentado</b>"), '', ''])

    # Encabezado tabla sentado
    tabla.append([p("<b>No</b>"), p("<b>Nombre</b>"), p("<b>Valor (mm)</b>")])

    for i, m in enumerate(datos["medidas_sentado"], start=1):
        tabla.append([str(i), m["nombre"], str(m["valor"])])

    # Subtítulo: Control
    tabla.append([p("<b>Control</b>"), '', ''])

    # Fila: fecha, inicio, fin
    tabla.append([
        p("Fecha: {}".format(datos["control"]["fecha"])),
        p("Inicio: {}".format(datos["control"]["inicio"])),
        p("Fin: {}".format(datos["control"]["fin"]))
    ])

    # Fila: responsable, supervisor
    tabla.append([
        p("Responsable: {}".format(datos["control"]["responsable"])),
        p("Supervisor: {}".format(datos["control"]["supervisor"])),
        ''
    ])

    # Fila: dimensiones y peso
    tabla.append([
        p("Dimensiones: {}".format(datos["control"]["dimensiones"])),
        p("Peso: {} kg".format(datos["control"]["peso"])),
        ''
    ])

    # Definir tabla como una sola gran tabla con columnas
    t = Table(tabla, colWidths=[180, 180, 180])

    # Estilo de la tabla
    estilo = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.8, colors.black),
        ('SPAN', (0, 0), (-1, 0)),  # Título
        ('SPAN', (0, 3), (-1, 3)),  # Subtítulo erecto
        ('SPAN', (0, 5 + len(datos["medidas_erecto"])), (-1, 5 + len(datos["medidas_erecto"]))),  # Subtítulo sentado
        ('SPAN', (0, 7 + len(datos["medidas_erecto"]) + len(datos["medidas_sentado"])), (-1, 7 + len(datos["medidas_erecto"]) + len(datos["medidas_sentado"]))),  # Subtítulo control
        # ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # título
        # ('BACKGROUND', (0, 3), (-1, 3), colors.lightgrey),
        # ('BACKGROUND', (0, 6 + len(datos["medidas_erecto"])), (-1, 6 + len(datos["medidas_erecto"])), colors.lightgrey),
        # ('BACKGROUND', (0, 9 + len(datos["medidas_erecto"]) + len(datos["medidas_sentado"])), (-1, 9 + len(datos["medidas_erecto"]) + len(datos["medidas_sentado"])), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

    t.setStyle(estilo)

    contenido.append(t)
    doc.build(contenido)

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="ficha_{datos["nombre"]}.pdf"'
    })
