from django import forms
from .models import ClientNote


class ClientNoteForm(forms.ModelForm):
    class Meta:
        model = ClientNote
        fields = ['title', 'content', 'note_type', 'priority', 'is_private', 'is_resolved', 'follow_up_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título descriptivo de la nota...',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe el contenido de la nota...',
                'required': True
            }),
            'note_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_private': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_resolved': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'follow_up_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make fields required
        self.fields['title'].required = True
        self.fields['content'].required = True
        
        # Add help text
        self.fields['title'].help_text = 'Un título descriptivo para identificar la nota'
        self.fields['content'].help_text = 'Describe detalladamente el contenido de la nota'
        self.fields['note_type'].help_text = 'Clasifica la nota según su propósito'
        self.fields['priority'].help_text = 'Establece la prioridad de la nota'
        self.fields['is_private'].help_text = 'Solo visible para ti'
        self.fields['is_resolved'].help_text = 'Marcar si la nota ha sido resuelta o atendida'
        self.fields['follow_up_date'].help_text = 'Fecha opcional para dar seguimiento' 