# Generated by Django 5.1.6 on 2025-05-24 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0013_study_supervisor'),
    ]

    operations = [
        migrations.AddField(
            model_name='dimension',
            name='category',
            field=models.CharField(choices=[('0', 'Altura'), ('1', 'Longitud'), ('2', 'Profundidad'), ('3', 'Anchura'), ('4', 'Diametro'), ('5', 'Circunferencia'), ('6', 'Alcance'), ('7', 'Peso')], default=0, max_length=10),
            preserve_default=False,
        ),
    ]
