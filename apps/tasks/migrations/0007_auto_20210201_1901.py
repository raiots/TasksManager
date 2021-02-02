# Generated by Django 3.1.5 on 2021-02-01 19:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20210201_1900'),
        ('tasks', '0006_auto_20210201_1900'),
    ]

    operations = [
        migrations.AlterField(
            model_name='todo',
            name='quality_mark',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.qualitymark', verbose_name='质量评价'),
        ),
    ]