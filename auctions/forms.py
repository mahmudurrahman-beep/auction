from django import forms
from .models import Listing, Comment

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'description', 'starting_bid', 'image_url', 'category']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a clear, concise title (e.g. Vintage Rolex Submariner)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the item: condition, history, dimensions, defects, etc.'
            }),
            'starting_bid': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Starting bid (numeric, e.g. 100.00)',
                'step': '0.01',
                'min': '0.01'
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional image URL (https://...)'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Friendly empty label for the category select
        self.fields['category'].empty_label = "Select a category"
        # Make sure starting_bid is required and has sensible validation
        self.fields['starting_bid'].required = True
        self.fields['title'].required = True
        self.fields['description'].required = True


class BidForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your bid (e.g. 150.00)',
            'step': '0.01',
            'min': '0.01'
        })
    )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add a comment...'
            }),
        }
