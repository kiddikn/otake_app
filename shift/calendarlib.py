"""カレンダーを作成するためのモジュール."""
from calendar import (
    month_name, monthrange, LocaleHTMLCalendar, different_locale
)
import datetime
from django.conf import settings
from django.shortcuts import resolve_url
from .models import Shift
#import locale


#if hasattr(settings, 'CALENDAR_LOCALE'):
CalendarClass = LocaleHTMLCalendar
#else:
#    CalendarClass = HTMLCalendar

DAY_HTML = """
<td class="{0} shift_day">
    {1}
    <div id="{2}" class="back{3}" style="padding-left:10px;">{4}</div>
    <div class="hogehoge">{5}</div>
</td>
"""

SHIFT_WORK = "<label class='myshift'><input class='myshift' type='radio' value={0} name='{1}' {2} onClick=\"col_{0}('{1}')\">{3}</input></label>"

SCHEDULE_LINK_AND_NUM = """
<a href="{0}">
    <span class="badge badge-primary">+{1}</span>
</a>
"""

POPUP_A_TAG = """
    <a href="javascript:void(0);"
    class='square_btn'
    onclick="window.open('{0}','subwin','width=500,height=500');">
        >> {1}
    </a>
"""

class PatrolCalendar(CalendarClass):
    """Bootstrap4対応したカスタムカレンダー."""

    model = Shift

    def __init__(self, year, month,shift_reg = None, user_shift = None, shift_type = None, start=1,end=31, locale=None):
        #locale.setlocale(locale.LC_ALL, "")
        if CalendarClass is LocaleHTMLCalendar:
            super().__init__(6, 'ja_JP')
        else:
            super().__init__(6)
        self.year = year
        self.month = month
        self.shift_reg = shift_reg
        self.user_shift = user_shift
        self.shift_type = shift_type
        self.start=start
        self.end=end

    def get_shift_member_url(self, year, month, day):
        """スケジュール一覧ページのURLを返す."""
        return resolve_url(
            'shift:shift_member',
            year=year, month=month, day=day,
        )

    def create_month_day(self, year, month, day, css_class):
        """月間カレンダーの日付部分のhtmlを作成する.

        引数:
            year: 年
            month: 月
            day: 日
            css_class: 日付部分のhtmlに与えたいcssのクラス

        返り値:
            日付部分のhtml。具体的にはDAY_HTMLに変数を埋め込んだ文字列
        """

        # 登録されているシフトごとの集計と合計人数を表示
        now = datetime.date(year, month, day)
        shift_detail = ''
        shift_sum = 0
        a_tag = day
        for list in self.shift_reg:
            if list['shift_date'] == now:
                shift_detail += '</br>■{}→{}人'.format(list['shift'],list['cnt'])
                shift_sum += list['cnt']
        # シフト登録されている場合、合計とメンバーリストへのリンクを作成
        if shift_detail != '':
            shift_detail += '</br>【{}人】'.format(shift_sum)
            # 日付クリックで詳しいメンバー表示させる
            a_tag = POPUP_A_TAG.format(
                self.get_shift_member_url(year, month, day),
                day,
            )

        # 自分の登録状態を把握
        myshift_id = 0
        for me in self.user_shift:
            if me.shift_date == now:
                myshift_id = me.shift
                break

        # 登録用のフォームを作成
        shift_input=''
        for stype in self.shift_type:
            check = ''
            if stype[0] == myshift_id:
                check = "checked='checked'"
            shift_input+=SHIFT_WORK.format(
                        stype[0],
                        now,
                        check,
                        stype[1]
                    )

        return DAY_HTML.format(
            css_class,
            a_tag,
            now,
            myshift_id,
            shift_input,
            shift_detail
        )

    def formatday(self, day, weekday):
        """tableタグの日付部分のhtmlを作成する<td>...</td>."""
        if day == 0:
            return '<td class="noday">&nbsp;</td>'  # day outside month
        elif day < self.start or self.end < day:
            return '<td class="{}">{}</td>'.format(self.cssclasses[weekday],day)
        else:
            day_html = self.create_month_day(
                self.year, self.month, day,
                self.cssclasses[weekday]
            )
            return day_html

    def formatmonthname(self, withyear=True):
        """月間カレンダーの一番上、タイトル部分を作成する."""
        if CalendarClass is LocaleHTMLCalendar:
            with different_locale(self.locale):
                s = month_name[self.month]
                if withyear:
                    s = '%s年 %s' % (self.year,s)
        else:
            s = month_name[self.date.month]
            if withyear:
                s = '%s年 %s' % (self.year, s)
        html = '<tr><th colspan="7" class="month">{} シフト登録</th></tr>'
        return html.format(s)

    def formatmonth(self, withyear=True):
        """月のカレンダーを作成する."""
        v = []
        a = v.append
        a('<table class="month table table-bordered">')
        a('\n')
        a(self.formatmonthname(withyear=withyear))
        a('\n')
        a(self.formatweekheader())
        a('\n')
        for week in self.monthdays2calendar(self.year, self.month):
            a(self.formatweek(week))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)

