from django import forms
from .models import Album

class AlbumForm(forms.ModelForm):
    """アルバム登録フォーム"""

    class Meta:
        model = Album
        fields = ("title", "owner")

    title = forms.CharField(
        label='アルバムタイトル',
        max_length=50,
        required=True
    )
    title.widget.attrs.update({'class': 'form-control','placeholder':'20181007全日本大会や201808パトロールなど'})

    owner = forms.CharField(
        label='ユーザー名',
        max_length=20,
        required=True
    )
    owner.widget.attrs.update({'class': 'form-control form-group'})