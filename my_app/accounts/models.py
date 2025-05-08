from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ADMIN = 'admin'
    INVESTIGADOR = 'investigador'
    USUARIO = 'usuario'
    ROLE_CHOICES = [
        (ADMIN, 'Administrador'),
        (INVESTIGADOR, 'Investigador'),
        (USUARIO, 'Usuario'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=USUARIO)

    # Campos adicionales para investigadores
    institucion = models.CharField(
        max_length=255,
        blank=True,
        help_text="Institución a la que pertenece el investigador"
    )
    profesion = models.CharField(
        max_length=150,
        blank=True,
        help_text="Profesión u ocupación del investigador"
    )
   

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
