# app1/tests/test_auth_endpoints.py

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

class TokenObtainPairBlackBoxTest(APITestCase):
    def setUp(self):
        # 1) Creamos un usuario en la base de datos de pruebas
        User = get_user_model()
        self.username = "usuario_test"
        self.password = "passw0rd_test"
        User.objects.create_user(username=self.username, password=self.password)

        # 2) Preparamos la URL reversable (asegúrate de que el 'name' coincida con tus urls.py)
        #    En urls.py debes tener algo como:
        #    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair')
        self.token_url = reverse('token_obtain_pair')

    def test_login_con_credenciales_validas_devuelve_200_y_tokens(self):
        """
        Envío username/password válidos a /api/token/.
        Espero status 200 y JSON con keys 'access' y 'refresh', ambas non-empty strings.
        """
        payload = {
            "username": self.username,
            "password": self.password
        }
        response = self.client.post(self.token_url, payload, format='json')

        # 1) Verifico el código de estado
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2) La respuesta JSON debe contener 'access' y 'refresh'
        data = response.json()
        self.assertIn('access', data)
        self.assertIn('refresh', data)

        # 3) Comprobamos que ambas cadenas no estén vacías
        self.assertIsInstance(data['access'], str)
        self.assertIsInstance(data['refresh'], str)
        self.assertTrue(len(data['access']) > 0, "El token 'access' no debe estar vacío")
        self.assertTrue(len(data['refresh']) > 0, "El token 'refresh' no debe estar vacío")

    def test_login_con_usuario_incorrecto_devuelve_401(self):
        """
        Envío credenciales inválidas (username o password equivocado).
        Espero status 401 Unauthorized y un mensaje de error.
        """
        payload = {
            "username": self.username,
            "password": "otra_contraseña_incorrecta"
        }
        response = self.client.post(self.token_url, payload, format='json')

        # 1) Verifico el código de estado (puede ser 401 o 400, según tu configuración de Simple JWT)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2) El contenido JSON debe describir el error (clave 'detail' suele usarse)
        data = response.json()
        # Simple JWT típicamente devuelve: {"detail": "No active account found with the given credentials"}
        self.assertIn('detail', data)
        self.assertIsInstance(data['detail'], str)

    def test_login_sin_campos_obligatorios_devuelve_400(self):
        """
        Envío un payload incompleto (sin 'password' o sin 'username').
        Espero status 400 Bad Request y mensajes de validación.
        """
        # a) Sin password
        payload_a = {"username": self.username}
        response_a = self.client.post(self.token_url, payload_a, format='json')
        self.assertEqual(response_a.status_code, status.HTTP_400_BAD_REQUEST)
        errors_a = response_a.json()
        # Serializer de TokenObtainPair exige ambos campos, así que debe incluir errors sobre 'password'
        self.assertIn('password', errors_a)

        # b) Sin username
        payload_b = {"password": self.password}
        response_b = self.client.post(self.token_url, payload_b, format='json')
        self.assertEqual(response_b.status_code, status.HTTP_400_BAD_REQUEST)
        errors_b = response_b.json()
        self.assertIn('username', errors_b)
