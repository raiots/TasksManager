from import_export import resources

from .models import Todo, Task


class TodoResources(resources.ModelResource):
    class Meta:
        model = Todo
        fields = ('todo_topic', 'todo_note',	'deadline',	'duty_group__name', 'main_executor__real_name',
                  'sub_executor__real_name', 'sub_executor_count', 'related_task', 'predict_work',	'evaluate_factor',
                  'maturity', 'real_work', 'complete_note', 'quality_mark')


class TaskResources(resources.ModelResource):
    class Meta:
        model = Task
