from django.conf.urls import url
from . import views

app_name = 'albums'

urlpatterns = [
    url(r'^$', views.AlbumView.as_view(), name='album'),
    url(r'^create$', views.AlbumCreateView.as_view(), name='album_add'),
    url(r'^photo/(?P<title>[0-9]+)$', views.PhotoView.as_view(), name='photo'),
    url(r'^photoadd/(?P<album_id>[0-9]+)$', views.PhotoUpload, name='photoadd'),
]
