# Generated by Django 5.1.2 on 2024-10-14 15:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='rating_square_sum',
            field=models.FloatField(default=0.0),
        ),
    ]
