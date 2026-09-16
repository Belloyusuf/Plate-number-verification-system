from django import forms

from .alpr import ALPRService


# user login page
class LoginForm(forms.Form):
    username = forms.CharField(max_length=15 ,required=True)
    password = forms.CharField(widget=forms.PasswordInput ,required=True)


class ALPRUploadForm(forms.Form):
    image = forms.ImageField(required=True)
    model_name = forms.ChoiceField(choices=[(name, name) for name in ALPRService.get_available_models()], required=True)


