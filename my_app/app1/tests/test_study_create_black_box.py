from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from app1.models import Dimension

class StudyCreateBlackBoxTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        # 1) Creamos un usuario de registro normal (role queda en 'usuario')
        self.user = User.objects.create_user(
            username='investigador_test', 
            password='secreto123'
        )
        # 2) Simulamos que un admin le asignó el rol de 'investigador'
        self.user.role = User.INVESTIGADOR
        self.user.save()

        # 3) Creamos dos dimensiones de ejemplo
        self.dim1 = Dimension.objects.create(name="Altura", initial="Alt", category='0')
        self.dim2 = Dimension.objects.create(name="Peso",   initial="P",   category='7')

        # 4) Ruta para POST /api/studies/
        self.studies_url = reverse('study-list')

    def obtain_token(self):
        login_url = reverse('token_obtain_pair')
        login_payload = {
            "username": self.user.username,
            "password": "secreto123"
        }
        login_resp = self.client.post(login_url, login_payload, format='json')
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        return login_resp.json()['access']

    def test_create_study_con_datos_validos_devuelve_201(self):
        """
        Con credenciales válidas (JWT) y role='investigador',
        debe devolver 201 Created y JSON con los datos del estudio.
        """
        # 1) Obtenemos token
        token = self.obtain_token()

        # 2) Adjuntamos el token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # 3) Payload válido
        payload = {
            "name": "Estudio de Prueba",
            "description": "Descripción breve",
            "age_min": 10,
            "age_max": 20,
            "classification": "A",   # Adolescente
            "gender": "MF",          # Mixto
            "size": 100,
            "location": "Ciudad X",
            "country": "País Y",
            "start_date": "2025-06-01",
            "end_date": "2025-06-30",
            "study_dimension": [
                {"id_dimension": self.dim1.id},
                {"id_dimension": self.dim2.id}
            ]
        }

        response = self.client.post(self.studies_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['name'], "Estudio de Prueba")
        self.assertEqual(data['size'], 100)
        self.assertEqual(data['classification'], "A")
        # Supervisor ha de coincidir con el ID de nuestro usuario
        self.assertEqual(data['supervisor'], self.user.id)
        # Debe devolver campo `dimensions` como dict agrupado
        self.assertIn('dimensions', data)
        self.assertIsInstance(data['dimensions'], dict)

    def test_create_study_sin_autenticacion_devuelve_401(self):
        """
        Sin token JWT, devuelve 401 Unauthorized.
        """
        payload = {
            "name": "Estudio X",
            "age_min": 5,
            "age_max": 10,
            "classification": "L",
            "gender": "M",
            "size": 50,
            "start_date": "2025-07-01",
            "study_dimension": [{"id_dimension": self.dim1.id}]
        }
        response = self.client.post(self.studies_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_study_campos_obligatorios_faltantes_devuelve_400(self):
        token = self.obtain_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # a) Falta “name”
        payload_a = {
            "description": "Sin nombre",
            "age_min": 5,
            "age_max": 10,
            "classification": "L",
            "gender": "M",
            "size": 50,
            "start_date": "2025-07-01",
            "study_dimension": [{"id_dimension": self.dim1.id}]
        }
        resp_a = self.client.post(self.studies_url, payload_a, format='json')
        self.assertEqual(resp_a.status_code, status.HTTP_400_BAD_REQUEST)
        errores_a = resp_a.json()
        self.assertIn('name', errores_a)

        # b) Falta “classification”
        payload_b = {
            "name": "Sin clasificación",
            "age_min": 5,
            "age_max": 10,
            "gender": "F",
            "size": 60,
            "start_date": "2025-07-01",
            "study_dimension": [{"id_dimension": self.dim1.id}]
        }
        resp_b = self.client.post(self.studies_url, payload_b, format='json')
        self.assertEqual(resp_b.status_code, status.HTTP_400_BAD_REQUEST)
        errores_b = resp_b.json()
        self.assertIn('classification', errores_b)

    def test_create_study_campos_invalidos_devuelve_400(self):
        token = self.obtain_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        payload = {
            "name": "Estudio Inválido",
            "age_min": 0,
            "age_max": 5,
            "classification": "XYZ",  # Invalido (no está en choices)
            "gender": "F",
            "size": 20,
            "start_date": "2025-07-01",
            "study_dimension": [{"id_dimension": self.dim1.id}]
        }
        resp = self.client.post(self.studies_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        errores = resp.json()
        self.assertIn('classification', errores)
