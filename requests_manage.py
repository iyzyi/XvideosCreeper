import requests
import config


class RequestManager:

    def __init__(self, headers = None, proxies = None, timeout = 8, retry_num = 5):
        self.headers = headers 
        self.proxies = proxies
        self.timeout = timeout
        self.retry_num = retry_num

        self.session = requests.Session()


    def get(self, url, headers = None, proxies = None, timeout = None, retry_num = None):  
        kwargs = {}

        if headers:
            kwargs['headers'] = headers
        elif self.headers:
            kwargs['headers'] = self.headers

        if proxies:
            kwargs['proxies'] = proxies
        if self.proxies:
            kwargs['proxies'] = self.proxies

        if timeout:
            kargs['timeout'] = timeout
        elif self.timeout:
            kwargs['timeout'] = self.timeout
        
        if retry_num:
            _retry_num = retry_num
        else:
            _retry_num = self.retry_num


        success = False
        for i in range(_retry_num):
            try:
                #if i != 0:
                #    print('第{}次重连{}'.format(i+1, url))

                res = self.session.get(url, **kwargs)

                if len(res.content) > 0:
                    success = True
                # if res.status_code == 200:
                #     success = True
                    #print(kwargs)
                    break
            except Exception as e:
                pass
                #print(e)
        if success:
            return res
        else:
            return False
