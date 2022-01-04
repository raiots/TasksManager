from django import template
from datetime import datetime

from dateutil.relativedelta import relativedelta

register = template.Library()


@register.filter(name='quarter_cate')
def quarter_cate(value, year_quarter):
    year_now = datetime.now().strftime('%Y')
    month = value.deadline.strftime('%m')
    year = value.deadline.strftime('%Y')
    month = int(month)
    # year = int(year)
    # year_now = int(year) 不知道为什么，如果转整数会把2021和2022认为相同
    # print(quarter)
    req_year = str(year_quarter[1])
    quarter = int(year_quarter[0])
    # 可能造成性能损失，每次数据库会调出符合“当年”的任务或工作包的全部任务下工作包，并逐个判断
    if year == req_year:
        if quarter == 1 and 1 <= month <= 3:
            return str(value) + '&#13;&#10;'

        elif quarter == 2 and 4 <= month <= 6:
            return str(value) + '&#13;&#10;'

        elif quarter == 3 and 7 <= month <= 9:
            return str(value) + '&#13;&#10;'

        elif quarter == 4 and 10 <= month <= 12:
            return str(value) + '&#13;&#10;'

        else:
            return ''
    else:
        return ''


@register.filter(name='last_month')
def last_month(value):
    curent_date = datetime.strptime(value, '%Y年%m月')
    last_date = curent_date - relativedelta(months=+1)
    last_month = last_date.strftime('%Y/%m')
    return last_month


@register.filter(name='next_month')
def next_month(value):
    curent_date = datetime.strptime(value, '%Y年%m月')
    next_date = curent_date + relativedelta(months=+1)
    next_month = next_date.strftime('%Y/%m')
    return next_month


@register.filter(name='this_month')
def this_month(value):
    curent_date = datetime.strptime(value, '%Y年%m月')
    return curent_date.strftime('%m')


@register.filter(name='last_year')
def last_year(value):
    curent_year = value[1]
    last_year = curent_year - 1
    return last_year


@register.filter(name='next_year')
def next_year(value):
    curent_year = value[1]
    next_year = curent_year + 1
    return next_year


@register.filter(name='this_year')
def this_year(value):
    curent_year = value[1]
    return curent_year