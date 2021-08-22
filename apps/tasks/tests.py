from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.test import TestCase

# Create your tests here.
from django.db.models import Sum, F, FloatField, Count, Q

from django.utils import timezone
from django.views import View

from apps.users.models import User
from apps.tasks.models import Todo
import pandas as pd
from collections import defaultdict, Counter
from copy import deepcopy


class TestView(View):
    def get(self, request, year=2021, month=7):
        # sub_credit = User.objects.filter(department=request.user.department).annotate(
        #     pre_credit=Sum(
        #         (F('sub_executor__predict_work') * (1 - F('sub_executor__evaluate_factor')) / F(
        #             'sub_executor__sub_executor_count')
        #          ),
        #         filter=Q(sub_executor__deadline__year=year, sub_executor__deadline__month=month),
        #         output_field=FloatField()
        #     ),
        #     real_credit=Sum(
        #         (F('sub_executor__real_work') * (1 - F('sub_executor__evaluate_factor')) / F(
        #             'sub_executor__sub_executor_count')
        #          ),
        #         filter=Q(sub_executor__deadline__year=year, sub_executor__deadline__month=month),
        #         output_field=FloatField()
        #     )
        # ).values('id', 'real_name', 'pre_credit', 'real_credit')
        # sub_credit = [entry for entry in sub_credit]

        # 建立username和真实姓名的对应字典，并在工作量计算完成后插入结果集
        user_info = User.objects.filter(department=request.user.department)\
            .values_list('username', 'real_name')
        user_name = {}
        for user in user_info:
            user_name[user[0]] = user[1]
        # print(user_name)

        # 以用户表查询，按用户列出所参与承办、协办任务，并在之后按用户名分组合并。
        main_credit = User.objects.filter(department=request.user.department)\
            .annotate(main_count=Count('main_executor'))\
            .order_by('username')\
            .values('username', 'main_executor', 'main_executor__predict_work', 'main_executor__real_work',
                    'main_executor__evaluate_factor', 'main_count')  # 这里的annotate不知会不会有问题

        sub_count = Todo.objects.filter(sub_executor__department=request.user.department) \
            .annotate(sub_count=Count('sub_executor')).values('id', 'sub_count')
        sub_credit = User.objects.filter(department=request.user.department) \
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
        total_credit = deepcopy(main_credit)

        # 按用户名合并承办与协办任务字典
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

        current_user = total_credit[request.user.username]
        print(current_user)

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

        # 为页面提供日期信息
        date = str(year) + '年' + str(month) + '月'

        # return HttpResponse(str(total_credit) + '\n' + str(department_cal))
        context = {'date': date, 'users_data': total_credit, 'department_cal': department_cal,
                   'current_user': current_user}
        return render(request, 'tasks/index.html', context)
