from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from .models import *
from django.contrib.gis.geos import Point
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

class InternRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_intern = True
        
        if commit:
            user.save()
        return user

class ProfileCompletionForm(forms.ModelForm):
    class Meta:
        model = Intern
        fields = ['department', 'phone_number', 'organization']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organization'].queryset = Organization.objects.all()
        
    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        
        # Remove any whitespace or special characters that might have been added
        phone_number = ''.join(filter(str.isdigit, phone_number))
        
        # Check if the number starts with 254 and has exactly 12 digits (254 + 9)
        if not (phone_number.startswith('+254') and len(phone_number) == 12):
            raise forms.ValidationError(
                "Phone number must start with country code +254 followed by 9 digits (e.g., 254712345678)"
            )
            
        return phone_number


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'address', 'geofence_radius']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'geofence_radius': forms.NumberInput(attrs={'min': 10}),
        }
    
    def clean_geofence_radius(self):
        radius = self.cleaned_data['geofence_radius']
        if radius < 10:
            raise forms.ValidationError("Geofence radius must be at least 10 meters")
        return radius
    
    def save(self, commit=True):
        organization = super().save(commit=False)
        if organization.location_source == 'geocode' and organization.address:
            try:
                geolocator = Nominatim(user_agent="org_locator")
                location = geolocator.geocode(organization.address)
                if location:
                    organization.location = Point(location.longitude, location.latitude)
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                logger.error(f"Geocoding failed: {str(e)}")
                # You might want to handle this differently
        
        if commit:
            organization.save()
        return organization


class EmailForm(forms.Form):
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'
        })
    )

class OTPForm(forms.Form):
    otp = forms.CharField(
        label='Verification Code',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123456',
            'autocomplete': 'off'
        })
    )