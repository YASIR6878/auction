from django import forms
from captcha.fields import CaptchaField

class ContactForm(forms.Form):
    username = forms.CharField()
    email = forms.EmailField()
    pass1 = forms.CharField(widget=forms.PasswordInput)
    pass2 = forms.CharField(widget=forms.PasswordInput)
    captcha = CaptchaField()
