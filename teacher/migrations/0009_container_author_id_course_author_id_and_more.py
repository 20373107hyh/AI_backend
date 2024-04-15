# Generated by Django 5.0.1 on 2024-04-09 07:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("teacher", "0008_experiment"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="container",
            name="author_id",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="users.userinfo",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="course",
            name="author_id",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="users.userinfo",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="images",
            name="author_id",
            field=models.ForeignKey(
                default="1",
                on_delete=django.db.models.deletion.CASCADE,
                to="users.userinfo",
            ),
            preserve_default=False,
        ),
    ]