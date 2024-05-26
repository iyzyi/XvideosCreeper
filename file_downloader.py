import config
from requests_manage import RequestManager
from progress_bar import ProgressBar
from threading import Thread, Lock
from os import path, makedirs


class FileDownloader:
    
    def __init__(self, urls_list, relative_path, rename_list = None, use_progress_bar = False, progress_fmt=ProgressBar.FMT):
        self.urls_list = urls_list
        self.urls_list_bak = urls_list.copy()
        self.relative_path = relative_path
        self.rename_list = rename_list
        self.use_progress_bar = use_progress_bar
        self.thread_list = []
        self.request = RequestManager(config.headers, config.proxies)
        self.lock = Lock()
        self.path = path.join(config.root_path, relative_path)
        if not path.exists(self.path):
            makedirs(self.path)
        # 进度条
        if use_progress_bar:
            self.progress_bar = ProgressBar(len(self.urls_list), fmt=progress_fmt)

        self.save_files()


    def save_files(self):
        for i in range(config.thread_num):
            t = Thread(target = FileDownloader.thread_func, args=(self,))
            t.setDaemon(True)               #设置守护进程
            t.start()
            self.thread_list.append(t)

        for t in self.thread_list:
            t.join()                        #阻塞主进程，进行完所有线程后再运行主进程


    def thread_func(self):
        while True:
            url = ''
            self.lock.acquire()
            if len(self.urls_list) > 0:
                url = self.urls_list.pop()
            else:
                self.lock.release()
                break
            self.lock.release()

            if url:
                self.save_file(url)

            # 绘制进度条
            self.lock.acquire()
            if self.use_progress_bar:
                self.progress_bar.current += 1
                self.progress_bar()
            self.lock.release()




    def save_file(self, url):
        res = self.request.get(url)
        if res:
            file_name = ''
            if self.rename_list:
                try:
                    index = self.urls_list_bak.index(url)
                    file_name = self.rename_list[index]
                except ValueError:
                    pass
            if file_name == '':
                file_name = url.split('/')[-1].split('?')[0]
            file_path = path.join(self.path, file_name)
            with open(file_path, 'wb')as f:
                f.write(res.content)
        #print('成功下载：{}'.format(file_path))
