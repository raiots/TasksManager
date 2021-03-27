from import_export import resources

from .models import Todo, Task


class TodoResources(resources.ModelResource):
    class Meta:
        model = Todo


class TaskResources(resources.ModelResource):
    class Meta:
        model = Task
