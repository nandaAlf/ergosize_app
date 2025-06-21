from rest_framework import serializers
from app1.models import Person, Measurement, Study, Dimension, StudyDimension, StudyPerson


class DimensionSerializer(serializers.ModelSerializer):
    id_dimension = serializers.IntegerField(source='id')
    class Meta:
        model = Dimension
        fields = ['id_dimension', 'name', 'initial','category']
        extra_kwargs = {
            'name': {'validators': []}  # Desactiva los validadores de unicidad
        }

class MeasurementSerializer(serializers.ModelSerializer):
    dimension_id = serializers.PrimaryKeyRelatedField(queryset=Dimension.objects.all(), source='dimension')
    study_id = serializers.PrimaryKeyRelatedField(queryset=Study.objects.all(), source='study')

    class Meta:
        model = Measurement
        fields = ['dimension_id', 'study_id', 'value', 'position','date']


class StudyPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyPerson
        fields = ['study','person']

class PersonSerializer(serializers.ModelSerializer):
    measurements = MeasurementSerializer(many=True)
    
    class Meta:
        model = Person
        fields = ['id','identification', 'name', 'gender', 'date_of_birth', 'country', 'state', 'province', 'measurements']
    
    def validate(self, data):
        # DRF hace esta validación automáticamente, así que la atrapamos y controlamos
        existing = Person.objects.filter(
            identification=data['identification']
            # name=data['name'],
            # gender=data['gender'],
            # date_of_birth=data.get('date_of_birth'),
            # country=data.get('country'),
            # state=data.get('state'),
            # province=data.get('province'),
        ).first()

        if existing:
            self.instance = existing  # <- Esto es CLAVE para que DRF no lo vea como error
        return data
    def create(self, validated_data):
        print("🔵 serializer create called")
        measurements_data = validated_data.pop('measurements')

        # person, created = Person.objects.get_or_create(
        #     name=validated_data['name'],
        #     gender=validated_data['gender'],
        #     date_of_birth=validated_data.get('date_of_birth'),
        #     country=validated_data.get('country'),
        #     state=validated_data.get('state'),
        #     province=validated_data.get('province'),
        #     defaults=validated_data
        # )
        person = self.instance or Person.objects.create(**validated_data)
        for m_data in measurements_data:
            Measurement.objects.update_or_create(
                person=person,
                study=m_data['study'],
                dimension=m_data['dimension'],
                defaults={
                    'value': m_data['value'],
                    'position': m_data['position'],
                }
            )
            StudyPerson.objects.get_or_create(
                person=person,
                study=m_data['study']
            )

        return person
          # Buscar si la persona ya existe (según los campos únicos definidos)
        # measurements_data = validated_data.pop('measurements')
        # person, created = Person.objects.get_or_create(
        #     name=validated_data['name'],
        #     gender=validated_data['gender'],
        #     date_of_birth=validated_data.get('date_of_birth'),
        #     country=validated_data.get('country'),
        #     state=validated_data.get('state'),
        #     province=validated_data.get('province'),
        #     defaults=validated_data
        # )
        #  # Insertar las mediciones
        # for m_data in measurements_data:
        #     # Crear o actualizar medición
        #     Measurement.objects.update_or_create(
        #         person=person,
        #         study=m_data['study'],
        #         dimension=m_data['dimension'],
        #         defaults={
        #             'value': m_data['value'],
        #             'position': m_data['position'],
        #         }
        #     )

        #     # Vincular a StudyPerson (si no está ya vinculado)
        #     StudyPerson.objects.get_or_create(
        #         person=person,
        #         study=m_data['study']
        #     )
        
        # measurements_data = validated_data.pop('measurements')
        # person = Person.objects.create(**validated_data)
        #   # Para evitar duplicados
   
        # study_ids_inserted = set()
        # for measurement_data in measurements_data:
        #     study = measurement_data['study']
        #     Measurement.objects.create(person=person, **measurement_data)
        #     if study.id not in study_ids_inserted:
        #         StudyPerson.objects.get_or_create(person=person, study=study)
        #         study_ids_inserted.add(study.id)
        # return person
    
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
    category = serializers.CharField(source='id_dimension.category', read_only=True)
    class Meta:
        model = StudyDimension
        fields = ['id_dimension','name','initial','category']
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
    # dimensions = StudyDimensionSerializer(many=True, source='study_dimension', required=False)
    current_size = serializers.SerializerMethodField()
    
      # Nuevo campo agrupado
    dimensions = serializers.SerializerMethodField(read_only=True)
    # current_size = serializers.SerializerMethodField()
      # → Solo escritura: mapea al related_name 'study_dimension'
    study_dimension = StudyDimensionSerializer(
        many=True, 
        # source='study_dimension',  # coincide con related_name en tu modelo
        write_only=True
    )
    
    # members
    class Meta:
        model = Study
        fields = ['name','size', 'id', 'description', 'location', 'country', 'start_date', 'end_date','age_min','age_max','classification','gender','supervisor','current_size', 'dimensions','study_dimension']
        read_only_fields = ['id', 'supervisor','current_sizes']

    def get_current_size(self, obj):
        # Cuenta personas únicas con mediciones en este estudio
        return Measurement.objects.filter(study=obj).values('person').distinct().count()

    def get_dimensions(self, obj):
        """
        Devuelve un dict { 'Altura': [...], 'Longitud': [...], ... }
        con las dimensiones de este Study.
        """
        # # Primero, recuperamos todas las StudyDimension de este Study
        # # study_dims = StudyDimension.objects.filter(id_study=obj).select_related('id_dimension')
        # # Mapa de código→etiqueta
        # labels = dict(Dimension.CATEGORY_CHOICES)

        # grouped = {}
        # for sd in study_dims:
        #     dim = sd.id_dimension
        #     cat_label = labels.get(dim.category, dim.category)
        #     # Serializar solo los datos que quieras exponer
        #     item = {
        #         'id_dimension': dim.id,
        #         'name':         dim.name,
        #         'initial':      dim.initial,
        #         # opcionalmente podrías incluir aquí sd.id o más campos
        #     }
        #     grouped.setdefault(cat_label, []).append(item)

        # return grouped
        labels = dict(Dimension.CATEGORY_CHOICES)
        grouped = {}
        for sd in obj.study_dimension.select_related('id_dimension').all():
            dim = sd.id_dimension
            cat = labels.get(dim.category, dim.category)
            item = {
                'id_dimension': dim.id,
                'name':         dim.name,
                'initial':      dim.initial,
            }
            grouped.setdefault(cat, []).append(item)
        return grouped

    
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