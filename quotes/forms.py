from django import forms
from .models import Quote


class AddQuoteForm(forms.ModelForm):
    # Honeypot field — hidden from real users, filled by bots
    website = forms.CharField(required=False, widget=forms.HiddenInput, label="")

    class Meta:
        model = Quote
        fields = ("content",)

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Bot detected.")
        return ""
