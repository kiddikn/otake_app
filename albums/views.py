from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from .models import Album, Photo
from .forms import AlbumForm
from PIL import Image 
from django.contrib import messages

class AlbumView(ListView):
    """アルバム表示するビュー"""
    model = Album
    template_name = 'albums/album_list.html'

    def get_queryset(self):
        """タイトル名の降順"""
        return self.model.objects.order_by('-title')

class AlbumCreateView(CreateView):
    """アルバム追加"""
    model = Album
    form_class = AlbumForm
    template_name = 'albums/album_form.html'
    success_url = reverse_lazy('albums:album')

class PhotoView(ListView):
    """投稿された画像を表示するビュー"""
    model = Photo
    context_object_name = 'albums/photo_list'

    def get_queryset(self):
        """該当タイトルの画像一覧を返す"""
        title_id = self.kwargs.get('title')
        queryset = self.model.objects.filter(album_id=title_id)\
                                     .order_by('created')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) # はじめに継承元のメソッドを呼び出す
        
        title_id = self.kwargs.get('title')
        from django.shortcuts import get_object_or_404
        context["title"] = get_object_or_404(Album, pk=title_id) # 指定されたタイトルがない場合は404
        context["album_id"] = title_id
        return context

def PhotoUpload(request, album_id):
    """投稿された画像情報をDB登録・サムネイル作成"""
    if request.method != 'POST':
        pass

    # 登録するアルバムがない場合は処理しない(インスタンスは一回だけ取得)
    try:
        album = Album.objects.get(pk=album_id)
    except:
        messages.warning(request, '選択されたアルバムは存在しません。') 
        return redirect('albums:photo', album_id)
    
    err_list = []

    # アップロードされたそれぞれのファイルに対して登録処理
    for afile in request.FILES.getlist('files'):
        # アップロードファイルの保存先ファイル名
        original_url = get_image_path(album_id, str(afile))

        # アップロードされたファイルを移動
        from django.core.files.storage import default_storage
        default_storage.save(original_url, afile)

        # 画像チェック・EXIT情報削除
        from django.conf import settings
        org_fullpath = settings.MEDIA_ROOT + '/' + original_url   
        if not clean_up_image(org_fullpath):
            # ImageOpen出来ない場合は、次の画像に映る
            delete_file(org_fullpath)
            err_list.append(str(afile))
            continue
        
        # サムネイルファイル名作成
        from os import path
        folder, outfile = path.split(org_fullpath)
        thumb_filename = 'thumb-' + path.splitext(outfile)[0] + '.jpg'
        thumb_fullpath = folder + '/' + thumb_filename

        # サムネイル作成
        im = Image.open(org_fullpath)
        if not create_thumbnail(im, thumb_fullpath):
            delete_file(org_fullpath)
            delete_file(thumb_fullpath)
            err_list.append(str(afile))
            continue

        # photo設定  
        photo = Photo()
        photo.album = album         # アルバムID
        photo.origin = settings.MEDIA_URL + original_url 
        thumbdir,aaa = path.split(photo.origin)
        photo.thumbnail = thumbdir + '/' + thumb_filename
        photo.width, photo.height = im.size  
        photo.editor = request.POST.get('editor')   
        photo.save()
        
        # アクセス権付与
        from os import chmod
        chmod(org_fullpath, 0o644)
        chmod(thumb_fullpath, 0o644)

    if err_list:
        messages.error(request, '次の画像アップロードに失敗しました。・' + '・'.join(err_list))
    else:
        messages.success(request, '画像のアップロードに成功しました!') 
    return redirect('albums:photo', album_id)

