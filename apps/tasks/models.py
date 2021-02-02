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
    # related_task = models.ManyToManyField(Task, verbose_name="关联的主任务")
    duty_group = models.ForeignKey('users.Department', on_delete=models.CASCADE, verbose_name='承办单位')
    main_executor = models.ForeignKey(User, related_name='main_executor', on_delete=models.SET_NULL, verbose_name='承/督办人', null=True)
    sub_executor = models.ManyToManyField(User, related_name='sub_executor', verbose_name='协办人', default='', blank=True)
    predict_work = models.DecimalField('预计工作量', max_digits=5, decimal_places=1)
    evaluate_factor = models.DecimalField('折算系数', max_digits=5, decimal_places=1)
    maturity = models.CharField(
        verbose_name='成熟度',
        max_length=5,
        choices=(
            ('0%', '0%'),
            ('10%', '10%'),
            ('20%', '20%'),
            ('30%', '30%'),
            ('40%', '40%'),
            ('50%', '50%'),
            ('60%', '60%'),
            ('70%', '70%'),
            ('80%', '80%'),
            ('90%', '90%'),
            ('100%', '100%')
        ),
        blank=True,
        default='0%',
    )
    real_work = models.DecimalField('实际工作量', max_digits=5, decimal_places=1, blank=True, null=True)
    complete_note = models.TextField('完成情况说明', max_length=150, blank=True)
    quality_mark = models.ForeignKey('users.QualityMark', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='质量评价')
    deadline = models.DateField(verbose_name='完成时间')

    def __str__(self):
        date = str(self.deadline)
        date = parse_ymd(date)
        return str(date) + self.todo_topic

    class Meta:
        ordering = ['deadline']
        verbose_name = '工作包'
        verbose_name_plural = '工作包'

    @property
    def lined_task(self):
        lined_task = Task.objects.filter(related_task=self)
        for task in lined_task:
            return task.task_topic
    # TODO 不知道有没有不用for循环直接查的

    @property
    def task_id(self):
        tasks = Task.objects.filter(related_task=self)
        for task in tasks:
            return task.task_id

    def task_origin(self):
        tasks = Task.objects.filter(related_task=self)
        for task in tasks:
            return task.task_origin
    def duty_department(self):
        tasks = Task.objects.filter(related_task=self)
        for task in tasks:
            return task.duty_group

    @property
    def last_month_list(self):
        return self.deadline

    @property
    def get_tatal_num(self):
        return self.objects.all().count()


class Task(models.Model):
    task_topic = models.CharField(
        verbose_name='任务名称',
        max_length=50
    )
    task_id = models.CharField(max_length=50, unique=True, verbose_name='任务编号')
    task_note = models.CharField(
        verbose_name='任务说明',
        max_length=100
    )
    task_origin = models.CharField(max_length=150, verbose_name='任务来源')
    task_property = models.ForeignKey('users.TaskProperty', on_delete=models.CASCADE, verbose_name='任务属性')
    related_task = models.ManyToManyField(Todo, verbose_name='任务节点', blank=True)
    department = models.ForeignKey('users.Department', related_name='department', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='所属单位')
    duty_group = models.ForeignKey('users.Department', related_name='duty_group', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='责任单位')
    principal = models.ForeignKey(User, related_name='principal', verbose_name='负责人', on_delete=models.CASCADE)
    leader = models.ForeignKey(User, related_name='leader', verbose_name='主管领导', on_delete=models.CASCADE)
    aim_value = models.CharField(max_length=50, verbose_name='目标值')
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
