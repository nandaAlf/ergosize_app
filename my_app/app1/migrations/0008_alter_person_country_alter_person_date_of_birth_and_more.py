# Generated by Django 5.1.6 on 2025-03-13 20:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0007_remove_study_dimension_dimension_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='country',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='study',
            name='country',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='study',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='study',
            name='location',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
