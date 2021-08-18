from django import forms
from .models import Todo


class LoginForm(forms.Form):
    username = forms.CharField(error_messages={'required': '用户名不能为空'})
    password = forms.CharField()
    remember = forms.BooleanField(required=False)


# TODO 数据不可为空
class TodoForm(forms.ModelForm):
    required_css_class = 'required'

    # (confused by Form & ModelForm https://stackoverflow.com/questions/2303268/djangos-forms-form-vs-forms-modelform)
    # maturity = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), choices=(
    #     ('0%', '0%'),
    #     ('10%', '10%'),
    #     ('50%', '50%'),
    #     ('90%', '90%'),
    #     ('100%', '100%')
    # ))
    # real_work = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    # sub_executor = forms.MultipleChoiceField(widget=forms.SelectMultiple(attrs={'class': 'form-control'}))

    class Meta:
        model = Todo
        fields = ['maturity', 'real_work', 'sub_executor', 'evaluate_factor', 'complete_note']
        widgets = {'complete_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
                   # 'evaluate_factor': forms.NumberInput(attrs={'class': 'form-control'}),
                   }

    def __init__(self, *args, **kwargs):
        super(TodoForm, self).__init__(*args, **kwargs)
        # self.fields['sub_executor'].widget.attrs['class'] = 'form-control'
        fields = ['maturity', 'real_work', 'sub_executor', 'evaluate_factor', 'complete_note']
        for i in fields:
            self.fields[i].widget.attrs['class'] = 'form-control'
