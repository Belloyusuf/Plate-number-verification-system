# Generated by Django 3.2.23 on 2023-11-26 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('owners', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carregisteration',
            name='tank_capacity',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='owner',
            name='date_of_birth',
            field=models.DateField(help_text='Date of Birth Format 2000-11-25'),
        ),
    ]