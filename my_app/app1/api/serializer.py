from rest_framework import serializers
from app1.models import AnthropometricStatistic, AnthropometricTable, Person, Measurement, Study, MeasurementType

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = '__all__'

class MeasurementTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementType
        fields = '__all__'

class MeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = '__all__'

class AnthropometricStatisticSerializer(serializers.ModelSerializer):
    measurement_type = MeasurementTypeSerializer()

    class Meta:
        model = AnthropometricStatistic
        fields = '__all__'

class AnthropometricTableSerializer(serializers.ModelSerializer):
    statistics = AnthropometricStatisticSerializer(many=True, source='anthropometricstatistic_set')

    class Meta:
        model = AnthropometricTable
        fields = '__all__'

class StudySerializer(serializers.ModelSerializer):
    class Meta:
        model = Study
        fields = '__all__'
