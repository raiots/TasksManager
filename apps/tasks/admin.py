import re

from django.contrib import admin
from django.utils.html import format_html

from . import models
from apps.users.models import TaskProperty


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
                'task_note', 'related_task', 'department'),
        }),
    )
    raw_id_fields = ("principal", "leader",)
    autocomplete_fields = ('related_task',)
    search_fields = ('related_task',)

class TaskInline(admin.StackedInline):
    model = models.Task

class TodoAdmin(admin.ModelAdmin):
    def sub_executor(self, obj):
        return ', '.join([a.real_name for a in obj.sub_executor.all()])

    fieldsets = [
        (None, {
            'fields': [
                'todo_topic', 'todo_note', 'deadline', 'duty_group', 'main_executor', 'sub_executor', 'predict_work',
                'evaluate_factor',
            ]
        }),
        ('完成情况', {
            'fields': [
                'real_work', 'complete_note', 'quality_mark', 'maturity',
            ], 'classes': ['collapse']
        }),
    ]
    # inlines = [TaskInline]
    list_display = (
        'todo_topic',
        'deadline',
        'task_id',
        'lined_task',
        'task_origin',
        'duty_department',
        'duty_group',
        'main_executor',
        # 'sub_executor',
    )
    list_filter = ('deadline', )
    list_display_links = ('todo_topic', 'deadline', )
    date_hierarchy = 'deadline'
    list_per_page = 20
    raw_id_fields = ("main_executor", "sub_executor")
    search_fields = ('todo_topic',)
    # ordering = ('task_id',)
    def approval_state(self, obj):
        return format_html('<span style="color:{};">{}</span>', 'green', obj.approval)
    def task_id(self, obj):
        return obj.task_id
    def lined_task(self, obj):
        return obj.lined_task
    def task_origin(self, obj):
        return obj.task_origin
    task_id.admin_order_field = 'task__task_id'
    task_id.short_description = '任务编号'
    lined_task.admin_order_field = 'task__task_topic'
    lined_task.short_description = '任务名称'
    task_origin.short_description = '任务来源'


admin.site.register(models.Task, TaskAdmin)
admin.site.register(models.Todo, TodoAdmin)
