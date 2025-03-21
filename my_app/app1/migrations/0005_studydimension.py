# Generated by Django 5.1.6 on 2025-03-13 03:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0004_alter_measurement_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudyDimension',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_dimension', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dimension_study', to='app1.dimension')),
                ('id_study', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='study_dimension', to='app1.study')),
            ],
            options={
                'unique_together': {('id_study', 'id_dimension')},
            },
        ),
    ]