def clean_up_image(org_filepath, THUMBNAIL_WIDTH=800,THUMBNAIL_HEIGHT=600):
    """
    画像を整備してサイズを整えて保存。
    →iPhoneの使用を考慮し、Exif情報からOrientationを取得し回転。
    　セキュリティも考慮してExif情報を削除しておく。
    画像以外の場合はFalseを返す。
    """
    try:
        img = Image.open(org_filepath)       # 開けたら画像(拡張子偽造チェック)

        # 先に画像を縮小
        if img.width > THUMBNAIL_WIDTH or img.height > THUMBNAIL_HEIGHT:
            img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.ANTIALIAS)

        # EXIF情報から傾きを取得
        exif = img._getexif()
        orientation = exif.get(0x112, 1) if exif else 1
        rotate, reverse = get_exif_rotation(orientation)
        
        # 新画像作成用にデータ取得
        data = img.getdata()
        mode = img.mode
        size = img.size
        img.close()     # 後ほど上書きするためclose
        
        # imageの再作成(Exif情報の削除)
        with Image.new(mode, size) as dst:
            dst.putdata(data)
            if reverse == 1:
                dst = ImageOps.mirror(dst)
            if rotate != 0:
                dst = dst.rotate(rotate, expand=True)            
            dst.save(org_filepath)

        return True
    except:
        return False

def create_thumbnail(im, dst_file):
    """サムネイル作成"""
    im_thumb = expand2square(im, (0, 0, 0)).resize((250, 250), Image.LANCZOS)
    try:
        if im_thumb.mode != "RGB":
            im_thumb = im_thumb.convert("RGB") # RGBモードに変換する
        im_thumb.save(dst_file, quality=95)    
    except:
        return False
    return True

def expand2square(pil_img, background_color):
    """
    元の解像度を保ちつつ正方形にする。余白は引数で指定された色でぬりつぶす
    """
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        result = Image.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, (width - height) // 2))
        return result
    else:
        result = Image.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, ((height - width) // 2, 0))
        return result

def get_image_path(album_id, filename):
    """
    アップロードしたファイルの保存先とファイル名を定義する
    ファイル名：photos/アルバムID/yyyyMMdd_00001.拡張子
    """
    prefix = 'photos/'
    folder_dir = prefix + str(album_id) + '/'  # photos/1(アルバムのID)/...

    from datetime import datetime
    newfilename = datetime.today().strftime('%Y%m%d') + '_'

    # ファイル名の連番を振る(今あるファイル名末尾の連番を増やしていく)
    from glob import glob
    from os import path, makedirs
    from django.conf import settings

    # 保存先フォルダーの生成
    folder_full_dir = settings.MEDIA_ROOT + '/' + folder_dir
    if not path.exists(folder_full_dir):
        makedirs(folder_full_dir)
    
    # 連番作成処理
    l = [path.basename(r) for r in glob(folder_full_dir + newfilename + '*')]
    num = 1
    if(len(l) > 0):
        # すでに同名規則のファイル名があれば取得してカウントアップ(5桁)
        l.sort()
        lastfile,ext = path.splitext(l[-1])
        lastid = lastfile.replace(newfilename, '')
        num = int(lastid) + 1      
    newfilename = newfilename + '{:0=5}'.format(num)

    extension = path.splitext(filename)[-1]
    return folder_dir + newfilename + extension

def get_exif_rotation(orientation_num):
    """
    ExifのRotationの数値から、回転する数値と、ミラー反転するかどうかを取得する
    return 回転度数,反転するか(0 1)
    # 参考: https://qiita.com/minodisk/items/b7bab1b3f351f72d534b
    """
    if orientation_num == 1:
        return 0, 0
    if orientation_num == 2:
        return 0, 1
    if orientation_num == 3:
        return 180, 0
    if orientation_num == 4:
        return 180, 1
    if orientation_num == 5:
        return 270, 1
    if orientation_num == 6:
        return 270, 0
    if orientation_num == 7:
        return 90, 1
    if orientation_num == 8:
        return 90, 0

def delete_file(full_path):
    """ファイルを削除"""
    from os import path, remove
    if path.exists(full_path):
        try:
            remove(full_path)
        except:
            pass