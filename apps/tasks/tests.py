import decimal

from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions import TruncMonth
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
from collections import defaultdict, Counter, ChainMap
from copy import deepcopy


# 用于按用户名合并任务，会对指定字段进行累加，类似GROUP BY(SUM)，但会丢失无需计算的部分，因此之前需要单独构建姓名字典
def solve(dataset, group_by_key, sum_value_keys):
    dic = defaultdict(Counter)
    for item in dataset:
        key = item[group_by_key]
        vals = {k: item[k] for k in sum_value_keys}
        dic[key].update(vals)
    return dic

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
            quality_dict[i['username']] = []
            if i['main_executor__quality_mark__mark_value__mark_value'] != None:
                quality_dict[i['username']].append(i['main_executor__quality_mark__mark_value__mark_value'])

        for key, value in quality_dict.items():
            if value:
                quality_dict[key] = sum(value) / len(value)
        # print(quality_dict)

        main_credit = solve(main_credit, 'username', ['main_pre_cal', 'main_real_cal', 'main_count', 'main_executor__evaluate_factor'])
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


class TestView(View):
    def get(self, request, year=2021, month=7):
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

        # 计算每个承办任务的预计、实际工作量，并插入字典
        for i in main_credit:
            # 将成熟度由百分数转小数，以便其后与其他变量计算 eg. 50% -> 0.5
            i['main_executor__maturity'] = decimal.Decimal(float(i['main_executor__maturity'].strip('%')) / 100)
            # print(i['main_executor__maturity'])
            i['main_pre_cal'] = i['main_executor__predict_work'] * i['main_executor__evaluate_factor'] * i['main_executor__maturity']
            i['main_real_cal'] = i['main_executor__real_work'] * i['main_executor__evaluate_factor'] * i['main_executor__maturity']
            # print(i)
            # print(str(i['sub_executor']))

        # 将协办任务对应的人数插入，计算每个协办任务的预计、实际工作量，并插入字典
        for i in sub_credit:
            sub_todo_id = i['sub_executor']
            i['sub_exe_count'] = sub_exe_count[sub_todo_id]
            i['sub_executor__maturity'] = decimal.Decimal(float(i['sub_executor__maturity'].strip('%')) / 100)
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
        result = cal_method(main_list, sub_list, user_name)
        print(result)
        stat = {}
        for key, value in result.items():
            stat[key] = {}
            for j in value:
                stat[key]['real_name'] = j['real_name']
                season = str(j['season'])
                real_cal_season = 'real_cal_' + season
                quality_season = 'quality_' + season
                stat[key][real_cal_season] = j[real_cal_season]
                stat[key][quality_season] = j[quality_season]
                print(j)
        print(stat)

        return HttpResponse(stat)
        # return render(request, 'tasks/index.html', context)
