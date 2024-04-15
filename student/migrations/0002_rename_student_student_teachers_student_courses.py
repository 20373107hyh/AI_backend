# Generated by Django 5.0.3 on 2024-03-20 03:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("student", "0001_initial"),
        ("teacher", "0002_alter_score_options_alter_container_container_name"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Student",
            new_name="Student_Teachers",
        ),
        migrations.CreateModel(
            name="Student_Courses",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("course_score", models.IntegerField(default=0)),
                (
                    "course_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="teacher.course"
                    ),
                ),
                (
                    "student_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="users.userinfo"
                    ),
                ),
            ],
        ),
    ]