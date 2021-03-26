import re

from django.contrib import admin
from django.utils.html import format_html

from . import models
from apps.users.models import TaskProperty, User


class TodoInline(admin.StackedInline):

    # 在Inline中同样筛选仅本部门的承办人、协办人
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'related_task':
            kwargs["queryset"] = models.Task.objects.filter(department=request.user.department)
        elif db_field.name == 'main_executor':
            kwargs["queryset"] = User.objects.filter(department=request.user.department)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'sub_executor':
            kwargs["queryset"] = User.objects.filter(department=request.user.department)
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    model = models.Todo
    extra = 0
    # classes = ['collapse']


class TaskAdmin(admin.ModelAdmin):

    # def formfield_for_manytomany(self, db_field, request, **kwargs):
    #     if db_field.name == "related_task":
    #         ori_path = request.path
    #         f_id = re.sub("\D", "", ori_path)
    #         try:
    #             kwargs["queryset"] = models.Task.objects.get(id=f_id).related_task
    #             return super().formfield_for_manytomany(db_field, request, **kwargs)
    #         except:
    #             pass
    #             # kwargs["queryset"] = models.Task.objects.get(id=2).related_task

    def get_changeform_initial_data(self, request):
        return {'department': request.user.department}

    # 年度任务编辑界面仅显示本部门的任务属性
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'task_property':
            kwargs["queryset"] = TaskProperty.objects.filter(own_department=request.user.department)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    list_display = (
        'task_property', 'task_id', 'task_topic', 'task_origin', 'aim_value', 'deadline', 'duty_group', 'principal',
        'leader', 'task_note',
    )

    fieldsets = (
        (None, {
            'fields': (
                ('task_property', 'task_id', 'task_topic', 'task_origin', 'aim_value', 'deadline', 'duty_group',
                 'principal', 'leader'),
                'task_note', 'department'),
        }),
    )
    inlines = [TodoInline]
    raw_id_fields = ("principal", "leader",)
    list_display_links = ('task_topic',)
    # autocomplete_fields = ('related_task',)
    # search_fields = ('related_task',)


class TodoAdmin(admin.ModelAdmin):

    # 工作包页面仅显示所属本部门的年度任务、承办人、协办人
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'related_task':
            kwargs["queryset"] = models.Task.objects.filter(department=request.user.department)
        elif db_field.name == 'main_executor':
            kwargs["queryset"] = User.objects.filter(department=request.user.department)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'sub_executor':
            kwargs["queryset"] = User.objects.filter(department=request.user.department)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    fieldsets = [
        (None, {
            'fields': [
                'related_task', 'todo_topic', 'todo_note', 'deadline', 'duty_group', 'main_executor', 'sub_executor',
                'predict_work', 'evaluate_factor',
            ],
            'description': []
        }),

        (None, {
            'fields': [],
        }),
    ]
    list_display = (
        'todo_topic',
        'deadline',
        'todo_note',
        'task_id',
        'task_origin',
        'lined_task',
        # 'duty_department',
        'duty_group',
        'main_executor',
        'list_sub_executor',
        'maturity',
        'real_work',
        'complete_note',
        'quality_mark',
    )
    list_editable = ['quality_mark']
    list_filter = ('deadline',)
    list_display_links = ('todo_topic', 'deadline', )
    date_hierarchy = 'deadline'
    list_per_page = 70  # 目的是取消自动分页，好像有bug
    # raw_id_fields = ("sub_executor",)
    search_fields = ('todo_topic',)
    ordering = ('related_task', )

    def approval_state(self, obj):
        return format_html('<span style="color:{};">{}</span>', 'green', obj.approval)

    def task_id(self, obj):
        return obj.task_id
    task_id.admin_order_field = 'related_task__task_id'
    task_id.short_description = '任务编号'

    def task_origin(self, obj):
        return obj.task_origin
    task_origin.short_description = '任务来源'

    def duty_department(self, obj):
        return obj.duty_group
    duty_department.short_description = '责任部门'

    def lined_task(self, obj):
        return obj.related_task
    lined_task.short_description = '任务名称'

# TODO 任务编辑界面按部门显示


admin.site.register(models.Task, TaskAdmin)
admin.site.register(models.Todo, TodoAdmin)
