from django import forms
from .models import Todo

class LoginForm(forms.Form):
    username = forms.CharField(error_messages={'required': '用户名不能为空'})
    password = forms.CharField()
    remember = forms.BooleanField(required=False)

class TodoForm(forms.ModelForm):
    class Meta:
        model = Todo
        fields = ['maturity', 'complete_note']
        labels ={'text': ''}
        widgets = {'row': '3'}