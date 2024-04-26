import datetime

import pytz
from django.db import models
from users.models import UserInfo


class Images(models.Model):
    image_id = models.CharField('镜像ID', primary_key=True, max_length=100)
    image_name = models.CharField('镜像名', max_length=100)
    create_time = models.DateTimeField('镜像创建时间', auto_now_add=True)
    update_time = models.DateTimeField('镜像更新时间', auto_now=True)
    author_id = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    cpu_num = models.CharField('CPU数量', max_length=100)
    mem_size = models.CharField('内存大小', max_length=100)

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
    base_image = models.CharField('基于镜像', max_length=100)
    cpu_num = models.CharField('CPU数量', max_length=100)
    mem_size = models.CharField('内存大小', max_length=100)
    http_port = models.IntegerField('HTTP端口')
    ssh_port = models.IntegerField('SSH端口')
    ssh_password = models.CharField('SSH密码', max_length=100)


    def __str__(self):
        return str(self.container_id)

    class Meta:
        verbose_name = "容器信息"
        verbose_name_plural = verbose_name


class Chapter(models.Model):
    chapter_number = models.IntegerField('章节编号', primary_key=True)
    chapter_name = models.CharField('章节名词', max_length=100)
    chapter_intro = models.CharField('章节简介', max_length=500)


class Course(models.Model):
    course_id = models.AutoField('课程ID', primary_key=True)
    author_id = models.ForeignKey(UserInfo, on_delete=models.PROTECT)
    use_image_name = models.CharField('使用镜像名', max_length=100)
    course_name = models.CharField('课程名称', max_length=100)
    course_intro = models.CharField('课程简介', max_length=1000)
    course_aim = models.CharField("课程目标", max_length=1000)
    course_limit_time = models.IntegerField('课程限时', default=0)
    course_difficulty = models.CharField('课程难度', max_length=100)
    course_chapter = models.ForeignKey(Chapter, on_delete=models.PROTECT)
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
    experiment_password = models.CharField('ssh密码', max_length=100)
    create_time = models.DateTimeField('实验创建时间', auto_now_add=True)
    update_time = models.DateTimeField('实验更新时间', auto_now=True)
    job_id = models.CharField(max_length=100)
    expire_time = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return str(self.course_id)

    class Meta:
        verbose_name = "实验信息"
        verbose_name_plural = verbose_name

    def get_remaining_time(self):
        # 获取剩余时间
        remaining_time = (self.expire_time - datetime.datetime.now(pytz.utc)).total_seconds()
        remaining_time = int(remaining_time)
        return remaining_time if remaining_time > 0 else 0


class FileUpload(models.Model):
    user_id = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    file_path = models.TextField()  #保存文件的相对路径