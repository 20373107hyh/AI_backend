# Generated by Django 5.0.3 on 2024-03-20 03:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("teacher", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="score",
            options={"verbose_name": "分数信息", "verbose_name_plural": "分数信息"},
        ),
        migrations.AlterField(
            model_name="container",
            name="container_name",
            field=models.CharField(max_length=100, verbose_name="容器名称"),
        ),
    ]