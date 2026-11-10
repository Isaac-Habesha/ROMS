from django import forms
from .models import Meal, MealCategory

INPUT_TW = 'w-full px-3.5 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500'
SELECT_TW = 'w-full px-3.5 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500'
TEXTAREA_TW = 'w-full px-3.5 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500'
CHECKBOX_TW = 'w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500'


class MealCategoryForm(forms.ModelForm):
    class Meta:
        model = MealCategory
        fields = ['name', 'description', 'display_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_TW}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_TW, 'rows': 3}),
            'display_order': forms.NumberInput(attrs={'class': INPUT_TW}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_TW}),
        }


class MealForm(forms.ModelForm):
    class Meta:
        model = Meal
        fields = ['category', 'name', 'description', 'price', 'image', 'is_available', 'preparation_time_minutes']
        widgets = {
            'category': forms.Select(attrs={'class': SELECT_TW}),
            'name': forms.TextInput(attrs={'class': INPUT_TW}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_TW, 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': INPUT_TW, 'step': '0.01'}),
            'image': forms.FileInput(attrs={'class': 'w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'}),
            'is_available': forms.CheckboxInput(attrs={'class': CHECKBOX_TW}),
            'preparation_time_minutes': forms.NumberInput(attrs={'class': INPUT_TW}),
        }
