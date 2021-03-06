from django.urls import path
from apps.tasks import views

app_name = 'tasks'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('todolist/', views.TodoListView.as_view(), name='todolist'),
    path('todolist/<int:year>/<int:month>/', views.TodoListView.as_view(), name='todolist_month'),
    path('group_todolist/', views.GroupTodoList.as_view(), name='group_todolist'),
    path('group_todolist/<int:year>/<int:month>/', views.GroupTodoList.as_view(), name='group_todolist_month'),
    path('todo/<int:pk>/', views.TodoEntryView.as_view(), name='todo_detail'),
    path('tasklist/', views.TaskListView.as_view(), name='tasklist'),
    path('about/', views.AboutView.as_view(), name='about'),
]
