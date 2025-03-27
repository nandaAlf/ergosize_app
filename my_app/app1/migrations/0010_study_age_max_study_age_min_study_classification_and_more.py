# Generated by Django 5.1.6 on 2025-03-24 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0009_alter_dimension_initial_alter_measurement_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='age_max',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='study',
            name='age_min',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='study',
            name='classification',
            field=models.CharField(choices=[('L', 'Lactante'), ('T', 'Transicional'), ('A', 'Adolescente'), ('E', 'Escolares'), ('AD', 'Adulto'), ('ADM', 'Adulto Mayor')], default=2, max_length=5),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='study',
            name='size',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
