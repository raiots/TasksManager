from django.urls import path, include
import debug_toolbar
from apps.tasks import views, tests
from TasksManager import settings

app_name = 'tasks'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:year>/<int:month>/', views.IndexView.as_view(), name='index_month'),
    path('test/', tests.TestView.as_view(), name='test'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('todolist/', views.TodoListView.as_view(), name='todolist'),
    path('todolist/<int:year>/<int:month>/', views.TodoListView.as_view(), name='todolist_month'),
    path('group_todolist/', views.GroupTodoList.as_view(), name='group_todolist'),
    path('group_todolist/<int:year>/<int:month>/', views.GroupTodoList.as_view(), name='group_todolist_month'),
    path('todo/<int:pk>/', views.TodoEntryView.as_view(), name='todo_detail'),
    path('tasklist/', views.TaskListView.as_view(), name='tasklist'),
    path('tasklist/<int:year>/', views.TaskListView.as_view(), name='tasklist_year'),
    path('about/', views.AboutView.as_view(), name='about'),
]
#
# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns = [
#         path('__debug__/', include(debug_toolbar.urls)),
#     ] + urlpatterns

