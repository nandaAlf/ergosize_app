from rest_framework import serializers
from app1.models import AnthropometricStatistic, AnthropometricTable, Person, Measurement, Study, Dimension, StudyDimension

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = '__all__'

class DimensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dimension
        fields = '__all__'
        extra_kwargs = {
            'name': {'validators': []}  # Desactiva los validadores de unicidad
        }

class MeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = '__all__'

class StudyDimensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyDimension
        fields = '__all__'


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
    class Meta:
        model = Study
        fields = '__all__'
