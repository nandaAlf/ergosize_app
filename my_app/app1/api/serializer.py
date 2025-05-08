from rest_framework import serializers
from app1.models import Person, Measurement, Study, Dimension, StudyDimension


class DimensionSerializer(serializers.ModelSerializer):
    id_dimension = serializers.IntegerField(source='id')
    class Meta:
        model = Dimension
        fields = ['id_dimension', 'name', 'initial']
        extra_kwargs = {
            'name': {'validators': []}  # Desactiva los validadores de unicidad
        }

class MeasurementSerializer(serializers.ModelSerializer):
    dimension_id = serializers.PrimaryKeyRelatedField(queryset=Dimension.objects.all(), source='dimension')
    study_id = serializers.PrimaryKeyRelatedField(queryset=Study.objects.all(), source='study')

    class Meta:
        model = Measurement
        fields = ['dimension_id', 'study_id', 'value', 'position','date']

class PersonSerializer(serializers.ModelSerializer):
    measurements = MeasurementSerializer(many=True)
    
    class Meta:
        model = Person
        fields = ['id', 'name', 'gender', 'date_of_birth', 'country', 'state', 'province', 'measurements']
    def create(self, validated_data):
        measurements_data = validated_data.pop('measurements')
        person = Person.objects.create(**validated_data)

        for measurement_data in measurements_data:
            Measurement.objects.create(person=person, **measurement_data)

        return person
    def update(self, instance, validated_data):
        measurements_data = validated_data.pop('measurements')
        instance.name = validated_data.get('name', instance.name)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.country = validated_data.get('country', instance.country)
        instance.state = validated_data.get('state', instance.state)
        instance.province = validated_data.get('province', instance.province)
        instance.save()

        # Actualizar o crear mediciones
        for measurement_data in measurements_data:
            measurement, created = Measurement.objects.update_or_create(
                person=instance,
                dimension=measurement_data['dimension'],
                study=measurement_data['study'],
                defaults=measurement_data
            )

        return instance


class StudyDimensionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='id_dimension.name', read_only=True)
    initial = serializers.CharField(source='id_dimension.initial', read_only=True)
    class Meta:
        model = StudyDimension
        fields = ['id_dimension','name','initial']
        extra_kwargs = {
            'id_dimension': {'write_only': False}  # El id_dimension es necesario para escritura
        }

# class AnthropometricStatisticSerializer(serializers.ModelSerializer):
#     dimension = DimensionSerializer()

#     class Meta:
#         model = AnthropometricStatistic
#         fields = '__all__'

#     def create(self, validated_data):
#         print("Entrando a create")  # Debug: Verifica si el método se está ejecutando
#         # Extrae los datos de la dimensión
#         dimension_data = validated_data.pop('dimension')
#         print("Datos de la dimensión:", dimension_data)  # Debug: Verifica los datos de la dimensión
        
#         # Obtén la dimensión existente o lanza un error si no existe
#         try:
#             dimension = Dimension.objects.get(name=dimension_data['name'])
#             print("Dimensión existente encontrada:", dimension)  # Debug: Verifica la dimensión
#         except Dimension.DoesNotExist:
#             raise serializers.ValidationError({"dimension": "La dimensión especificada no existe."})
        
#         # Crea la estadística con la dimensión obtenida
#         statistic = AnthropometricStatistic.objects.create(dimension=dimension, **validated_data)
        
#         return statistic

#     def update(self, instance, validated_data):
#         # Extrae los datos de la dimensión
#         dimension_data = validated_data.pop('dimension')
        
#         # Obtén la dimensión existente o lanza una excepción si no existe
#         try:
#             dimension = Dimension.objects.get(name=dimension_data['name'])
#         except Dimension.DoesNotExist:
#             raise serializers.ValidationError({"dimension": "La dimensión especificada no existe."})
        
#         # Actualiza la estadística con la dimensión obtenida
#         instance.dimension = dimension
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()
        
