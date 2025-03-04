from django.contrib import admin

from app1.models import AnthropometricStatistic, AnthropometricTable, Study, Measurement, MeasurementType, Person

# # Register your models here.
admin.site.register(Person)
admin.site.register(MeasurementType)
admin.site.register(Measurement)
# admin.site.register(Supervisor)
admin.site.register(AnthropometricTable)
admin.site.register(Study)
admin.site.register(AnthropometricStatistic)
