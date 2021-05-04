from django.db import models
from django.contrib.auth.models import AbstractUser, Group


# Create your models here.
from django.db.models import Avg, Sum, F, Value


class User(AbstractUser):
    real_name = models.CharField(max_length=150, verbose_name='姓名')
    staff_id = models.CharField(max_length=150, verbose_name='工号')
    department = models.ForeignKey('Department', related_name='member', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.real_name

    @classmethod
    def get_total_point(cls):
        return cls.objects.annotate(total=Sum('main_executor__predict_work'))
    # def get_total_point(cls):
    #     return cls.objects.aggregate(total=Sum(F('main_executor__predict_work') * F('main_executor__evaluate_factor') + F('sub_executor__predict_work') * F('sub_executor__evaluate_factor')))['total']

    @classmethod
    def get_predict_work_count(cls):
        return cls.objects.aggregate(total_predict_work=Sum('main_executor__predict_work'))


class MyGroup(Group):
    class Meta:
        verbose_name = '权限组'
        verbose_name_plural = '权限组'


class Department(models.Model):
    name = models.CharField(max_length=50, verbose_name='部门名称')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '部门'
        verbose_name_plural = '部门'

    @property
    def get_user_number(self):
        return self.member.count()


class MarkValue(models.Model):
    mark_value = models.DecimalField('评价等级考核系数', max_digits=3, decimal_places=2)

    def __str__(self):
        return str(self.mark_value)
    class Meta:
        verbose_name = '评价等级考核系数'
        verbose_name_plural = verbose_name


class QualityMark(models.Model):
    mark_name = models.CharField('评价等级定义', max_length=10)
    mark_value = models.ForeignKey('MarkValue', on_delete=models.CASCADE)

    def __str__(self):
        return self.mark_name
    class Meta:
        verbose_name = '评价等级定义'
        verbose_name_plural = verbose_name


class TaskProperty(models.Model):
    own_department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属部门')
    task_property = models.CharField(max_length=50, verbose_name='任务属性')

    class Meta:
        verbose_name = '任务属性'
        verbose_name_plural = '任务属性'

    def __str__(self):
        return self.task_property
