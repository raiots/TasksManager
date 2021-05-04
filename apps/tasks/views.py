import re
from copy import deepcopy

from django.contrib import auth, messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, FloatField, Count, Q
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
import django.utils.timezone as timezone
from django.views import View
# Create your views here.
from apps.tasks.models import Todo, Task
from apps.tasks.forms import TodoForm
from apps.users.models import User
from functools import reduce
import pandas as pd


class IndexView(View):
    @method_decorator(login_required)
    def get(self, request, year=timezone.now().year, month=timezone.now().month):
        basic_users = User.objects.filter(department=request.user.department).annotate(
            main_executor_count=Count('main_executor',
                                      filter=Q(main_executor__deadline__year=year, main_executor__deadline__month=month)
                                      , distinct=True),
            sub_executor_count=Count('sub_executor',
                                     filter=Q(sub_executor__deadline__year=year, sub_executor__deadline__month=month),
                                     distinct=True)
        ).values('id', 'real_name', 'main_executor_count', 'sub_executor_count')

        basic_users = [entry for entry in basic_users]
        basic_user_cal = {}
        for i in basic_users:
            basic_user_cal.update({i['id']: i})
        print(basic_user_cal)

        current_user = User.objects.filter(username=request.user.username).annotate(
            main_executor_count=Count('main_executor',
                                      filter=Q(main_executor__deadline__year=year, main_executor__deadline__month=month)
                                      , distinct=True),
            sub_executor_count=Count('sub_executor',
                                     filter=Q(sub_executor__deadline__year=year, sub_executor__deadline__month=month),
                                     distinct=True),
            pre_credit=Sum(
                F('main_executor__predict_work') * F('main_executor__evaluate_factor'),
                filter=Q(main_executor__deadline__year=year, main_executor__deadline__month=month),
                distinct=True,
                output_field=FloatField()
            ),
            real_credit=Sum(
                F('main_executor__real_work') * F('main_executor__evaluate_factor'),
                filter=Q(main_executor__deadline__year=year, main_executor__deadline__month=month),
                distinct=True,
                output_field=FloatField()
            )
        )

        department_cal = Todo.objects.filter(main_executor__department=request.user.department,
                                             deadline__year=year, deadline__month=month).aggregate(count=Count('id'),
                                                pre_total=Sum('predict_work'), real_total=Sum('real_work'), pre_avg=Sum('predict_work'), real_avg=Sum('real_work')).values()
        keys = ['count', 'pre_total', 'real_total', 'pre_avg', 'real_avg']
        temp = []
        for values in department_cal:
            print(values)
            temp.append(values)
        #TODO 解决部门tem无数据报错问题
        try:
            tem = [float(tem) for tem in temp]
            whole = dict(zip(keys, tem))
            pre_avg = {'pre_avg': float(whole['pre_avg'])/request.user.department.get_user_number}
            real_avg = {'real_avg': float(whole['real_avg']) / request.user.department.get_user_number}
            whole.update(pre_avg)
            whole.update(real_avg)
        except:
            whole = {}
            print('无数据')
        # print(whole)



        date = str(year) + '年' + str(month) + '月'

        # points = []
        # point = User.objects.all()
        # for i in point:
        #     points.append(i)
        # points = User.objects.annotate(a=F('main_executor__evaluate_factor'))
        # points = User.objects.annotate(a=Coalesce(Sum(F('main_executor__predict_work') * F('main_executor__evaluate_factor')) + Sum(F('sub_executor__predict_work') * F('sub_executor__evaluate_factor')), 0))
        # points = User.objects.annotate(a=Sum(F('main_executor__predict_work') * F('main_executor__evaluate_factor')), b=Sum(F('sub_executor__predict_work') * F('sub_executor__evaluate_factor')))
        # points = User.objects.annotate(a=Sum(F('main_executor__main_workload')))

        main_credit = User.objects.filter(department=request.user.department, ).annotate(
            pre_credit=Sum(
                F('main_executor__predict_work') * F('main_executor__evaluate_factor'),
                filter=Q(main_executor__deadline__year=year, main_executor__deadline__month=month),
                distinct=True,
                output_field=FloatField()
            ),
            real_credit=Sum(
                F('main_executor__real_work') * F('main_executor__evaluate_factor'),
                filter=Q(main_executor__deadline__year=year, main_executor__deadline__month=month),
                distinct=True,
                output_field=FloatField()
            )
        ).values('id', 'real_name', 'pre_credit', 'real_credit')
        main_credit = [entry for entry in main_credit]  # converts ValuesQuerySet into Python list

        sub_credit = User.objects.filter(department=request.user.department).annotate(
            pre_credit=Sum(
                (F('sub_executor__predict_work') * (1 - F('sub_executor__evaluate_factor')) / F(
                    'sub_executor__sub_executor_count')
                 ),
                filter=Q(sub_executor__deadline__year=year, sub_executor__deadline__month=month),
                output_field=FloatField()
            ),
            real_credit=Sum(
                (F('sub_executor__real_work') * (1 - F('sub_executor__evaluate_factor')) / F(
                    'sub_executor__sub_executor_count')
                 ),
                filter=Q(sub_executor__deadline__year=year, sub_executor__deadline__month=month),
                output_field=FloatField()
            )
        ).values('id', 'real_name', 'pre_credit', 'real_credit')
        sub_credit = [entry for entry in sub_credit]

        total_credit = main_credit + sub_credit
        print(total_credit)

        basic_user_credit = {}
        if total_credit:
            df = pd.DataFrame(total_credit)
            cols = ['id', 'real_name', 'pre_credit', 'real_credit']
            df = df.loc[:, cols]
            result = df.groupby(['id', ]).sum()
            cal_credit = result.T.to_dict('dict')
            # print(cal_credit)
            temp_credit = {}
            basic_user_credit = {}
            for key, values in cal_credit.items():
                # print(values['real_credit'])
                temp_credit['pre_credit'] = values['pre_credit']
                temp_credit['real_credit'] = values['real_credit']
                # print(temp_credit)
                basic_user_credit.update({key: temp_credit})
                # print(basic_user_credit)
                temp_credit = {}
            print(basic_user_credit)
        else:
            print("当前页Index无任何人员具有工作包")

        for key in basic_user_cal:
            basic_user_cal[key].update(basic_user_credit[key])
        print(basic_user_cal)



        # ids = []
        # person_list = []
        # for person in total_points:
        #     id = person["id"]
        #     temp = {}
        #     if id not in ids:
        #         ids.append(id)
        #         temp_list = filter(lambda x: x["id"] == person["id"], total_points)
        #         for i in temp_list:
        #             temp.update(i)
        #         person_list.append(temp)
        #     else:
        #         continue

        # for i in main_points:
        #     for key, value in i.items():

        # def sum_dict(a, b):
        #     temp = dict()
        #     # python3,dict_keys类似set； | 并集
        #     for key in a.keys() | b.keys():
        #         temp[key] = sum([d.get(key, 0) for d in (a, b)])
        #     return temp
        #
        # def test():
        #     # [a,b,c]列表中的参数可以2个也可以多个，自己尝试。
        #     return print(reduce(sum_dict, [a, b, c]))

        context = {'users_data': basic_user_cal, 'date': date, 'current_user': current_user, 'department': whole}
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
        tasks = Task.objects.filter(department=request.user.department).order_by('task_id')
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
