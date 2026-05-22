from django import forms


class SummarizeHNDiscussionForm(forms.Form):
    discussion_ids = forms.CharField(
        label="Hacker News Discussion IDs",
        help_text="Enter one or more discussion IDs, separated by commas. E.g. 12345,67890",
        widget=forms.TextInput(attrs={"placeholder": "e.g. 12345,67890"}),
    )


class SendNewsletterForm(forms.Form):
    summary_ids = forms.CharField(
        label="Summary IDs",
        help_text="Enter one or more HNDiscussionSummary IDs, separated by commas. E.g. 1,2,3",
        widget=forms.TextInput(attrs={"placeholder": "e.g. 1,2,3"}),
    )
