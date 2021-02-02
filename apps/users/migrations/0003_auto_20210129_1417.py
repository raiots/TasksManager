# Generated by Django 3.1.5 on 2021-01-29 14:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20210129_1332'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='department',
            options={'verbose_name': '部门', 'verbose_name_plural': '部门'},
        ),
        migrations.AddField(
            model_name='taskproperty',
            name='own_department',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.department'),
            preserve_default=False,
        ),
    ]