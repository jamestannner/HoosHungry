from django import forms
from .models import Restaurant, RestaurantRequest, Report, Review
from django.forms import inlineformset_factory


class RestaurantRequestForm(forms.ModelForm):

    corresponding_restaurant = forms.ModelChoiceField(
        queryset=Restaurant.objects.all(),
        required=False,
        empty_label="New Restaurant",
        label="Restaurant to Change"
    )

    class Meta:
        model = RestaurantRequest
        fields = ['corresponding_restaurant', 'name', 'address', 'latitude', 'longitude', 'contact_info', 'menu_text']
        labels = {
            'name': 'Proposed Name',
            'address': 'Proposed Address',
            'latitude': 'Proposed Latitude',
            'longitude': 'Proposed Longitude',
            'contact_info': 'Proposed Contact Info',
            'menu_text': 'Proposed Menu Text'
        }
        widgets = {
            'menu_text': forms.Textarea(attrs={'rows': 4, 'cols': 50}),
        }
        error_messages = {
            'latitude': {
                'min_value': 'Latitude must be between -90 and 90',
                'max_value': 'Latitude must be between -90 and 90',
            },
            'longitude': {
                'min_value': 'Longitude must be between -180 and 180',
                'max_value': 'Longitude must be between -180 and 180',
            }
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['restaurant', 'report_type', 'rating']
        labels = {
            'report_type': 'Report Type',
            'restaurant': 'Restaurant',
            'rating': 'Rating (1-5)',
        }
        error_messages = {
            'rating': {
                'min_value': 'Rating must be at least 1',
                'max_value': 'Rating must be at most 5',
            }
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['restaurant', 'review_text', 'rating']
        widgets = {
            'review_text': forms.Textarea(attrs={'rows': 4, 'cols': 50}),
        }

        labels = {
            'restaurant': 'Restaurant',
            'review_text': 'Your Review',
            'rating': 'Rating (1-5)',
        }

        error_messages = {
            'rating': {
                'min_value': 'Rating must be at least 1',
                'max_value': 'Rating must be at most 5',
            }
        }