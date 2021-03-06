from django.db import models
from apps.users.models import User, MyGroup, QualityMark, TaskProperty, Department


class Todo(models.Model):
    todo_topic = models.CharField(
        verbose_name='工作事项',
        max_length=50
    )
    todo_note = models.CharField(
        verbose_name='工作要求及交付物',
        blank=True,
        max_length=100
    )
    deadline = models.DateField(verbose_name='完成时间')
    # related_task = models.ManyToManyField(Task, verbose_name="关联的主任务")
    duty_group = models.ForeignKey('users.Department', on_delete=models.CASCADE, verbose_name='承办单位')
    main_executor = models.ForeignKey(User, related_name='main_executor', on_delete=models.CASCADE,
                                      verbose_name='承/督办人', blank=True, null=True)
    sub_executor = models.ManyToManyField(User, related_name='sub_executor', verbose_name='协办人', blank=True)
    related_task = models.ForeignKey('Task', related_name='related_task', on_delete=models.CASCADE, verbose_name='年度任务')
    predict_work = models.DecimalField('预计工作量', max_digits=5, decimal_places=1, blank=True, null=True)
    evaluate_factor = models.DecimalField('折算系数', max_digits=5, decimal_places=1, blank=True, default='1')
    maturity = models.CharField(
        verbose_name='成熟度',
        max_length=5,
        choices=(
            ('0%', '0%'),
            ('10%', '10%'),
            ('50%', '50%'),
            ('70%', '70%'),
            ('90%', '90%'),
            ('100%', '100%')
        ),
        blank=True,
        default='0%',
    )
    real_work = models.DecimalField('实际工作量', max_digits=5, decimal_places=1, blank=True, null=True)
    complete_note = models.TextField('完成情况说明', max_length=150, blank=True)
    quality_mark = models.ForeignKey('users.QualityMark', on_delete=models.SET_NULL, blank=True, null=True,
                                     verbose_name='质量评价')

    def __str__(self):
        date = str(self.deadline)
        date = parse_ymd(date)
        return str(date) + self.todo_topic

    class Meta:
        ordering = ['deadline']
        verbose_name = '工作包'
        verbose_name_plural = '工作包'

    @property
    def task_id(self):
        return self.related_task.task_id

    @property
    def task_origin(self):
        return self.related_task.task_origin

    @property
    def duty_department(self):
        return self.related_task.duty_group

    @property
    def last_month_list(self):
        return self.deadline

    @property
    def get_total_num(self):
        return self.objects.all().count()

    @property
    def points(self):
        return int(self.predict_work * self.evaluate_factor)

    def list_sub_executor(self):
        return ', '.join([a.real_name for a in self.sub_executor.all()])
    list_sub_executor.short_description = '协办人'


class Task(models.Model):
    task_topic = models.CharField(
        verbose_name='任务名称',
        max_length=50
    )
    task_id = models.CharField(max_length=50, unique=True, verbose_name='编号')
    task_note = models.CharField(
        verbose_name='任务说明',
        max_length=100,
        blank=True
    )
    task_origin = models.CharField(max_length=150, verbose_name='任务来源', blank=True)
    task_property = models.ForeignKey('users.TaskProperty', on_delete=models.CASCADE, verbose_name='任务属性')
    department = models.ForeignKey('users.Department', related_name='department', on_delete=models.SET_NULL, blank=True,
                                   null=True, verbose_name='所属单位')
    duty_group = models.ForeignKey('users.Department', related_name='duty_group', on_delete=models.SET_NULL, blank=True,
                                   null=True, verbose_name='责任单位')
    principal = models.ForeignKey(User, related_name='principal', verbose_name='负责人', on_delete=models.CASCADE, blank=True, null=True)
    leader = models.ForeignKey(User, related_name='leader', verbose_name='主管领导', on_delete=models.CASCADE, blank=True, null=True)
    aim_value = models.CharField(max_length=50, verbose_name='目标值', blank=True)
    # start_date = models.DateField(verbose_name='起始日期')
    deadline = models.DateField(verbose_name='完成时间')

    def __str__(self):
        return self.task_topic

    class Meta:
        ordering = ['deadline']
        verbose_name = '年度任务'
        verbose_name_plural = '年度任务'


def parse_ymd(s):
    year_s, mon_s, day_s = s.split('-')
    date = mon_s + '月' + day_s + '日  '
    return date
# https://www.cnblogs.com/chichung/p/9905835.html
