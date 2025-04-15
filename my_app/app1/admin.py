from django.contrib import admin

from app1.models import  Study, Measurement, Dimension, Person, StudyDimension

# # Register your models here.
admin.site.register(Person)
admin.site.register(Dimension)
admin.site.register(Measurement)
# admin.site.register(Supervisor)
# admin.site.register(AnthropometricTable)
admin.site.register(Study)
admin.site.register(StudyDimension)
# admin.site.register(AnthropometricStatistic)
