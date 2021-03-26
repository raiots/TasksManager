from django import forms
from .models import Todo

class LoginForm(forms.Form):
    username = forms.CharField(error_messages={'required': '用户名不能为空'})
    password = forms.CharField()
    remember = forms.BooleanField(required=False)


class TodoForm(forms.ModelForm):
    required_css_class = 'required'

    class Meta:
        model = Todo
        fields = ['maturity', 'real_work', 'complete_note']
        labels ={'text': ''}
        widgets = {'rows': '3'}


        # TODO 数据不可为空