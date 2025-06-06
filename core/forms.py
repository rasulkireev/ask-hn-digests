from allauth.account.forms import LoginForm, SignupForm
from django import forms

from core.models import Profile
from core.utils import DivErrorList


class CustomSignUpForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_class = DivErrorList


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_class = DivErrorList


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    class Meta:
        model = Profile
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile.save()
        return profile


class SummarizeHNDiscussionForm(forms.Form):
    discussion_ids = forms.CharField(
        label="Hacker News Discussion IDs",
        help_text="Enter one or more discussion IDs, separated by commas. E.g. 12345,67890",
        widget=forms.TextInput(attrs={"placeholder": "e.g. 12345,67890"})
    )


class SendNewsletterForm(forms.Form):
    summary_ids = forms.CharField(
        label="Summary IDs",
        help_text="Enter one or more HNDiscussionSummary IDs, separated by commas. E.g. 1,2,3",
        widget=forms.TextInput(attrs={"placeholder": "e.g. 1,2,3"})
    )
