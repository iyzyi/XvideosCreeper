# XvideosCreeper

Xvideos爬虫🥰

5年前刚学没多久python的时候写过一版，[tonny0812/xvideos](https://github.com/tonny0812/xvideos)这个就是当时fork我的。可惜后来改成私有库了，就失去了fork关联。

重新再把当年的版本开源没意义，索性用[iyzyi/PornhubCreeper](https://github.com/iyzyi/PornhubCreeper)的框架再重构一版吧。

推荐搭配[iyzyi/VideoViewer: Pornhub Xvideos 本地视频浏览](https://github.com/iyzyi/VideoViewer)使用。

## 使用

1. 安装ffmpeg

2. 修改`config.py`中的配置

3. 在`xvideos.py`中，有两种调用方式：

   ```
   # 下载单个视频（指定一个URL）
   view_url = 'https://www.xvideos.com/videoxxxxxxxx/yyyyyyy'		# 旧版URL
   view_url = 'https://www.xvideos.com/video.xxxxxxxxxxx/yyyyyyy'	# 新版URL
   xd = XvideosDownloader(view_url = view_url)
   
   # 下载多个视频（指定一个TXT，其中一行对应一个URL）
   urls_txt = r'xvideos_urls.txt'
   xd = XvideosDownloader(urls_txt = urls_txt)
   ```

4. 下载成功后，会将视频号保存到`SAVED.txt`；下载时发现视频已失效，则将视频号保存到`INVALID.txt`；已知的新旧URL的映射关系会保存到`MAP.txt`。避免重复下载
5. 可通过`get_favorite_urls.py`来将收藏夹中所有的Xvideos视频URL提取到`xvideos_urls.txt`中。

