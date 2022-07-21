import re
from collections import defaultdict, Counter
from copy import deepcopy

from django.contrib import auth, messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, FloatField, Count, Q
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
import django.utils.timezone as timezone
from django.views import View
from django.db import connection
# Create your views here.
from apps.tasks.models import Todo, Task
from apps.tasks.forms import TodoForm
from apps.users.models import User
from . import my_query
from functools import reduce
import pandas as pd

import decimal


class IndexView(View):
    @method_decorator(login_required)
    def get(self, request, year=None, month=None):
        # 搞成了！！！ 当月份更改时自动变更首页显示的月份！ 其实就是用的上面那个链接的方法，之前不知道为啥没去用
        #  https://stackoverflow.com/questions/63072235/django-localdate-doesnt-return-correct-date
        #  https://stackoverflow.com/questions/13225890/django-default-timezone-now-saves-records-using-old-time
        #  https://stackoverflow.com/questions/38237777/django-timezone-now-vs-timezone-now
        if year is None:
            year = timezone.now().year
        if month is None:
            month = timezone.now().month
        #TODO 部门不用部门下用户累加
        # 建立username和真实姓名的对应字典，并在工作量计算完成后插入结果集
        user_info = User.objects.filter(department=request.user.department)\
            .values_list('username', 'real_name')
        user_name = {}
        for user in user_info:
            user_name[user[0]] = user[1]
        # print(user_name)

        # 以用户表查询，按用户列出所参与承办、协办任务，并在之后按用户名分组合并。
        main_credit = User.objects.filter(department=request.user.department,
                                          main_executor__deadline__year=year, main_executor__deadline__month=month)\
            .annotate(main_count=Count('main_executor'))\
            .order_by('username')\
            .values('username', 'main_executor', 'main_executor__predict_work', 'main_executor__real_work',
                    'main_executor__evaluate_factor', 'main_count')  # 这里的annotate不知会不会有问题

        sub_count = Todo.objects.filter(sub_executor__department=request.user.department,
                                        deadline__year=year, deadline__month=month) \
            .annotate(sub_count=Count('sub_executor')).values('id', 'sub_count')
        sub_credit = User.objects.filter(department=request.user.department,
                                         sub_executor__deadline__year=year, sub_executor__deadline__month=month) \
            .order_by('username') \
            .values('username', 'real_name', 'sub_executor', 'sub_executor__predict_work', 'sub_executor__real_work',
                    'sub_executor__evaluate_factor')

        # 构建工作包id对应协办人人数的字典
        sub_exe_count = {}
        for i in sub_count:
            key = i['id']
            value = i['sub_count']
            sub_exe_count[key] = value
        # print(sub_exe_count)

        # 计算每个承办任务的预计、实际工作量，并插入字典
        for i in main_credit:
            i['main_pre_cal'] = i['main_executor__predict_work'] * i['main_executor__evaluate_factor']
            i['main_real_cal'] = i['main_executor__real_work'] * i['main_executor__evaluate_factor']
            # print(i)
            # print(str(i['sub_executor']))

        # 将协办任务对应的人数插入，计算每个协办任务的预计、实际工作量，并插入字典
        for i in sub_credit:
            sub_todo_id = i['sub_executor']
            i['sub_exe_count'] = sub_exe_count[sub_todo_id]
            i['sub_pre_cal'] = i['sub_executor__predict_work'] * (1 - i['sub_executor__evaluate_factor']) / i['sub_exe_count']
            i['sub_real_cal'] = i['sub_executor__real_work'] * (1 - i['sub_executor__evaluate_factor']) / i['sub_exe_count']
            i['sub_count'] = 1  # 用于帮助累加程序计算每个用户的协办任务数量， sub_exe_count会返回此协办任务的协办人数，在累加时导致计算错误
            # print(i)
            # print(str(i['sub_executor']))

        # 用于按用户名合并任务，会对指定字段进行累加，类似GROUP BY(SUM)，但会丢失无需计算的部分，因此之前需要单独构建姓名字典
        def solve(dataset, group_by_key, sum_value_keys):
            dic = defaultdict(Counter)
            for item in dataset:
                key = item[group_by_key]
                vals = {k: item[k] for k in sum_value_keys}
                dic[key].update(vals)
            return dic
        main_credit = solve(main_credit, 'username', ['main_pre_cal', 'main_real_cal', 'main_count'])
        main_credit = dict(main_credit)
        sub_credit = solve(sub_credit, 'username', ['sub_pre_cal', 'sub_real_cal', 'sub_count'])
        sub_credit = dict(sub_credit)

        # 按用户名合并承办与协办任务字典
        total_credit = deepcopy(main_credit)
        for key in sub_credit.keys():
            if key in total_credit:
                total_credit[key].update(sub_credit[key])
            else:
                total_credit[key] = sub_credit[key]

        # print(total_credit['admin']['sub_pre_cal'])
        # 根据字典内容，计算总工作量
        for key, value in total_credit.items():
            # print(value)
            value['pre_cal'] = value['sub_pre_cal'] + value['main_pre_cal']
            value['real_cal'] = value['sub_real_cal'] + value['main_real_cal']
            value['real_name'] = user_name[key]
        # total_credit = dict(main_credit.items() + sub_credit.items())
        # for value in sub_credit.values():
        #     dict(value)
        # print(sub_credit)
        #
        # new_pair = {}
        # for doc, tab in sub_credit.items():
        #     new_pair[doc] = {}
        #     for word, freq in tab.items():
        #         new_pair[doc][word] = freq
        # print(new_pair)
        # return HttpResponse(str(main_credit)+str(sub_credit))

        # 若total_credit为空，不进行以下操作，避免err
        if total_credit:
            # 暂时解决当该用户当月无任务时，total_credit中不包含该用户的用户名，导致Key Error
            try:
                current_user = total_credit[request.user.username]
            except:
                current_user = {}

            # 累加该部门各个用户的工作量，计算部门工作量
            department_cal = {}
            temp_pre = []
            depart_pre, depart_real, depart_count = 0, 0, 0
            for username, value in total_credit.items():
                print(username)
                print(value['pre_cal'])
                depart_pre = depart_pre + value['pre_cal']
                depart_real = depart_real + value['real_cal']
                depart_count = depart_count + value['main_count']
                temp_pre.append(value['pre_cal'])
                department_cal['pre_cal'] = depart_pre
                department_cal['real_cal'] = depart_real
                department_cal['depart_count'] = depart_count
            department_cal['pre_avg'] = department_cal['pre_cal'] / len(total_credit)
            department_cal['real_avg'] = department_cal['real_cal'] / len(total_credit)
        else:
            department_cal, current_user = {}, {}


        # 计算实际工作量、完成质量
        def cal_method(main_list, sub_list, user_name):
            # print(main_list, sub_list, user_name)

            # sub_credit = sub_list
            # main_credit = main_list

            total_data = []
            season = 1
            # 分别计算每个季度的工作量、评价
            for main_credit, sub_credit in zip(main_list, sub_list):
                # TODO 对于完成质量的核算，先对评价求和，再除以已评价的承办任务数
                # for i in main_credit:
                # print(i['main_executor__quality_mark__mark_value__mark_value'])
                # print(main_credit)
                quality_dict = {}
                for i in main_credit:
                    # 先赋值0，避免前端显示个[]
                    quality_dict[i['username']] = []
                    if i['main_executor__quality_mark__mark_value__mark_value'] != None:
                        quality_dict[i['username']].append(i['main_executor__quality_mark__mark_value__mark_value'])

                # TEST
                for i in sub_credit:
                    # 先赋值0，避免前端显示个[]
                    quality_dict[i['username']] = []
                    if i['sub_executor__quality_mark__mark_value__mark_value'] != None:
                        quality_dict[i['username']].append(i['sub_executor__quality_mark__mark_value__mark_value'])


                for key, value in quality_dict.items():
                    if value:
                        quality_dict[key] = sum(value) / len(value)
                # print(quality_dict)

                main_credit = solve(main_credit, 'username',
                                    ['main_pre_cal', 'main_real_cal', 'main_count', 'main_executor__evaluate_factor'])
                main_credit = dict(main_credit)
                sub_credit = solve(sub_credit, 'username', ['sub_pre_cal', 'sub_real_cal', 'sub_count'])
                sub_credit = dict(sub_credit)

                # 按用户名合并承办与协办任务字典
                total_credit = deepcopy(main_credit)
                for key in sub_credit.keys():
                    if key in total_credit:
                        total_credit[key].update(sub_credit[key])
                    else:
                        total_credit[key] = sub_credit[key]

                # print(total_credit['admin']['sub_pre_cal'])
                # 根据字典内容，计算总工作量
                for key, value in total_credit.items():
                    # print(value)
                    value['pre_cal'] = value['sub_pre_cal'] + value['main_pre_cal']
                    value['real_cal'] = value['sub_real_cal'] + value['main_real_cal']
                    value['real_name'] = user_name[key]
                    value['season'] = season

                    # 由于不计算协办任务，quality_dict会有空值情况
                    try:
                        value['quality'] = quality_dict[key]
                    except:
                        value['quality'] = 0

                for value in total_credit.values():
                    # print(value)
                    real_cal_season = "real_cal_" + str(season)
                    value[real_cal_season] = value.pop("real_cal")
                    quality_season = "quality_" + str(season)
                    value[quality_season] = value.pop("quality")
                # print(total_credit)
                total_data.append(total_credit)
                # print(season)
                season += 1

                # new_credit = []
                # for item in total_credit:
                #     for key, value in item.items():
            # print(total_data, season)
            dd = defaultdict(list)
            for d in total_data:  # you can list as many input dicts as you want here
                for key, value in d.items():
                    dd[key].append(value)
            # print(dd)
            return dd
        user_info = User.objects.filter(department=request.user.department) \
            .values_list('username', 'real_name')
        user_name = {}
        for user in user_info:
            user_name[user[0]] = user[1]

        work_cal = User.objects.filter(department=request.user.department, main_executor__deadline__year=2021) \
            .order_by('main_executor__deadline').values('main_executor__todo_topic', 'main_executor__deadline')

        # 以用户表查询，按用户列出所参与承办、协办任务，并在之后按用户名分组合并。
        main_credit = User.objects.filter(department=request.user.department,
                                          main_executor__deadline__year=year) \
            .annotate(main_count=Count('main_executor')) \
            .order_by('username') \
            .values('username', 'main_executor', 'main_executor__predict_work', 'main_executor__real_work',
                    'main_executor__evaluate_factor', 'main_executor__maturity', 'main_executor__quality_mark__mark_value__mark_value', 'main_executor__deadline', 'main_count')  # 这里的annotate不知会不会有问题

        sub_count = Todo.objects.filter(sub_executor__department=request.user.department,
                                        deadline__year=year) \
            .annotate(sub_count=Count('sub_executor')).values('id', 'sub_count')
        sub_credit = User.objects.filter(department=request.user.department,
                                         sub_executor__deadline__year=year) \
            .order_by('username') \
            .values('username', 'real_name', 'sub_executor', 'sub_executor__predict_work', 'sub_executor__real_work',
                    'sub_executor__evaluate_factor', 'sub_executor__maturity', 'sub_executor__quality_mark__mark_value__mark_value', 'sub_executor__deadline')

        # 构建工作包id对应协办人人数的字典
        sub_exe_count = {}
        for i in sub_count:
            key = i['id']
            value = i['sub_count']
            sub_exe_count[key] = value
        # print(sub_exe_count)

        # 计算每个承办任务的预计、实际工作量、成熟度，并插入字典
        for i in main_credit:
            # 将成熟度由百分数转小数，以便其后与其他变量计算 eg. 50% -> 0.5
            print('ad', i['main_executor__maturity'])
            # 临时补丁，解决用户将成熟度设置为空的问题，后面的协办任务也改了，记得改回去
            # TODO 数据库中设置成熟度为非空
            try:
                i['main_executor__maturity'] = decimal.Decimal(float(i['main_executor__maturity'].strip('%')) / 100)
            except:
                i['main_executor__maturity'] = decimal.Decimal(float(0) / 100)
            # print(i['main_executor__maturity'])
            i['main_pre_cal'] = i['main_executor__predict_work'] * i['main_executor__evaluate_factor'] * i['main_executor__maturity']
            i['main_real_cal'] = i['main_executor__real_work'] * i['main_executor__evaluate_factor'] * i['main_executor__maturity']
            # print(i)
            # print(str(i['sub_executor']))

        # 将协办任务对应的人数插入，计算每个协办任务的预计、实际工作量，并插入字典
        for i in sub_credit:
            sub_todo_id = i['sub_executor']
            i['sub_exe_count'] = sub_exe_count[sub_todo_id]
            try:
                i['sub_executor__maturity'] = decimal.Decimal(float(i['sub_executor__maturity'].strip('%')) / 100)
            except:
                i['sub_executor__maturity'] = decimal.Decimal(float(0) / 100)
            i['sub_pre_cal'] = i['sub_executor__predict_work'] * (1 - i['sub_executor__evaluate_factor']) / i['sub_exe_count'] * i['sub_executor__maturity']
            i['sub_real_cal'] = i['sub_executor__real_work'] * (1 - i['sub_executor__evaluate_factor']) / i['sub_exe_count'] * i['sub_executor__maturity']
            i['sub_count'] = 1  # 用于帮助累加程序计算每个用户的协办任务数量， sub_exe_count会返回此协办任务的协办人数，在累加时导致计算错误
            # print(i)
            # print(str(i['sub_executor']))



        main_Q1st, main_Q2nd, main_Q3th, main_Q4th = [], [], [], []
        for i in main_credit:
            # print(i['main_executor__deadline'].month)
            deadline_month = i['main_executor__deadline'].month
            if 1 <= deadline_month <= 3:
                main_Q1st.append(i)
            elif 4 <= deadline_month <= 6:
                main_Q2nd.append(i)
            elif 7 <= deadline_month <= 9:
                main_Q3th.append(i)
            elif 10 <= deadline_month <= 12:
                main_Q4th.append(i)
        # print(Q1st, Q2nd, Q3th, Q4th)

        sub_Q1st, sub_Q2nd, sub_Q3th, sub_Q4th = [], [], [], []
        for i in sub_credit:
            # print(i['main_executor__deadline'].month)
            deadline_month = i['sub_executor__deadline'].month
            if 1 <= deadline_month <= 3:
                sub_Q1st.append(i)
            elif 4 <= deadline_month <= 6:
                sub_Q2nd.append(i)
            elif 7 <= deadline_month <= 9:
                sub_Q3th.append(i)
            elif 10 <= deadline_month <= 12:
                sub_Q4th.append(i)

        main_list = [main_Q1st, main_Q2nd, main_Q3th, main_Q4th]
        sub_list = [sub_Q1st, sub_Q2nd, sub_Q3th, sub_Q4th]
        stat_result = cal_method(main_list, sub_list, user_name)

        stat = {}
        for key, value in stat_result.items():
            stat[key] = {}
            for j in value:
                stat[key]['real_name'] = j['real_name']
                season = str(j['season'])
                real_cal_season = 'real_cal_' + season
                quality_season = 'quality_' + season
                stat[key][real_cal_season] = j[real_cal_season]
                stat[key][quality_season] = j[quality_season]
        print(stat_result)

        # return HttpResponse(result.items())
        # 为页面提供日期信息
        date = str(year) + '年' + str(month) + '月'

        # return HttpResponse(str(total_credit) + '\n' + str(department_cal))
        context = {'date': date, 'users_data': total_credit, 'department_cal': department_cal,
                   'current_user': current_user, 'stat': stat}
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
    def get(self, request, year=timezone.now().year): # TODO 把timezone.now().year写在后面要用year替换的地方是否可以解决
        tasks = Task.objects.filter(department=request.user.department, deadline__year=year).order_by('task_id')\
                 | Task.objects.filter(department=request.user.department, related_task__deadline__year=year).order_by('task_id')
        tasks = tasks.distinct()
        # tasks = Task.objects.filter(Q(department=request.user.department), Q(deadline__year=year) | Q(related_task__deadline__year=year)).order_by('task_id')
        # 使用‘或’，找出工作包/年度任务的截止日期在今年的年度任务。后面还要做一个筛选，以达到只显示本年度的工作包
        year_quarter = {'1': [1, year], '2': [2, year], '3': [3, year], '4': [4, year]}

        context = {'tasks': tasks, 'year_quarter': year_quarter}
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
