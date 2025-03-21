from rest_framework import serializers
from app1.models import AnthropometricStatistic, AnthropometricTable, Person, Measurement, Study, Dimension, StudyDimension


class DimensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dimension
        fields = '__all__'
        extra_kwargs = {
            'name': {'validators': []}  # Desactiva los validadores de unicidad
        }

class MeasurementSerializer(serializers.ModelSerializer):
    dimension_id = serializers.PrimaryKeyRelatedField(queryset=Dimension.objects.all(), source='dimension')
    study_id = serializers.PrimaryKeyRelatedField(queryset=Study.objects.all(), source='study')

    class Meta:
        model = Measurement
        fields = ['dimension_id', 'study_id', 'value', 'position']

class PersonSerializer(serializers.ModelSerializer):
    measurements = MeasurementSerializer(many=True)
    
    class Meta:
        model = Person
        fields = ['id', 'name', 'gender', 'date_of_birth', 'country', 'state', 'province', 'measurements']
    def create(self, validated_data):
        print("hola")
        print(validated_data)
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
    class Meta:
        model = StudyDimension
        fields = ['id_dimension']

class AnthropometricStatisticSerializer(serializers.ModelSerializer):
    dimension = DimensionSerializer()

    class Meta:
        model = AnthropometricStatistic
        fields = '__all__'

    def create(self, validated_data):
        print("Entrando a create")  # Debug: Verifica si el método se está ejecutando
        # Extrae los datos de la dimensión
        dimension_data = validated_data.pop('dimension')
        print("Datos de la dimensión:", dimension_data)  # Debug: Verifica los datos de la dimensión
        
        # Obtén la dimensión existente o lanza un error si no existe
        try:
            dimension = Dimension.objects.get(name=dimension_data['name'])
            print("Dimensión existente encontrada:", dimension)  # Debug: Verifica la dimensión
        except Dimension.DoesNotExist:
            raise serializers.ValidationError({"dimension": "La dimensión especificada no existe."})
        
        # Crea la estadística con la dimensión obtenida
        statistic = AnthropometricStatistic.objects.create(dimension=dimension, **validated_data)
        
        return statistic

    def update(self, instance, validated_data):
        # Extrae los datos de la dimensión
        dimension_data = validated_data.pop('dimension')
        
        # Obtén la dimensión existente o lanza una excepción si no existe
        try:
            dimension = Dimension.objects.get(name=dimension_data['name'])
        except Dimension.DoesNotExist:
            raise serializers.ValidationError({"dimension": "La dimensión especificada no existe."})
        
        # Actualiza la estadística con la dimensión obtenida
        instance.dimension = dimension
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance

class AnthropometricTableSerializer(serializers.ModelSerializer):
    # statistics = AnthropometricStatisticSerializer(many=True, source='anthropometricstatistic_set')

    class Meta:
        model = AnthropometricTable
        fields = '__all__'

class StudySerializer(serializers.ModelSerializer):
    dimensions = StudyDimensionSerializer(many=True, source='study_dimension', required=False)
    
    class Meta:
        model = Study
        fields = ['name', 'id', 'description', 'location', 'country', 'start_date', 'end_date', 'dimensions']

    def create(self, validated_data):
        # Extraer los datos de las dimensiones si están presentes
        dimensions_data = validated_data.pop('study_dimension', [])
        print("Datos de dimensiones:", dimensions_data)  # Depuración
        
        # Crear el estudio
        study = Study.objects.create(**validated_data)
        
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