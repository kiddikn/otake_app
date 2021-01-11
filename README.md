## 大竹 S.L.S.C.専用アプリケーション

### アプリケーション

- 監視救助活動中のシフトおよび食事の管理
- アルバム

### アプリケーションのローカルでの起動

python のバージョンと site-package のバージョンを合わせる

```shell
$ python manage.py runserver
```

### 管理外ファイル

以下のファイルは設定ファイルで環境依存するので[別リポジトリ](https://github.com/kiddikn/otake_app_settings)で管理

- settings.py
- wsgi.py

### production サイト

https://otake-slsc.org/patrol/shift
