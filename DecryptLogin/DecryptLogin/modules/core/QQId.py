'''
Function:
    QQ中心模拟登录
Author:
    Charles
微信公众号:
    Charles的皮卡丘
更新日期:
    2022-04-23
'''
import os
import re
import time
import random
import requests
from ..utils import removeImage, showImage, saveImage


'''PC端登录QQ中心'''
class QQIdPC():
    is_callable = False
    def __init__(self, **kwargs):
        for key, value in kwargs.items(): setattr(self, key, value)
        self.info = 'login in QQId in pc mode'


'''移动端登录QQ中心'''
class QQIdMobile():
    is_callable = False
    def __init__(self, **kwargs):
        for key, value in kwargs.items(): setattr(self, key, value)
        self.info = 'login in QQId in mobile mode'


'''扫码登录QQ中心'''
class QQIdScanqr():
    is_callable = True
    def __init__(self, **kwargs):
        for key, value in kwargs.items(): setattr(self, key, value)
        self.info = 'login in QQId in scanqr mode'
        self.cur_path = os.getcwd()
        self.session = requests.Session()
        self.__initialize()
    '''登录函数'''
    def login(self, username='', password='', crack_captcha_func=None, **kwargs):
        # 设置代理
        self.session.proxies.update(kwargs.get('proxies', {}))
        # 保存cookies的字典
        all_cookies = {}
        # 获取pt_login_sig
        params = {
            'pt_disable_pwd': '1',
            'appid': '1006102',
            'daid': '1',
            'style': '23',
            'hide_border': '1',
            'proxy_url': 'https://id.qq.com/login/proxy.html',
            's_url': 'https://id.qq.com/index.html'
        }
        response = self.session.get(self.xlogin_url, headers=self.headers, verify=False, params=params)
        all_cookies.update(requests.utils.dict_from_cookiejar(response.cookies))
        pt_login_sig = all_cookies['pt_login_sig']
        # 获得ptqrtoken
        params = {
            'appid': '1006102',
            'e': '2',
            'l': 'M',
            's': '3',
            'd': '72',
            'v': '4',
            't': str(random.random()),
            'daid': '1',
            'pt_3rd_aid': '0'
        }
        response = self.session.get(self.qrshow_url, headers=self.headers, verify=False, params=params)
        all_cookies.update(requests.utils.dict_from_cookiejar(response.cookies))
        ptqrtoken = self.__decryptQrsig(all_cookies['qrsig'])
        # 保存二维码图片
        qrcode_path = saveImage(response.content, os.path.join(self.cur_path, 'qrcode.jpg'))
        showImage(qrcode_path)
        self.session.cookies.update(all_cookies)
        # 检测二维码状态
        while True:
            params = {
                'u1': 'https://id.qq.com/index.html',
                'ptqrtoken': ptqrtoken,
                'ptredirect': '1',
                'h': '1',
                't': '1',
                'g': '1',
                'from_ui': '1',
                'ptlang': '2052',
                'action': '0-0-' + str(int(time.time())),
                'js_ver': '19112817',
                'js_type': '1',
                'login_sig': pt_login_sig,
                'pt_uistyle': '40',
                'aid': '1006102',
                'daid': '1',
                'ptdrvs': 'tdFUBPqGbsl12CBHGONGr1T3rqmzLwCrhYVcn7cbpIikibC3NmyChzmAr0L*Nxkn',
                'has_onekey': '1'
            }
            response = self.session.get(self.qrlogin_url, headers=self.headers, verify=False, params=params)
            if '登录成功' in response.text:
                break
            elif '二维码已经失效' in response.text:
                raise RuntimeError('Fail to login, qrcode has expired')
            time.sleep(2)
        # 登录成功
        all_cookies.update(requests.utils.dict_from_cookiejar(response.cookies))
        qq_number = re.findall(r'&uin=(.+?)&service', response.text)[0]
        url_refresh = response.text[response.text.find('http'): response.text.find('pt_3rd_aid=0')] + 'pt_3rd_aid=0'
        self.session.cookies.update(all_cookies)
        response = self.session.get(url_refresh, allow_redirects=False, verify=False)
        all_cookies.update(requests.utils.dict_from_cookiejar(response.cookies))
        self.session.cookies.update(all_cookies)
        removeImage(qrcode_path)
        print('[INFO]: Account -> %s, login successfully' % qq_number)
        infos_return = {'username': qq_number, 'cookies': all_cookies}
        return infos_return, self.session
    '''qrsig转ptqrtoken, hash33函数'''
    def __decryptQrsig(self, qrsig):
        e = 0
        for c in qrsig:
            e += (e << 5) + ord(c)
        return 2147483647 & e
    '''初始化PC端'''
    def __initialize(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        }
        self.xlogin_url = 'https://xui.ptlogin2.qq.com/cgi-bin/xlogin?'
        self.qrshow_url = 'https://ssl.ptlogin2.qq.com/ptqrshow?'
        self.qrlogin_url = 'https://ssl.ptlogin2.qq.com/ptqrlogin?'


'''
Function:
    QQ中心模拟登录
Detail:
    -login:
        Input:
            --username: 用户名
            --password: 密码
            --mode: mobile/pc/scanqr
            --crack_captcha_func: 若提供验证码接口, 则利用该接口来实现验证码的自动识别
            --proxies: 为requests.Session()设置代理
        Return:
            --infos_return: 用户名等信息
            --session: 登录后的requests.Session()
'''
class QQId():
    def __init__(self, **kwargs):
        self.info = 'login in QQId'
        self.supported_modes = {
            'pc': QQIdPC(**kwargs),
            'mobile': QQIdMobile(**kwargs),
            'scanqr': QQIdScanqr(**kwargs),
        }
    '''登录函数'''
    def login(self, username='', password='', mode='scanqr', crack_captcha_func=None, **kwargs):
        assert mode in self.supported_modes, 'unsupport mode %s in QQId.login' % mode
        selected_api = self.supported_modes[mode]
        if not selected_api.is_callable: raise NotImplementedError('not be implemented for mode %s in QQId.login' % mode)
        args = {
            'username': username,
            'password': password,
            'crack_captcha_func': crack_captcha_func,
        }
        args.update(kwargs)
        return selected_api.login(**args)