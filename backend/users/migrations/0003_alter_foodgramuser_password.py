# Generated by Django 3.2.3 on 2024-11-01 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_foodgramuser_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foodgramuser',
            name='password',
            field=models.CharField(max_length=30, verbose_name='Пароль'),
        ),
    ]
