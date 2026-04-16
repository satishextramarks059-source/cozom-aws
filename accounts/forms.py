from django import forms
from .models import ContactMessage
from .models import SubscriptionPlan

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'your@email.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200',
                'placeholder': '+1 (555) 123-4567'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Subject of your message'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Your message...',
                'rows': 5
            }),
        }


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = [
            'name', 'user_type', 'monthly_price', 'half_yearly_discount', 'yearly_discount',
            'receiver_qr', 'receiver_banking_name', 'description', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-select'}),
            'monthly_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'half_yearly_discount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'yearly_discount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'receiver_banking_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required in the form layer except boolean (checkbox can't be required)
        for fname, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                # set sensible default for create view
                if self.instance is None or not getattr(self.instance, 'pk', None):
                    field.initial = True
                field.required = False
            else:
                field.required = True

    def clean_receiver_qr(self):
        file = self.cleaned_data.get('receiver_qr')
        # When editing, allow leaving QR empty (keep existing)
        if not file:
            if self.instance and getattr(self.instance, 'pk', None) and getattr(self.instance, 'receiver_qr', None):
                return self.instance.receiver_qr
            raise forms.ValidationError('Receiver QR is required.')

        valid_ext = ['.png', '.jpg', '.jpeg']
        name = getattr(file, 'name', '')
        if not any(name.lower().endswith(ext) for ext in valid_ext):
            raise forms.ValidationError('Invalid file type. Only png, jpg, jpeg allowed.')
        return file