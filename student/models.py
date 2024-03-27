from django.db import models
from users.models import UserInfo
from teacher.models import Course


class Student_Teachers(models.Model):
    student_id = models.ForeignKey(UserInfo, on_delete = models.CASCADE, related_name = 'students')
    teacher_id = models.ForeignKey(UserInfo, on_delete = models.CASCADE, related_name = 'teachers')


class Student_Courses(models.Model):
    student_id = models.ForeignKey(UserInfo, on_delete = models.CASCADE)
    course_id = models.ForeignKey(Course, on_delete = models.CASCADE)
    course_score = models.IntegerField(default = 0)
