from django.db import models


# Create your models here.
class UserInfo(models.Model):

    user_id = models.AutoField(primary_key=True)
    username = models.CharField("用户名", max_length=100)
    password = models.CharField("密码", max_length=100)
    realname = models.CharField("真实姓名", max_length=100)
    email = models.EmailField("邮箱", null=True, blank=True)
    phone = models.CharField("电话号码", max_length=100, null=True, blank=True)
    status = models.CharField("用户身份", max_length=100)

    def __str__(self):
        return str(self.user_id)

    class Meta:
        verbose_name = "镜像信息"
        verbose_name_plural = verbose_name