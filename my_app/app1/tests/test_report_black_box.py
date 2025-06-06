# app1/tests/test_report_black_box.py

import io
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from app1.models import Study, Person, Dimension, StudyDimension, Measurement

class ReportBlackBoxTest(TestCase):
    def setUp(self):
        User = get_user_model()
        # 1) Creamos un usuario e inmediatamente le asignamos rol 'investigador'
        self.user = User.objects.create_user(username='investigador', password='secreto123')
        self.user.role = User.INVESTIGADOR
        self.user.save()

        # 2) Creamos un estudio asociado al usuario
        self.study = Study.objects.create(
            name="Estudio PDF",
            classification='A',   # Adolescente
            gender='MF',
            size=10,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            description="Prueba de PDF",
            location="Ciudad Test",
            country="País Test",
            supervisor=self.user
        )

        # 3) Creamos una persona
        self.person = Person.objects.create(
            name="María Pérez",
            gender='F',
            date_of_birth=timezone.now().date().replace(year=timezone.now().year - 12),
            country="TestLand",
            state="TestState",
            province="TestProvince"
        )

        # 4) Creamos una dimensión “Peso” y otra “Altura” y las asociamos al estudio
        self.dim_peso = Dimension.objects.create(name="Peso", initial="P", category='7')
        self.dim_altura = Dimension.objects.create(name="Altura", initial="A", category='0')
        StudyDimension.objects.create(id_study=self.study, id_dimension=self.dim_peso)
        StudyDimension.objects.create(id_study=self.study, id_dimension=self.dim_altura)

        # 5) Creamos mediciones para esa persona y ese estudio
        Measurement.objects.create(
            study=self.study,
            person=self.person,
            dimension=self.dim_peso,
            value=45.5,
            position='P',  # Parado
            date=timezone.now()
        )
        Measurement.objects.create(
            study=self.study,
            person=self.person,
            dimension=self.dim_altura,
            value=130.0,
            position='S',  # Sentado
            date=timezone.now()
        )

        # 6) URL del reporte
        self.url = reverse('report')

    def test_sin_params(self):
        """
        Si no pasamos study_id ni person_id, lo más probable es que falle con 500
        (p.ej. intentando hacer Study.objects.get(id=None)). 
        Verificamos que no sea 200.
        """
        response = self.client.get(self.url)  # sin query params
        # Puede ser 404 o 500 según tu manejo, en todo caso no debe ser 200
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_ids_invalidos(self):
        """
        Si enviamos study_id o person_id que no existen, debe lanzar excepción
        (Study.DoesNotExist o Person.DoesNotExist), y por tanto devolver 404.
        """
        # a) study_id inválido
        response_a = self.client.get(self.url, {'study_id': 9999, 'person_id': self.person.id})
        self.assertEqual(response_a.status_code, status.HTTP_404_NOT_FOUND)

        # b) person_id inválido
        response_b = self.client.get(self.url, {'study_id': self.study.id, 'person_id': 9999})
        self.assertEqual(response_b.status_code, status.HTTP_404_NOT_FOUND)

    def test_ids_validos_devuelve_pdf(self):
        """
        Con study_id y person_id correctos, la vista debe devolver:
          - status 200
          - content_type 'application/pdf'
          - encabezado 'Content-Disposition' con 'attachment; filename="ficha_<nombre>.pdf"'
          - el contenido binario no vacío (bytes de un PDF)
        """
        params = {
            'study_id': self.study.id,
            'person_id': self.person.id
        }
        response = self.client.get(self.url, params)

        # 1. Código 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. Revisamos Content-Type
        self.assertEqual(response['Content-Type'], 'application/pdf')

        # 3. Revisamos Content-Disposition
        disposition = response['Content-Disposition']
        # Debe contener algo como: attachment; filename="ficha_María Pérez.pdf"
        self.assertIn('attachment;', disposition)
        self.assertIn(f'ficha_{self.person.name}.pdf', disposition)

        # 4. El cuerpo de la respuesta no debe estar vacío y debe ser bytes
        content = response.content
        self.assertIsInstance(content, (bytes, bytearray))
        self.assertTrue(len(content) > 200)  # Al menos unos cientos de bytes de PDF

        # 5. Opcional: comprobamos que empiece con el header típico de un PDF "%PDF"
        self.assertTrue(content.startswith(b'%PDF'))

