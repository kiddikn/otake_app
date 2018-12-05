import datetime
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.db.models import Count
from django.utils.safestring import mark_safe
from django.views.generic import ListView, CreateView, UpdateView, TemplateView, FormView, View
from .calendarlib import PatrolCalendar
from .forms import MemberForm
from .models import Patrol,Member,Shift,SHIFT_TYPE

class MemberView(ListView):
    """メンバー表示するビュー"""
    model = Member
    template_name = 'shift/member_list.html'

class MemberCreateView(CreateView):
    """メンバー追加"""
    model = Member
    form_class = MemberForm
    template_name = 'shift/member_form.html'
    success_url = reverse_lazy('shift:member')

class MemberUpdateView(UpdateView):
    """メンバー区分更新"""
    model = Member
    form_class = MemberForm
    template_name = "shift/member_form.html"
    success_url = reverse_lazy('shift:member')

class ShiftMemberView(ListView):
    """スケジュールの一覧ビュー.
    できればここでシフト画像の表示とか登録したい。
    """

    model = Shift
    template_name = "shift/shift_member.html"

    def get_date(self):
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')

        return  datetime.datetime(year=int(year), month=int(month), day=int(day))

    def get_queryset(self):
        """その日付のスケジュールを返す."""
        date = self.get_date()
        queryset = self.model.objects.filter(shift_date=date)\
                                     .exclude(shift=0)\
                                     .order_by('shift')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) # はじめに継承元のメソッドを呼び出す
        context["shift_now"] = "{0:%Y年%m月%d日のシフト}".format(self.get_date())
        return context

class ShiftCreateView(TemplateView):
    """カレンダーにてシフトを登録する"""
    model = Shift
    template_name = 'shift/calendar.html'

    def get_calendar(self, *args, **kwagrs):
        return PatrolCalendar(*args, **kwagrs)

    def get_context_data(self, *args, **kwargs):
        """カレンダーオブジェクトをcontextに追加する."""
        year = self.kwargs.get('year')
        user = self.kwargs.get('u_id')

        # ユーザー未指定の場合
        #if user is None:
        #    print('error')
        #    return


        # 年を未指定の場合は現在の年
        #if year is None:
        #    year = datetime.datetime.now()
        start=1
        end=31
        pat_conf = Patrol.objects.filter(year=year)[0]

        ########################################################
        # 人数集計
        ########################################################
        shift_num = self.model.objects.filter(shift_date__year=year)\
                                      .exclude(shift = 0)\
                                      .values('shift_date','shift')\
                                      .annotate(cnt=Count(1))
        for query in shift_num:
            query['shift'] = self.model(shift=query['shift']).get_shift_display()

        ########################################################
        # 7月カレンダーの表示
        ########################################################
        # データの取得(パトロール用なので手間を省くため7,8月only)
        queryset7 = self.model.objects.filter(
            name_id=user, shift_date__year=year, shift_date__month=7
        )
        month7_calendar = self.get_calendar(int(year),7,shift_num,queryset7,SHIFT_TYPE,start=pat_conf.start)
        month7_calendar_html = month7_calendar.formatmonth()

        ########################################################
        # 8月カレンダーの表示
        ########################################################
        queryset8 = self.model.objects.filter(
            name_id=user, shift_date__year=year, shift_date__month=8
        )
        month8_calendar = self.get_calendar(int(year),8,shift_num,queryset8,SHIFT_TYPE,end=pat_conf.end)
        month8_calendar_html = month8_calendar.formatmonth()

        # mark_safeでhtmlがエスケープされないようにする
        context = super().get_context_data(*args, **kwargs)
        context['calendar7'] = mark_safe(month7_calendar_html)
        context['calendar8'] = mark_safe(month8_calendar_html)
        context['shift_num'] = shift_num
        context['user'] = user

        return context

def ShiftReg(request):
    """カレンダーにてシフトを登録する"""
    if request.method == "POST":
        # u_id→ユーザーモデルを取る
        user = request.POST['user']
        member = Member.objects.get(id=user)

        for k,v in request.POST.items():
            if k == 'csrfmiddlewaretoken' or k == 'user':
                continue
            if v == '0' or v == 0:
                Shift.objects.filter(name=user, shift_date=k).delete()

            else:
                shiftdata,created = Shift.objects.get_or_create(name=member, shift_date=k)
                shiftdata.shift = v
                shiftdata.save()
            now = datetime.datetime.strptime(k, '%Y-%m-%d')

        return redirect(reverse_lazy('shift:shift_view', kwargs={'u_id':user,'year':now.year}))
    else:
        pass
