import datetime
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.db.models import Count
from django.utils.safestring import mark_safe
from django.views.generic import ListView, CreateView, UpdateView, TemplateView, FormView, View
from collections import OrderedDict
from .calendarlib import PatrolCalendar
from .spcalendarlib import SpPatrolCalendar
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
                                     .order_by('shift')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) # はじめに継承元のメソッドを呼び出す
        context["shift_now"] = "{0:%Y年%m月%d日のシフト}".format(self.get_date())
        return context

class AllShiftMemberView(TemplateView):
    """全スケジュールの一覧ビュー.
    """

    model = Shift
    template_name = "shift/all_shift_member.html"

    def _get_start_date(self):
        year = self.kwargs.get('year')
        return  datetime.datetime(year=int(year), month=7, day=1)

    def _get_end_date(self):
        year = self.kwargs.get('year')
        return  datetime.datetime(year=int(year), month=8, day=31)

    def get_context_data(self, *args, **kwargs):
        """その日付のスケジュールを返す."""
        start = self._get_start_date()
        end = self._get_end_date()
        queryset = self.model.objects.filter(shift_date__range = [start,end])\
                                     .order_by('shift_date','shift','name_id')
        allshift=OrderedDict()
        for query in queryset:
            if query.shift_date not in allshift:
                allshift[query.shift_date]=[]    
            allshift[query.shift_date].append(query)

        context = super().get_context_data(*args, **kwargs)
        context['allshift'] = allshift
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
        try:
            pat_conf = Patrol.objects.filter(year=year)[0]
            start=pat_conf.start
            end=pat_conf.end
        except:
            pass

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
        month7_calendar = self.get_calendar(int(year),7,shift_num,queryset7,SHIFT_TYPE,start=start)
        month7_calendar_html = month7_calendar.formatmonth()

        ########################################################
        # 8月カレンダーの表示
        ########################################################
        queryset8 = self.model.objects.filter(
            name_id=user, shift_date__year=year, shift_date__month=8
        )
        month8_calendar = self.get_calendar(int(year),8,shift_num,queryset8,SHIFT_TYPE,end=end)
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
    # POST以外は対象外
    if request.method != "POST":
        return

    # u_id→ユーザーモデルを取る
    user = request.POST['user']
    member = Member.objects.get(id=user)

    # POSTデータを収集
    reg_info={}
    for k,v in request.POST.items():
        if k == 'csrfmiddlewaretoken' or k == 'user' or ":" not in k:
            continue
        
        reg_type,date=k.split(":")
        if date not in reg_info.keys():
            shiftdata,created = Shift.objects.get_or_create(name=member, shift_date=date)
            reg_info[date]=shiftdata

        if reg_type == "shift":
            reg_info[date].shift = v
        elif reg_type == "comment":
            reg_info[date].comment = v.strip()
        now = datetime.datetime.strptime(date, '%Y-%m-%d')

    # 収集データをDB登録
    for regdate,regdata in reg_info.items():
        # TODO:データがあるかないかの判定をmodelに移譲
        if (regdata.shift!='0' and regdata.shift!=0) or (regdata.comment is not None and regdata.comment!=""):
            regdata.save()
        else:
            regdata.delete()

    return redirect(reverse_lazy('shift:shift_view', kwargs={'u_id':user,'year':now.year}))

class SpShiftCreateView(TemplateView):
    """カレンダーにてシフトを登録する"""
    model = Shift
    template_name = 'shift/sp/calendar.html'

    def get_calendar(self, *args, **kwagrs):
        return SpPatrolCalendar(*args, **kwagrs)

    def get_context_data(self, *args, **kwargs):
        """カレンダーオブジェクトをcontextに追加する."""
        year = self.kwargs.get('year')
        user = self.kwargs.get('u_id')

        # 開始・終了日付を設定
        start=1
        end=31
        try:
            # 管理画面でパトロール期間を定義されている場合は、その範囲で作成
            pat_conf = Patrol.objects.filter(year=year)[0]
            start=pat_conf.start
            end=pat_conf.end
        except:
            pass

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
        month7_calendar = self.get_calendar(int(year),7,shift_num,queryset7,SHIFT_TYPE,start=start)
        month7_calendar_html = month7_calendar.formatmonth()

        ########################################################
        # 8月カレンダーの表示
        ########################################################
        queryset8 = self.model.objects.filter(
            name_id=user, shift_date__year=year, shift_date__month=8
        )
        month8_calendar = self.get_calendar(int(year),8,shift_num,queryset8,SHIFT_TYPE,end=end)
        month8_calendar_html = month8_calendar.formatmonth()

        # mark_safeでhtmlがエスケープされないようにする
        context = super().get_context_data(*args, **kwargs)
        context['calendar7'] = mark_safe(month7_calendar_html)
        context['calendar8'] = mark_safe(month8_calendar_html)
        context['shift_num'] = shift_num
        context['user'] = user

        return context