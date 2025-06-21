from django.db import models
from django.forms import ValidationError
from django.utils import timezone

from accounts.models import User
# Create your models here.
class Person(models.Model):
  
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    # id=models.CharField(max_length=11,blank=True,primary_key=True)
    identification = models.CharField(
        max_length=15,
        # unique=True,  # <-- Esto garantiza que no se repita
        verbose_name="Número de identificación",
        help_text="Ej: cédula, DNI o pasaporte",
        blank=True, null=True
    )

    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(blank=True, null=True)
    country = models.CharField(max_length=100,blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
    
    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(
    #             fields=['name', 'gender', 'date_of_birth', 'country', 'state', 'province'],
    #             name='unique_person_data'
    #         )
    #     ]    


class Dimension(models.Model):
    CATEGORY_CHOICES = [
        ('0', 'Alturas'),
        ('1', 'Longitudes'),
        ('2', 'Profundidades'),
        ('3', 'Anchuras'),
        ('4', 'Diametros'),
        ('5', 'Circunferencias'),
        ('6', 'Alcances'),
        ('7', 'Peso'),
    ]

    name = models.CharField(max_length=100, unique=True,)
    initial=models.CharField(max_length=6)
    category=models.CharField(max_length=10,choices=CATEGORY_CHOICES)


    def __str__(self):
        return f"{self.name}"


class Study(models.Model):
    CLASSFICATION_CHOICES = [
        ('L', 'Lactante'),
        ('T', 'Transicional'),
        ('A', 'Adolescente'),
        ('E', 'Escolares'),
        ('AD', 'Adulto'),
        ('ADM', 'Adulto Mayor'),
    ]
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('MF', 'Mixto'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    age_min=models.IntegerField(null=True)
    age_max=models.IntegerField(null=True)
    classification = models.CharField(max_length=5, choices=CLASSFICATION_CHOICES)
    gender = models.CharField(max_length=2, choices=GENDER_CHOICES)
    size = models.IntegerField()
    location = models.CharField(max_length=100,blank=True, null=True)
    country = models.CharField(max_length=100,blank=True, null=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(blank=True, null=True,db_index=True)
    supervisor = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name='studies',
        help_text='Usuario que creó este estudio'
    )
    # dimension = models.ManyToManyField(Dimension, through='StudyDimension')
    # supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)
    # anthropometric_table = models.OneToOneField(AnthropometricTable, on_delete=models.CASCADE, unique=True)

    def __str__(self):
        return self.name
    def clean(self):
        if self.age_min and self.age_max and self.age_min > self.age_max:
            raise ValidationError("La edad mínima no puede ser mayor a la máxima")
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError("La fecha de fin no puede ser anterior a la de inicio")
            
class StudyDimension(models.Model):
    id_study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name='study_dimension',)
    id_dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE, related_name='dimension_study')
    
    class Meta:
        unique_together = (('id_study', 'id_dimension'),)  # Clave primaria compuesta
        # verbose_name = 'Grupo-Dimensión'
        # verbose_name_plural = 'Grupos-Dimensiones'

    def __str__(self):
        return f"{self.id_study} - {self.id_dimension}"
class Measurement(models.Model):
    POSITION_CHOICES = [
        ('P', 'Parado'),
        ('S', 'Sentado'),
    ]
    
    study = models.ForeignKey(Study, on_delete=models.CASCADE)  # Relación con el estudio
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='measurements')
    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE)
    value = models.FloatField()
    position = models.CharField(max_length=2, choices=POSITION_CHOICES)
    date = models.DateTimeField(default=timezone.now)
    class Meta:
      unique_together = ('study','person', 'dimension')

    def __str__(self):
        return f"{self.person.name} - {self.dimension.name}"


class StudyPerson(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="participants")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="study_entries")

    class Meta:
        unique_together = ('study', 'person')
        verbose_name = "Participación en estudio"
        verbose_name_plural = "Participaciones en estudios"

    def __str__(self):
        return f"{self.person.name} en {self.study.name}"
