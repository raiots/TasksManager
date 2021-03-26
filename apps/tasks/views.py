from django.contrib import auth, messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
import django.utils.timezone as timezone
from django.views import View
# Create your views here.
from apps.tasks.models import Todo, Task
from apps.tasks.forms import TodoForm
from apps.users.models import User


class IndexView(View):
    @method_decorator(login_required)
    def get(self, request):
        users = User.objects.filter(department=request.user.department)
        # points = []
        # point = User.objects.all()
        # for i in point:
        #     points.append(i)
        # points = User.objects.annotate(a=F('main_executor__evaluate_factor'))
        points = User.objects.annotate(a=Sum(F('main_executor__predict_work') * F('main_executor__evaluate_factor') + F('sub_executor__predict_work') * F('sub_executor__evaluate_factor')))
        context = {'users': users, 'points': points}
        return render(request, 'tasks/index.html', context)


class TodoListView(View):
    @method_decorator(login_required)
    def get(self, request, year=timezone.now().year, month=timezone.now().month):
        my_todo = Todo.objects.filter(main_executor=request.user, deadline__year=year, deadline__month=month)
        my_sub_todo = Todo.objects.filter(sub_executor=request.user, deadline__year=year, deadline__month=month)
        date = str(year) + '年' + str(month) + '月'
        context = {'my_todo': my_todo, 'my_sub_todo': my_sub_todo, 'date': date}
        return render(request, 'tasks/todolist.html', context)


class GroupTodoList(View):
    @method_decorator(login_required)
    def get(self, request, year=timezone.now().year, month=timezone.now().month):
        group_todo = Todo.objects.filter(main_executor__department=request.user.department, deadline__year=year,
                                         deadline__month=month).order_by('related_task_id', 'deadline')
        date = str(year) + '年' + str(month) + '月'
        context = {'group_todo': group_todo, 'date': date}
        return render(request, 'tasks/group_todolist.html', context)


class TaskListView(View):
    @method_decorator(login_required)
    def get(self, request):
        tasks = Task.objects.filter().order_by('task_id')
        context = {'tasks': tasks}
        return render(request, 'tasks/tasklist.html', context)

class UserLoginView(View):
    def get(self, request):
        return render(request, 'tasks/login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)
        if user:
            auth.login(request, user)
            messages.success(request, 'hh')
            return redirect('tasks:index')
        else:
            return redirect('tasks:index')

class UserLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('tasks:index')


class TodoEntryView(View):
    def get(self, request, pk):
        todo_detail = Todo.objects.get(id=pk)
        form = TodoForm(instance=todo_detail)
        context = {'todo_detail': todo_detail, 'form': form}
        return render(request, 'tasks/todo.html', context)

    def post(self, request, pk):
        todo_detail = Todo.objects.get(id=pk)
        form = TodoForm(instance=todo_detail, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('tasks:todolist')
            # return redirect('tasks:todo_detail', pk=pk)


class AboutView(View):
    def get(self, request):
        return render(request, 'tasks/about.html')