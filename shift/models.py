from django.db import models

DIVISION_TYPE = (
                (0,'未'),
                (1,'高校生'),
                (2,'大学1年'),
                (3,'大学2年'),
                (4,'大学3年'),
                (5,'大学4年'),
                (6,'大学院'),
                (7,'社会人')
              )

SHIFT_TYPE = (
                (0,'不参加'),
                (1,'AM'),
                (2,'PM'),
                (3,'MID'),
                (4,'FULL')
              )

class Member(models.Model):
    """メンバー情報 キーとなる名前と区分を設定"""
    name = models.CharField("氏名",max_length=15,unique=True)                       # 名前
    division = models.IntegerField("区分",default=0, choices=DIVISION_TYPE)         # 区分
    update_finality = models.DateTimeField(auto_now=True)                           # 更新日付

    # 名前
    def __str__(self):
        return self.name


class Shift(models.Model):
    """夏のシフトを管理する。名前をキーに設定。"""
    name = models.ForeignKey(Member, on_delete=models.CASCADE)              # 名前(外部キー)
    shift_date = models.DateField()                                         # シフト登録日付
    shift = models.IntegerField("シフト",default=0,choices=SHIFT_TYPE)      # シフト区分番号
    comment = models.CharField(max_length=200,null=True,blank=True)         # コメント(NULL可)
    morning = models.BooleanField("朝食", default=False)
    lunch = models.BooleanField("昼食", default=False)
    dinner = models.BooleanField("夜食", default=False)  

    class Meta:
        unique_together = (("name", "shift_date"),)                         # 名前と日付でユニークにする

    # 名前,日付
    def __str__(self):
        return str(self.name) + ':' + str(self.shift_date)

class Patrol(models.Model):
    """パトロール情報設定"""
    year = models.IntegerField("年",unique=True)                      # 区分
    pc_name = models.CharField("PC氏名",max_length=15)                # 名前
    start = models.IntegerField("パトロール開始日(7月)",default=1)         # 始まり
    end = models.IntegerField("パトロール最終日(8月)",default=31)          # 終わり
    update_finality = models.DateTimeField(auto_now=True)             # 更新日付
    notify_days = models.IntegerField("変更通知適用日数", default=-1)

    # 名前
    def __str__(self):
        return str(self.year)

