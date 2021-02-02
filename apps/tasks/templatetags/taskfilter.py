from django import template
from datetime import datetime

from dateutil.relativedelta import relativedelta

register = template.Library()


@register.filter(name='quarter_cate')
def quarter_cate(value, quarter):
    month = value.deadline.strftime('%m')
    month = int(month)
    quarter = int(quarter)

    if quarter == 1 and 1 <= month <= 3:
        return value

    elif quarter == 2 and 4 <= month <= 6:
        return value

    elif quarter == 3 and 7 <= month <= 9:
        return value

    elif quarter == 4 and 10 <= month <= 12:
        return value

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