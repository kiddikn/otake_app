from django.conf.urls import url
from . import views

app_name = 'shift'

urlpatterns = [
    url(r'^$', views.MemberView.as_view(), name='member'),
    url(r'^create$', views.MemberCreateView.as_view(), name='member_add'),
    url(r'^update/(?P<pk>\d+)$', views.MemberUpdateView.as_view(), name="member_update"),
    url(r'^schedule_create/(?P<year>[0-9]+)/(?P<u_id>[0-9]+)$', views.ShiftCreateView.as_view(), name="shift_view"),
    url(r'^shift_member/(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)$',views.ShiftMemberView.as_view(),name='shift_member'),
    url(r'^shift_reg$', views.ShiftReg, name='shift_reg'),
]
