from django.db import models

class Album(models.Model):
    """ベースとなるアルバム"""
    title = models.CharField("タイトル", max_length=50, unique=True, null=False, blank=False, db_index=True) 
    owner = models.CharField("作成者", max_length=20, default=0, null=False, blank=False)        
    created = models.DateTimeField(auto_now=True, db_index=True)                                             

    # タイトル
    def __str__(self):
        return self.title

class Photo(models.Model):
    """投稿された画像"""
    album = models.ForeignKey(Album, on_delete=models.CASCADE, db_index=True)           
    origin = models.CharField("画像パス", max_length=200, blank=True, null=True)
    thumbnail = models.CharField("サムネイルパス", max_length=200, null=True)
    width = models.IntegerField("幅", default=0)
    height = models.IntegerField("高さ", default=0)    
    editor = models.CharField("投稿者", max_length=20, default='guest')                      
    created = models.DateTimeField(auto_now=True)                                   

    def __str__(self):
        return self.album + ":" + self.path

class Comment(models.Model):
    """掲示板のようにAlbumに残すコメント"""
    album = models.ForeignKey(Album, on_delete=models.CASCADE, db_index=True)           
    editor = models.CharField("投稿者", max_length=20)                      
    comment = models.TextField("コメント")        
    created = models.DateTimeField(auto_now=True, db_index=True)                          
    ipaddress = models.GenericIPAddressField("投稿者IPアドレス")

    def __str__(self):
        return self.album + ":" + self.comment + ":" + self.editor