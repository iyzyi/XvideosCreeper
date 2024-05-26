import config
from requests_manage import RequestManager
from file_downloader import FileDownloader
from progress_bar import ProgressBar
import re, os


class M3U8Downloader:

    def __init__(self, root_url_path, m3u8_url, file_path, file_name):
        self.root_url_path = root_url_path
        self.m3u8_url = m3u8_url
        self.file_path = file_path
        self.absolute_file_path = os.path.join(config.path, self.file_path)
        self.file_name = file_name
        self.request = RequestManager(config.headers, config.proxies)
        self.ts_urls_list = []
        self.ts_urls_dict = {}


    def run(self):
        m3u8_info = self.request.get(self.m3u8_url)
        if m3u8_info:
            r = re.findall(r'(hls-.+?\.ts)(\n|$)', m3u8_info.text)
            for i, info in enumerate(r):
                relative_path = info[0]
                ts_url = self.root_url_path + relative_path
                self.ts_urls_list.append(ts_url)
                self.ts_urls_dict[str(i+1).zfill(8)] = ts_url.split('/')[-1].split('?')[0]

            fd = FileDownloader(self.ts_urls_list, self.file_path, use_progress_bar=True, progress_fmt=ProgressBar.VIDEO)

            return self.ts_merge()

    
    def ts_merge(self):
        try:
            if os.name == 'posix':      # 暂时不实现linux
                return None             
            if os.name == 'nt':         # windows
                sorted_ts_files = [self.ts_urls_dict[num] for num in self.ts_urls_dict.keys()]

                # ts文件数大于100
                if len(self.ts_urls_dict) > 100:

                    # 每100个ts文件为一组，合并成iyzyi_merge0000000x.mp4
                    for i in range(0, len(self.ts_urls_dict), 100):
                        input_files = '|'.join(sorted_ts_files[i : i+100])
                        command = 'cd /d "{}" & '.format(self.absolute_file_path)  
                        command += '"{}" -i "concat:{}" -y -loglevel quiet -acodec copy -vcodec copy -crf 0 "{}" & '.format(config.ffmpeg_path, input_files, 'iyzyi_merge{}.ts'.format(str(i//100+1).zfill(8)))
                        #print(command)
                        os.popen(command).read()
                    
                    # 合并iyzyi_merge0000000x.mp4
                    second_merge = []
                    for file in os.listdir(self.absolute_file_path):
                        if re.match(r'iyzyi_merge\d{8}\.ts', file):
                            #print(file)
                            second_merge.append(file)
                    #print(second_merge)
                    second_merge = sorted(second_merge)
                    input_files = '|'.join(second_merge)
                    command = 'cd /d "{}" & '.format(self.absolute_file_path)  
                    command += '"{}" -i "concat:{}" -y -loglevel quiet -acodec copy -vcodec copy -crf 0 "{}" & '.format(config.ffmpeg_path, input_files, 'iyzyi_merge00000000.mp4')      #使用替身名称，否则ffmpeg遇utf-8字符不工作
                    os.popen(command).read()
                    #print(command)

                # ts文件数小于等于100
                else:
                    input_files = '|'.join(sorted_ts_files)   
                    command = 'cd /d "{}" & '.format(self.absolute_file_path)  
                    command += '"{}" -i "concat:{}" -y -loglevel quiet -acodec copy -vcodec copy -crf 0 "{}" & '.format(config.ffmpeg_path, input_files, 'iyzyi_merge00000000.mp4')      #使用替身名称，否则ffmpeg遇utf-8字符不工作
                    os.popen(command).read()
                

                # 再把名字换回去
                command = 'cd /d "{}" & '.format(self.absolute_file_path)
                command += 'ren "%s" "%s"' % ('iyzyi_merge00000000.mp4', self.file_name)      
                os.popen(command).read()

                # 删除中间文件
                filename = os.path.join(self.absolute_file_path, self.file_name)
                if os.path.exists(filename):
                    command = 'cd /d "{}" & '.format(self.absolute_file_path)
                    command += 'del /Q *.ts & '
                    #command += 'del /Q iyzyi_merge00*.ts'
                    os.popen(command).read()
                    print('\nts文件合并成功')
                    return True
                else:
                    print('\nts文件合并失败')
                    return False
        except Exception as e:
            print('错误：{}'.format(e))
            print('\nts文件合并失败')
            return False
