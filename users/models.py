from django.db import models


# Create your models here.
class UserInfo(models.Model):
    STATE = (
        (1, "学生"),
        (2, "教师"),
        (3, "管理员"),
    )

    user_id = models.AutoField(primary_key=True)
    username = models.CharField("用户名", max_length=100)
    password = models.CharField("密码", max_length=100)
    realname = models.CharField("真实姓名", max_length=100)
    email = models.EmailField("邮箱")
    phone = models.CharField("电话号码", max_length=100)
    status = models.CharField("用户身份", max_length=100, choices=STATE)

    def __str__(self):
        return str(self.user_id)

    class Meta:
        verbose_name = "镜像信息"
        verbose_name_plural = verbose_name