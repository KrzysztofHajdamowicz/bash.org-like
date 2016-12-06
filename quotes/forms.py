from django import forms
from .models import Quote

class AddQuoteForm(forms.ModelForm):

    class Meta:
        model = Quote
        fields = ('content', )