from django.db import models
from django.utils import timezone

from accounts.models import User
# Create your models here.
class Person(models.Model):
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(blank=True, null=True)
    country = models.CharField(max_length=100,blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
    
    # def get_dimensions(self, obj):
    #     study_id = self.context['study_id']
    #     # Filtrar las mediciones para esta persona y este estudio
    #     measurements = Measurement.objects.filter(person=obj, study_id=study_id).select_related('dimension')
    #     # Crear un diccionario con las dimensiones y sus valores
    #     return {measure.dimension.name: measure.value for measure in measurements}


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


# class Supervisor(models.Model):
#     name = models.CharField(max_length=100)
#     email = models.EmailField()

#     def __str__(self):
#         return self.name

# class AnthropometricTable(models.Model):
#     # study = models.OneToOneField(Study, on_delete=models.CASCADE, )
#     study = models.ForeignKey(Study, on_delete=models.CASCADE)
#     name = models.CharField(max_length=100, null=True)  # Nombre opcional para la tabla
#     description = models.TextField(blank=True, null=True)  # Descripción opcional
#     dimension = models.ManyToManyField(Dimension, through='AnthropometricStatistic')

#     def __str__(self):
#         return f"Tabla Antropométrica de {self.study.name}"


# class AnthropometricStatistic(models.Model):
#     table = models.ForeignKey(AnthropometricTable, on_delete=models.CASCADE)
#     dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE)
#     mean = models.FloatField()
#     sd = models.FloatField()
#     percentile_5 = models.FloatField(blank=True, null=True)
#     percentile_10 = models.FloatField(blank=True, null=True)
#     percentile_25 = models.FloatField(blank=True, null=True)
#     percentile_50 = models.FloatField(blank=True, null=True)
#     percentile_75 = models.FloatField(blank=True, null=True)
#     percentile_90 = models.FloatField(blank=True, null=True)
#     percentile_95 = models.FloatField(blank=True, null=True)

#     class Meta:
#       unique_together = ('table', 'dimension')
                       
#     def __str__(self):
#         return f"{self.dimension.name} - {self.table.study.name}"

