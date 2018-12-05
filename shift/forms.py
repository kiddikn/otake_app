from django import forms
from .models import Member, DIVISION_TYPE, Shift

class MemberForm(forms.ModelForm):
    """メンバー登録フォーム"""

    class Meta:
        model = Member
        fields = ("name", "division")
                 #   'division': forms.ChoiceField(attrs={
          #      'class': "form-control-file",
           #     'placeholder':'大竹太郎'
         #   }),
        #}

    name = forms.CharField(
        label='名前',
        max_length=15,
        required=True,
    )
    name.widget.attrs.update({'class': 'form-control','placeholder':'大竹太郎'})

    division = forms.ChoiceField(
        label='区分',
        choices=DIVISION_TYPE,
        widget=forms.Select,
        required=True
    )
    division.widget.attrs.update({'class': 'form-control form-group'})

