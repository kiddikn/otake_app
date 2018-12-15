from django.conf.urls import url
from . import views

app_name = 'albums'

urlpatterns = [
    url(r'^$', views.AlbumView.as_view(), name='album'),
    url(r'^create$', views.AlbumCreateView.as_view(), name='album_add'),
    url(r'^update/(?P<pk>\d+)$', views.AlbumUpdateView.as_view(), name="album_update"),
    url(r'^photo/(?P<title>[0-9]+)$', views.PhotoView.as_view(), name='photo'),
    url(r'^photoadd/(?P<album_id>[0-9]+)$', views.PhotoUpload, name='photoadd'),
    url(r'^delete/(?P<album_id>[0-9]+)/(?P<pk>\d+)$', views.PhotoDeleteView.as_view(), name='delete'),
    url(r'^delist/(?P<album_id>[0-9]+)$', views.PhotoDeleteListView.as_view(), name='del_list')
]
