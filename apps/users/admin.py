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

class QualityMarkAdmin(admin.ModelAdmin):
    list_display = (
        'mark_name',
        'mark_value'
    )

admin.site.register(models.User, MyUserAdmin)
admin.site.register(models.MyGroup, MyGroupAdmin)
admin.site.register(models.MarkValue)
admin.site.register(models.Department)
admin.site.register(models.QualityMark, QualityMarkAdmin)
admin.site.register(models.TaskProperty, TaskPropertyAdmin)
admin.site.unregister(Group)