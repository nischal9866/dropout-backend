from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.forms import SetPasswordForm, PasswordResetForm
from .models import User, TeacherProfile, StudentProfile

class UserLoginForm(AuthenticationForm):
    """Form for user login"""
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username or Email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'password']

class TeacherRegistrationForm(UserCreationForm):
    """Form for teacher registration (by admin only)"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control'
    }))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    phone_number = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    employee_id = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    qualification = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 
                  'phone_number', 'employee_id', 'qualification', 
                  'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'teacher'
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        user.employee_id = self.cleaned_data['employee_id']
        user.qualification = self.cleaned_data['qualification']
        
        if commit:
            user.save()
            
            # Create teacher profile
            TeacherProfile.objects.create(
                user=user,
                department='General',  # Set default or make it dynamic
                subjects_taught=''
            )
        
        return user

class StudentRegistrationForm(UserCreationForm):
    """Form for student registration"""
    email = forms.EmailField(required=True)
    roll_number = forms.CharField(required=True)
    class_name = forms.CharField(required=True, label="Class")
    parent_phone = forms.CharField(required=True, label="Parent's Phone Number")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 
                  'roll_number', 'class_name', 'parent_phone', 
                  'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        user.email = self.cleaned_data['email']
        user.roll_number = self.cleaned_data['roll_number']
        user.class_name = self.cleaned_data['class_name']
        user.parent_phone = self.cleaned_data['parent_phone']
        
        if commit:
            user.save()
            
            # Create student profile
            StudentProfile.objects.create(
                user=user,
                guardian_name=self.cleaned_data['parent_phone'],
                guardian_relationship='Parent',
                emergency_contact=self.cleaned_data['parent_phone']
            )
        
        return user

class UserProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }