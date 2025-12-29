from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")
        widgets = {
            "email": forms.EmailInput(attrs={"required": True}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "avatar")
        widgets = {
            "email": forms.EmailInput(attrs={"required": True}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        # ✅ bật unique email (khuyến nghị)
        if email and User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("Email này đã được sử dụng.")
        return email
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ["first_name", "last_name", "email"]:
            self.fields[name].widget.attrs.update({"class": "form-control"})
        self.fields["avatar"].widget.attrs.update({"class": "form-control"})
