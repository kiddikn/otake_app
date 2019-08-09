"""カレンダーを作成するためのモジュール."""
from calendar import (
    month_name, monthrange, LocaleHTMLCalendar, different_locale
)
import datetime
from django.conf import settings
from django.shortcuts import resolve_url
from .models import Shift


CalendarClass = LocaleHTMLCalendar

DAY_HTML = """
<td class="{0} back{1} shift_day" id="cal-{2}" month="{3}">
    <p class="dayname">{4}</p>
</td>
"""

SHIFT_WORK = """
<label>
    <input class='myshift' type='radio' value={0} name='shift:{1}' {2} onClick=\"col_{0}('cal-{1}')\">
        {3}{4}
    </input>
</label>
"""

POPUP_A_TAG = """
    <a href="{0}" class="btn-square" style="margin-bottom:5px;">シフトメンバー確認</a>
    <button type="submit" class="btn btn-primary">登録</button>
"""

class SpPatrolCalendar(CalendarClass):
    """スマートフォン表示に対応したカスタムカレンダー"""

    model = Shift

    def __init__(self, year, month,shift_reg = None, user_shift = None, shift_type = None, start=1,end=31, locale=None):
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
           単純に日付とシフトの色を設定する。

        引数:
            year: 年
            month: 月
            day: 日
            css_class: 日付部分のhtmlに与えたいcssのクラス

        返り値:
            日付部分のhtml。具体的にはDAY_HTMLに変数を埋め込んだ文字列
        """

        # 自分の登録状態を把握
        now = datetime.date(year, month, day)
        myshift_id = 0
        for me in self.user_shift:
            if me.shift_date == now:
                myshift_id = me.shift
                break

        return DAY_HTML.format(
            css_class,
            myshift_id,
            now,
            month,
            day
        )

    def formatreg(self, year, month, day):
        """シフトなど登録部分のフォームを作成。
        シフト登録対象日をクリックすることで表示するようにする。
        """

        # 登録されているシフトごとの集計人数の表示と合計人数を計算
        now = datetime.date(year, month, day)
        # 各シフトの人数を記憶
        shift_num={}
        for list in self.shift_reg:
            if list['shift_date'] == now:
                shift_num[list['shift']]=list['cnt']
        
        # 当日シフトメンバー表示用のaタグと登録ボタンを設定
        a_tag = POPUP_A_TAG.format(
            self.get_shift_member_url(year, month, day)
        )

        # 現在登録されているシフトをcheckにするため取得する
        myshift_id = 0
        comment=""
        for me in self.user_shift:
            if me.shift_date == now:
                myshift_id = me.shift
                # TODO:mealを取得

                # コメントデータを取得
                if me.comment is not None and me.comment!="":
                    comment = me.comment
                break
        
        # TODO:mealの状態に合わせてチェックボックスのチェック状態を設定する
        

        #登録用のフォームを作成
        shift_input='<div class="shift_reg_table month{}" id="reg-{}"><p class="myshiftday">{}<button type="button" class="close">&times;</button></p>'.format(month,now,day)
        shift_input+='<table class="form_all">'
        shift_input+='<tr>'
        shift_input+='<td class="form_half">'
        shift_input+='<div class="shift_reg">'
        shift_input+='<ul>'
        for stype in self.shift_type:
            shift_input+='<li class="list_item">'
            
            # シフトのチェック状態制御
            check = ''
            if stype[0] == myshift_id:
                check = "checked='checked'"
            
            # シフト登録済み人数の表示
            shift_disp_num=''
            if stype[1] in shift_num.keys() and shift_num[stype[1]]>0:
                shift_disp_num="({}人)".format(shift_num[stype[1]])

            # inputラジオボタンを設定
            shift_input+=SHIFT_WORK.format(
                        stype[0],
                        now,
                        check,
                        stype[1],
                        shift_disp_num
                    )
            shift_input+='</li>'
        shift_input+='</ul>'
        if len(shift_num.keys())>0:
            shift_input+="<p class='numexplain'>※()内は登録済み人数</p>"
        # shift_input+='<hr class="center">'
        shift_input+='</div>'
        shift_input+='</td>'
        shift_input+='<td class="form_half to_shift_member">'
        # shift_input+='<input type="checkbox" class="myshift" name={}>朝</input>'.format(now)
        # shift_input+='<input type="checkbox" class="myshift" name={}>昼</input>'.format(now)
        # shift_input+='<input type="checkbox" class="myshift" name={}>夜</input>'.format(now)
        shift_input+='<div class="form-group">'
        shift_input+='<label for="mycomment">コメント:</label>'
        shift_input+='<textarea class="form-control mycomment" name="comment:{}" rows="2" placeholder="送迎可。東京発18:00以降。など。" style="font-size:0.7rem;" maxlength="120">{}</textarea>'.format(now, comment)
        shift_input+='</div>'
        shift_input+=a_tag
        shift_input+='</td>'
        shift_input+='</tr>'
        shift_input+='</table>'
        shift_input+="</div>"
        return shift_input

    def formatday(self, day, weekday):
        """tableタグの日付部分のhtmlを作成する<td>...</td>."""
        if day == 0:
            return '<td class="noday" id="noday">&nbsp;</td>'  # day outside month
        elif day < self.start or self.end < day:
            return '<td class="{0}" id="noshift{1}" month="{1}"><p class="dayname">{2}</p></td>'.format(self.cssclasses[weekday],self.month,day)
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
        for week in self.monthdays2calendar(self.year, self.month):
            for (day, wd) in week:
                if day == 0:
                    continue
                elif day < self.start or self.end < day:
                    continue
                else:
                    a(self.formatreg(self.year,self.month,day))
        a('<div class="shift_reg_table month{0}" id="reg-noshift{0}"><p>パトロール期間ではありません<button type="button" class="close">&times;</button></p></div>'.format(self.month))
        a('\n')
        return ''.join(v)

