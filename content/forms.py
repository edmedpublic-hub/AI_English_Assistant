from django import forms
from .models import SentenceAttempt

class SentenceAttemptForm(forms.ModelForm):
    class Meta:
        model = SentenceAttempt
        fields = ["student_id", "sentence"]
        widgets = {
            "student_id": forms.TextInput(attrs={"class": "form-control"}),
            "sentence": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        
from django import forms

class ComprehensionAttemptForm(forms.Form):
    student_id = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    answer = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )