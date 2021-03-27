from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from . import models


class MyUserAdmin(UserAdmin):
    # @staticmethod
    # def group_list(self):
    #     return ', '.join([a.name for a in self.groups.all()])
    # group_list.short_description = '部门/组'

    list_display = ('username', 'real_name', 'staff_id', 'department')
    fieldsets = (
        (None, {'fields': ('username', 'password', 'real_name', 'staff_id', 'department')}),
        ('权限', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
    )


class MyGroupAdmin(GroupAdmin):
    pass


class DepartmentAdmin(admin.ModelAdmin):
    pass


class TaskPropertyAdmin(admin.ModelAdmin):
    list_display = (
        'task_property', 'own_department'
    )

    def get_queryset(self, request):
        qs = super(TaskPropertyAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(own_department=request.user.department)


class QualityMarkAdmin(admin.ModelAdmin):
    list_display = (
        'mark_name',
        'mark_value'
    )
    def mark_value(self):
        return self.mark_value
    mark_value.short_description = 'ss'

    # # 仅显示当前部门的任务属性，除非为超管
    # def get_queryset(self, request):
    #     qs = super(QualityMarkAdmin, self).get_queryset(request)
    #     if request.user.is_superuser:
    #         return qs
    #     else:
    #         return qs.filter(department=request.user.department)


class MarkValueAdmin(admin.ModelAdmin):
    # def get_queryset(self, request):
    #     qs = super(MarkValueAdmin, self).get_queryset(request)
    #     if request.user.is_superuser:
    #         return qs
    #     else:
    #         return qs.filter(department=request.user.department)
    pass

admin.site.register(models.User, MyUserAdmin)
admin.site.register(models.MyGroup, MyGroupAdmin)
admin.site.register(models.MarkValue, MarkValueAdmin)
admin.site.register(models.Department)
admin.site.register(models.QualityMark, QualityMarkAdmin)
admin.site.register(models.TaskProperty, TaskPropertyAdmin)
admin.site.unregister(Group)