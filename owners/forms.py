from django import forms

# user login page
class LoginForm(forms.Form):
    username = forms.CharField(max_length=15 ,required=True)
    password = forms.CharField(widget=forms.PasswordInput ,required=True)


