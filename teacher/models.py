from django.db import models
from users.models import UserInfo


class Images(models.Model):
    image_id = models.CharField('镜像ID', primary_key=True, max_length=100)
    image_name = models.CharField('镜像名', max_length=100)
    create_time = models.DateTimeField('镜像创建时间', auto_now_add=True)
    update_time = models.DateTimeField('镜像更新时间', auto_now=True)
    author_id = models.ForeignKey(UserInfo, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.image_id)

    class Meta:
        verbose_name = "镜像信息"
        verbose_name_plural = verbose_name


class Container(models.Model):
    container_id = models.CharField('容器ID', primary_key=True, max_length=100)
    container_name = models.CharField('容器名称', max_length=100)
    container_url = models.URLField('容器URL')
    create_time = models.DateTimeField('容器创建时间', auto_now_add=True)
    update_time = models.DateTimeField('容器更新时间', auto_now=True)
    author_id = models.ForeignKey(UserInfo, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.container_id)

    class Meta:
        verbose_name = "容器信息"
        verbose_name_plural = verbose_name


class Course(models.Model):
    course_id = models.AutoField('课程ID', primary_key=True)
    author_id = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    use_image_name = models.CharField('使用镜像名', max_length=100)
    course_name = models.CharField('课程名称', max_length=100)
    course_intro = models.CharField('课程简介', max_length=1000)
    course_aim = models.CharField("课程目标", max_length=1000)
    course_limit_time = models.IntegerField('课程限时', default=0)
    course_difficulty = models.CharField('课程难度', max_length=100)
    course_chapter = models.IntegerField('课程章节')
    create_time = models.DateTimeField('课程创建时间', auto_now_add=True)
    update_time = models.DateTimeField('课程更新时间', auto_now=True)

    def __str__(self):
        return str(self.course_id)

    class Meta:
        verbose_name = "容器信息"
        verbose_name_plural = verbose_name


class Score(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    student_id = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    score = models.FloatField("实验分数", default=0)

    def __str__(self):
        return str(self.course_id)

    class Meta:
        verbose_name = "分数信息"
        verbose_name_plural = verbose_name


class Experiment(models.Model):
    experiment_id = models.AutoField('实验ID', primary_key=True)
    user_id = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    experiment_countdown = models.IntegerField('实验倒计时')
    experiment_url = models.URLField('实验url')
    create_time = models.DateTimeField('实验创建时间', auto_now_add=True)
    update_time = models.DateTimeField('实验更新时间', auto_now=True)

    def __str__(self):
        return str(self.course_id)

    class Meta:
        verbose_name = "实验信息"
        verbose_name_plural = verbose_name