#         return instance

# class AnthropometricTableSerializer(serializers.ModelSerializer):
#     # statistics = AnthropometricStatisticSerializer(many=True, source='anthropometricstatistic_set')

#     class Meta:
#         model = AnthropometricTable
#         fields = '__all__'

class StudySerializer(serializers.ModelSerializer):
    dimensions = StudyDimensionSerializer(many=True, source='study_dimension', required=False)
    
    class Meta:
        model = Study
        fields = ['name','size', 'id', 'description', 'location', 'country', 'start_date', 'end_date', 'dimensions','age_min','age_max','classification','gender','supervisor']
        read_only_fields = ['id', 'supervisor']

    def create(self, validated_data):
        # Extraer los datos de las dimensiones si están presentes
        dimensions_data = validated_data.pop('study_dimension', [])
        
        # assign supervisor from context
        user = self.context['request'].user
        
        # Crear el estudio
        # study = Study.objects.create(**validated_data)
        study = Study.objects.create(supervisor=user, **validated_data)
        # Crear las relaciones StudyDimension
        for dimension_data in dimensions_data:
            # Asegúrate de que 'id_dimension' esté presente en dimension_data
            if 'id_dimension' in dimension_data:
                StudyDimension.objects.create(id_study=study, id_dimension=dimension_data['id_dimension'])
            else:
                print("Error: 'id_dimension' no está presente en dimension_data")
        
        return study
    
    def update(self, instance, validated_data):
        # Extraer los datos de las dimensiones si están presentes
        dimensions_data = validated_data.pop('study_dimension', [])
        print("Datos de dimensiones (update):", dimensions_data)  # Depuración
        
        # Actualizar los campos del estudio
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.location = validated_data.get('location', instance.location)
        instance.country = validated_data.get('country', instance.country)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.end_date = validated_data.get('end_date', instance.end_date)
        instance.size = validated_data.get('size', instance.size)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.age_max = validated_data.get('age_max', instance.age_max)
        instance.age_min = validated_data.get('age_min', instance.age_min)
        instance.classification = validated_data.get('classification', instance.classification)
        instance.save()
        
        # Eliminar las relaciones StudyDimension existentes
        StudyDimension.objects.filter(id_study=instance).delete()
        
        # Crear las nuevas relaciones StudyDimension
        for dimension_data in dimensions_data:
            if 'id_dimension' in dimension_data:
                StudyDimension.objects.create(id_study=instance, id_dimension=dimension_data['id_dimension'])
            else:
                print("Error: 'id_dimension' no está presente en dimension_data")
        
        return instance
    
    
class PersonMeasurementSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='person.id')
    name = serializers.CharField(source='person.name')
    dimensions = serializers.SerializerMethodField()

    def get_dimensions(self, obj):
        # obj es un dict { 'person': <Person>, 'measurements': <QuerySet> }
        measurements = obj['measurements']
        # Convertimos a { dimension_name: value, ... }
        return {
            m.dimension.name: m.value
            for m in measurements
        }
        
class StudyDetailWithPersonsSerializer(serializers.ModelSerializer):
    persons = serializers.SerializerMethodField()

    class Meta:
        model = Study
        # fields = [
        #     'id', 'name', 'description', 'location', 'country',
        #     'start_date', 'end_date', 'persons',
        # ]
        fields = [
            'id', 'persons',
        ]


    def get_persons(self, study):
        # Todas las mediciones de este estudio
        qs = Measurement.objects.filter(study=study).select_related('person', 'dimension')
        # Agrupamos por persona
        by_person = {}
        for m in qs:
            by_person.setdefault(m.person, []).append(m)
        # Construimos lista de dicts para el serializer
        data = []
        for person, measurements in by_person.items():
            data.append({
                'person': person,
                'measurements': measurements
            })
        return PersonMeasurementSerializer(data, many=True).data