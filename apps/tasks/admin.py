import re

from django.contrib import admin
from django.http import JsonResponse
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from import_export.formats import base_formats

from . import models
from apps.users.models import TaskProperty, User
from .resources import TodoResources, TaskResources


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


class TaskAdmin(ImportExportModelAdmin):
    resource_class = TaskResources

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

    # 所属单位默认为访问用户的部门
    def get_changeform_initial_data(self, request):
        return {'department': request.user.department}

    # 年度任务编辑界面仅显示本部门的任务属性
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'task_property':
            kwargs["queryset"] = TaskProperty.objects.filter(own_department=request.user.department)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # 仅显示当前部门的年度任务，除非为超管
    def get_queryset(self, request):
        qs = super(TaskAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(department=request.user.department)

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

    # 导入导出功能限制
    def get_export_formats(self):  # 该方法是限制格式为XLS
        formats = (
            base_formats.XLS,
        )
        return [f for f in formats if f().can_export()]

    def has_import_permission(self, request):  # 这是隐藏导入按钮，如果隐藏其他按钮也可以这样操作，
        if request.user.is_superuser:
            return True
        else:
            return False


# class TodoAdmin(admin.ModelAdmin):
class TodoAdmin(ImportExportModelAdmin):
    resource_class = TodoResources

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

    # 仅显示当前部门的工作包，除非为超管
    def get_queryset(self, request):
        qs = super(TodoAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(related_task__department=request.user.department)

    fieldsets = [
        (None, {
            'fields': [
                'related_task', 'todo_topic', 'todo_note', 'deadline', 'duty_group', 'main_executor', 'sub_executor',
                'predict_work', 'evaluate_factor',
            ],
            'description': 'aaa'
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
    list_per_page = 5  # 目的是取消自动分页，好像有bug
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

    # 导入导出功能限制
    def get_export_formats(self):  # 该方法是限制格式为XLS
        formats = (
            base_formats.XLS,
        )
        return [f for f in formats if f().can_export()]

    def has_import_permission(self, request):  # 这是隐藏导入按钮，如果隐藏其他按钮也可以这样操作，
        if request.user.is_superuser:
            return True
        else:
            return False

    # 增加批量操作按钮
    actions = ['bulk_action']

    def bulk_action(self, request, queryset):
        post = request.POST
        # 这里获取到数据后，可以做些业务处理
        # post中的_action 是方法名
        # post中 _selected 是选中的数据，逗号分割
        if not post.get('_selected'):
            return JsonResponse(data={
                'status': 'error',
                'msg': '请先选中数据！'
            })
        else:
            return JsonResponse(data={
                'status': 'success',
                'msg': '处理成功！'
            })

    # 显示的文本，与django admin一致
    bulk_action.short_description = '批量操作'
    # icon，参考element-ui icon与https://fontawesome.com
    bulk_action.icon = 'el-icon-files'

    # 指定element-ui的按钮类型，参考https://element.eleme.cn/#/zh-CN/component/button
    bulk_action.type = 'warning'

    # 给按钮追加自定义的颜色
    bulk_action.style = 'color:white;'

    # 指定为弹出层，这个参数最关键
    bulk_action.layer = {
        # 弹出层中的输入框配置

        # 这里指定对话框的标题
        'title': '弹出层输入框',
        # 提示信息
        'tips': '这个弹出对话框是需要在admin中进行定义，数据新增编辑等功能，需要自己来实现。',
        # 确认按钮显示文本
        'confirm_button': '确认提交',
        # 取消按钮显示文本
        'cancel_button': '取消',

        # 弹出层对话框的宽度，默认50%
        'width': '40%',

        # 表单中 label的宽度，对应element-ui的 label-width，默认80px
        'labelWidth': "80px",
        'params': [{
            # 这里的type 对应el-input的原生input属性，默认为input
            'type': 'input',
            # key 对应post参数中的key
            'key': 'name',
            # 显示的文本
            'label': '名称',
            # 为空校验，默认为False
            'require': True
        }, {
            'type': 'select',
            'key': 'type',
            'label': '类型',
            'width': '200px',
            # size对应elementui的size，取值为：medium / small / mini
            'size': 'small',
            # value字段可以指定默认值
            'value': '0',
            'options': [{
                'key': '0',
                'label': '收入'
            }, {
                'key': '1',
                'label': '支出'
            }]
        }, {
            'type': 'number',
            'key': 'money',
            'label': '金额',
            # 设置默认值
            'value': 1000
        }, {
            'type': 'date',
            'key': 'date',
            'label': '日期',
        }, {
            'type': 'datetime',
            'key': 'datetime',
            'label': '时间',
        }, {
            'type': 'rate',
            'key': 'star',
            'label': '评价等级'
        }, {
            'type': 'color',
            'key': 'color',
            'label': '颜色'
        }, {
            'type': 'slider',
            'key': 'slider',
            'label': '滑块'
        }, {
            'type': 'switch',
            'key': 'switch',
            'label': 'switch开关'
        }, {
            'type': 'input_number',
            'key': 'input_number',
            'label': 'input number'
        }, {
            'type': 'checkbox',
            'key': 'checkbox',
            # 必须指定默认值
            'value': [],
            'label': '复选框',
            'options': [{
                'key': '0',
                'label': '收入'
            }, {
                'key': '1',
                'label': '支出'
            }, {
                'key': '2',
                'label': '收益'
            }]
        }, {
            'type': 'radio',
            'key': 'radio',
            'label': '单选框',
            'options': [{
                'key': '0',
                'label': '收入'
            }, {
                'key': '1',
                'label': '支出'
            }, {
                'key': '2',
                'label': '收益'
            }]
        }]
    }


admin.site.register(models.Task, TaskAdmin)
admin.site.register(models.Todo, TodoAdmin)
