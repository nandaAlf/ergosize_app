from django.db import models

# Create your models here.
class Person(models.Model):
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class MeasurementType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.unit})"


class Study(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    age_range = models.CharField(max_length=50)
    size = models.IntegerField()
    location = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    # supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)
    # anthropometric_table = models.OneToOneField(AnthropometricTable, on_delete=models.CASCADE, unique=True)

    def __str__(self):
        return self.name
    
class Measurement(models.Model):
    # POSITION_CHOICES = [
    #     (True, 'Parado'),
    #     (False, 'Erecto'),
    # ]
    POSITION_CHOICES = [
        ('P', 'Parado'),
        # ('Erecto', 'Erecto'),
        ('S', 'Sentado'),
        # ('Acostado', 'Acostado'),
    ]
    
    study = models.ForeignKey(Study, on_delete=models.CASCADE)  # Relación con el estudio
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    measurement_type = models.ForeignKey(MeasurementType, on_delete=models.CASCADE)
    measure = models.FloatField()
    # position = models.BooleanField(choices=POSITION_CHOICES)
    position = models.CharField(max_length=2, choices=POSITION_CHOICES)  # Ahora más flexible
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.person.name} - {self.measurement_type.name}"


# class Supervisor(models.Model):
#     name = models.CharField(max_length=100)
#     email = models.EmailField()

#     def __str__(self):
#         return self.name

class AnthropometricTable(models.Model):
    # study = models.OneToOneField(Study, on_delete=models.CASCADE, )
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, null=True)  # Nombre opcional para la tabla
    description = models.TextField(blank=True, null=True)  # Descripción opcional
    measurement_types = models.ManyToManyField(MeasurementType, through='AnthropometricStatistic')

    def __str__(self):
        return f"Tabla Antropométrica de {self.study.name}"


class AnthropometricStatistic(models.Model):
    table = models.ForeignKey(AnthropometricTable, on_delete=models.CASCADE)
    measurement_type = models.ForeignKey(MeasurementType, on_delete=models.CASCADE)
    mean = models.FloatField()
    sd = models.FloatField()
    percentile_5 = models.FloatField(blank=True, null=True)
    percentile_10 = models.FloatField(blank=True, null=True)
    percentile_25 = models.FloatField(blank=True, null=True)
    percentile_50 = models.FloatField(blank=True, null=True)
    percentile_75 = models.FloatField(blank=True, null=True)
    percentile_90 = models.FloatField(blank=True, null=True)
    percentile_95 = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.measurement_type.name} - {self.table.study.name}"