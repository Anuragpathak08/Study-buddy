from django import forms
from django.contrib.auth.models import User
from .models import User_Profile

class UserProfileChangeForm(forms.ModelForm):
    firstname = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    lastname = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    avatar = forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control-file'}), required=False)
    bio = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    location = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), max_length=100, required=False)

    class Meta:
        model = User_Profile
        fields = ('avatar', 'bio', 'location')  # We exclude firstname and lastname since they're handled separately
