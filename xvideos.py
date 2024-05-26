import config
from requests_manage import RequestManager
from m3u8_downloader import M3U8Downloader
from file_downloader import FileDownloader
from progress_bar import ProgressBar
import re, json, html, os, time, shutil


class XvideosDownloader:

    def __init__(self, view_url = None, urls_txt = None):
        if view_url:
            self.download_one(view_url)
        elif urls_txt:
            self.download_some(urls_txt)


    def download_one(self, view_url):
        start_time = time.perf_counter()
        video_id_type = ''
        video_id = None
        title = ''

        def func():
            nonlocal video_id_type
            nonlocal video_id
            nonlocal title

            try:
                print(f'view_url : {view_url}')

                # 旧版URL
                video_id = re.search(r'video(\d+)', view_url)
                if video_id:
                    video_id = video_id.group(1)
                    video_id_type = 'old'
                    if self.already_downloaded(video_id):
                        print(f'早已下载过该视频')
                        return 'SAVED'

                # 新版URL
                else:
                    video_id_new = re.search(r'video\.([0-9a-zA-Z]+?)/', view_url)
                    if video_id_new:
                        video_id_new = video_id_new.group(1)
                        video_id_type = 'new'
                        if self.already_downloaded_new(video_id_new):
                            print(f'早已下载过该视频')
                            return 'SAVED'
                    else:
                        print('解析 video_id 失败')
                        return False

                invalid = True
                if video_id_type == 'old':
                    invalid = self.is_invalid(video_id)
                elif video_id_type == 'new':
                    invalid = self.is_invalid(video_id_new)
                if invalid:
                    print(f'视频已失效')
                    return 'SKIP'

                # 获取视频页面HTML数据
                request = RequestManager(config.headers, config.proxies)
                res = request.get(view_url)
                if len(res.content) == 0:
                    print(f'获取网页内容失败')
                    return False
                view_html = res.text
                # with open(r'test.html', 'w', encoding='utf-8') as f:
                #     f.write(view_html)

                # 判断视频是否有效
                valid = True
                invalid_list = [
                    'Sorry but the page you requested was not found',
                    'Sorry, this video has been deleted',
                    'This content is on hold',
                    'This video has not been released yet',
                ]
                for word in invalid_list:
                    if word in view_html:
                        valid = False
                        break
                if not valid:
                    print(f'视频已失效')
                    if video_id_type == 'old':
                        self.log_invalid(video_id)
                    elif video_id_type == 'new':
                        self.log_invalid(video_id_new)
                    return 'SKIP'

                # 从HTML数据中获取视频号 (URL改版了，现在无法直接从URL中获取)
                if not video_id:
                    video_id = re.search(r'"id_video":\s?(\d+?),', view_html)
                    if not video_id:
                        print(f'从网页内容中查找video_id失败')
                        return False
                    video_id = video_id.group(1)
                    self.map_video_id(video_id, video_id_new)

                if self.already_downloaded(video_id):
                    print(f'早已下载过')
                    return 'SAVED'
                print(f'video_id : {video_id}')

                # 获取标题
                title = re.search(r'<h2 class="page-title">(.*?)<span class="duration">', view_html)
                if not title:
                    print(f'查找网页title失败')
                    return False
                title = title.group(1).rstrip()
                title = html.unescape(title)
                if 'title-auto-tr' in title:
                    temp = re.search(r'\<span id="title-auto-tr"\>(.+?)\</span\>', title)
                    if temp:
                        title = temp.group(1)
                title = re.sub(r'[\/\\\*\?\|/:"<>\.]', '', title)
                print(f'title    : {title}')

                # 创建目录
                dir_path = os.path.join(config.path, title)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)

                # 下载图片
                result = self.download_images(title, view_html)
                if not result:
                    return False
                print()

                # 获取m3u8链接
                m3u8_url = re.search(r"html5player\.setVideoHLS\('(.*?)'\);", view_html)
                if not m3u8_url:
                    print(f'从网页中查找m3u8链接失败')
                    return False
                m3u8_url = m3u8_url.group(1)
                print(f'm3u8_url : {m3u8_url}')

                # 获取m3u8链接对应的数据
                res = request.get(m3u8_url)
                if not res:
                    print(f'获取 {m3u8_url} 内容失败')
                    return False
                m3u8_data = res.text

                # 获取最高清晰度链接
                base_url = re.search(r"(.*?)hls.m3u8", m3u8_url).group(1)
                definition_list = re.findall(r'NAME="(.*?)p"', m3u8_data)
                max_definition = max(definition_list)       # 最高清晰度
                line_list = m3u8_data.split('\n')
                for line in line_list:
                    if 'hls-' in line and max_definition in line:
                        max_definition_m3u8_url = line      # 最高清晰度的m3u8链接(相对路径)
                max_definition_m3u8_url = base_url + max_definition_m3u8_url
                print(f'{max_definition}p_url : {max_definition_m3u8_url}')

                # 下载m3u8视频
                m3u8_downloader = M3U8Downloader(base_url, max_definition_m3u8_url, title, title + '.mp4')
                result = m3u8_downloader.run()
                if not result:
                    return False

                with open(os.path.join(config.root_path, title, 'information.txt'), 'w')as f:
                    f.write(f'标题：\n{title}\n网址：\n{view_url}\n')

                return True

            except Exception as e:
                print(f'错误：{e}')
                if video_id:
                    self.download_failed(video_id)
                return False

        result = func()
        if result != 'SAVED' and result != 'SKIP':
            if result:
                mp4_path = os.path.join(config.root_path, title, title+'.mp4')
                self.download_success(video_id, start_time, mp4_path)
            else:
                print(f'视频下载失败')
                if video_id:
                    self.download_failed(video_id)


    def download_some(self, urls_txt):
        with open(urls_txt, 'r')as f:
            urls = f.read()
        urls_list = []
        for url in urls.split('\n'):
            if url[:4] == 'http':
                urls_list.append(url)
        #print(urls_list)
        for i, view_url in enumerate(urls_list):
            print('批量视频下载进度： {:>4}/{:<4}'.format(i+1, len(urls_list)))
            self.download_one(view_url)
            print('\n')


    def download_images(self, relative_path, view_html):
        img_dict = ['setThumbUrl169', 'setThumbSlide', 'setThumbSlideBig']
        img_urls_list = []
        rename_list = []
        cover_num = -1

        for img_key in img_dict:
            if img_key == 'setThumbUrl169':         # 一共30张图片，其中有一张是封面
                res = re.search(r"html5player\.%s\('(.*?)(\d+?)\.jpg'\);" % img_key, view_html)
                img_base_url = res.group(1)
                cover_num = int(res.group(2))
                print(f'cover_url: {img_base_url}{cover_num}.jpg')
                for i in range(1, 31):
                    url = img_base_url + f'{i}.jpg'
                    img_urls_list.append(url)
                    rename_list.append(f'{i}.jpg')
            else:
                keyword = rf"html5player\.{img_key}\('(.*?)'\);"
                url = re.search(keyword, view_html).group(1)
                img_urls_list.append(url)
                if img_key == 'setThumbSlide':
                    rename_list.append('31.jpg')
                else:
                    rename_list.append('32.jpg')

        fd = FileDownloader(img_urls_list, f'{relative_path}/图片', rename_list, use_progress_bar=True, progress_fmt=ProgressBar.IMAGE)

        if not set(os.listdir(os.path.join(config.root_path, relative_path, '图片'))) == set(rename_list):
            print('部分图片下载失败')
            return False

        def copy(src_img, dst_img):
            src_path = os.path.join(config.root_path, relative_path, f'图片/{src_img}')
            dst_path = os.path.join(config.root_path, relative_path, dst_img)
            shutil.copy(src_path, dst_path)

        copy(f'{cover_num}.jpg', '1.jpg')
        copy('31.jpg', '2.jpg')
        copy('32.jpg', '3.jpg')

        return True


    def already_downloaded(self, video_id):
        if not os.path.exists('SAVED.txt'):
            return False
        with open(r'SAVED.txt')as f:
            ids = f.read()
        return video_id in ids.split('\n')


    def already_downloaded_new(self, video_id_new):
        if not os.path.exists('MAP.txt'):
            return False
        with open(r'MAP.txt')as f:
            items = f.read()
        for item in items.split('\n'):
            result = item.split('\t')
            if len(result) == 2:
                new, old = result[0], result[1]
                if new == video_id_new:
                    return self.already_downloaded(old)
        return False


    def download_success(self, video_id, start_time, mp4_path):
        log_path = r'SAVED.txt'
        with open(log_path, 'a+')as f:
            f.write(video_id+'\n')

        fsize = os.path.getsize(mp4_path)
        fsize = round(fsize/float(1024*1024), 2)

        end_time = time.perf_counter()
        print('本视频大小%dMB, 下载时间%d分%.2f秒，平均下载速度为%.2fMB/s' % (fsize, (end_time-start_time)//60, (end_time-start_time)%60, fsize/(end_time-start_time)))


    def download_failed(self, video_id):
        log_path = r'FAILED.txt'
        with open(log_path, 'a+')as f:
            f.write(f'{video_id}\n')


    def map_video_id(self, video_id_old, video_id_new):
        map_path = r'MAP.txt'
        if os.path.exists(map_path):
            with open(map_path, 'r')as f:
                items = f.read()
            for item in items.split('\n'):
                result = item.split('\t')
                if len(result) == 2:
                    new, old = result[0], result[1]
                    if new == video_id_new:
                        return
        with open(map_path, 'a+') as f:
            f.write(f'{video_id_new}\t{video_id_old}\n')


    # 这里的video_id可以是旧版，可以是新版
    def is_invalid(self, video_id):
        log_path = r'INVALID.txt'
        if not os.path.exists(log_path):
            return False
        with open(log_path)as f:
            ids = f.read()
        return video_id in ids.split('\n')


    # 这里的video_id可以是旧版，可以是新版
    def log_invalid(self, video_id):
        log_path = r'INVALID.txt'
        with open(log_path, 'a+') as f:
            f.write(f'{video_id}\n')



if __name__ == '__main__':
    # view_url = 'https://www.xvideos.com/videoxxxxxxxx/~_~_1'
    # view_url = 'https://www.xvideos.com/video.xxxxxxxxxxx/~_~_1'
    # xd = XvideosDownloader(view_url = view_url)

    urls_txt = r'xvideos_urls.txt'
    xd = XvideosDownloader(urls_txt = urls_txt)