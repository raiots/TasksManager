# Generated by Django 3.1.5 on 2021-01-29 14:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20210129_1434'),
        ('tasks', '0003_auto_20210129_1335'),
    ]

    operations = [
        migrations.AlterField(
            model_name='todo',
            name='duty_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.department', verbose_name='承办单位'),
        ),
    ]