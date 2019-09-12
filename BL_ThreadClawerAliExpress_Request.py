# -*- coding: utf-8 -*-
# @Author   : liu
# 加入日志
from selenium.webdriver import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
import time
import json,re,os,urllib.request,datetime,random,requests,sys,socket
from lxml import etree
from mysql_utils.mysql_db import MysqlDb
from baidu_OCR import recognition_character
import threading
from threading import Thread
from queue import Queue
from tengxun_OCR import Ocr
from selenium.webdriver.chrome.options import Options
from log_utils.mylog import Mylog
from PIL import Image
import traceback
import warnings
warnings.filterwarnings('ignore')


class ThreadClawerAliExpress(Thread):

    def __init__(self, i, product_link_queue, product_info_queue, user_id):
        '''
        :param i: 线程编号
        :param product_link_queue:商品链接队列
        :param product_info_queue: 商品信息队列
        :param user_id: 用户id
        '''
        Thread.__init__(self)
        self.user_id = user_id
        self.mysql = MysqlDb()
        self.threadName = '商品数据采集线程' + str(i)
        self.product_link_queue = product_link_queue
        self.product_info_queue = product_info_queue

        self.s = requests.session()

        # 创建一个参数对象，用来控制chrome以无界面的方式打开

        chrome_options = Options()
        # # 设置浏览器参数
        chrome_options.add_argument('--headless')  # 无界面
        chrome_options.add_argument('--disable-gpu') # 谷歌文档提到需要加上这个属性来规避bug
        chrome_options.add_argument('--no-sandbox')  # 让Chrome在root权限下跑
        chrome_options.add_argument('--disable-dev-shm-usage')  # 防止在服务器上报错
        chrome_options.add_argument('blink-settings=imagesEnabled=false') # 不加载图片, 提升速度
        chrome_options.add_argument(
            # 'User-Agent="Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16"'
            'User-Agent=\"%s\"' % get_useragent(),
        )
        # 设置开发者模式启动，该模式下webdriver属性为正常值   一般反爬比较好的网址都会根据这个反爬
        chrome_options.add_experimental_option('excludeSwitches', ['enable - automation'])
        # chrome_options.binary_location = r'C:\Users\panda\Desktop\ChromePortable\App\Google Chrome\chrome.exe'
        # 创建浏览器对象
        # self.driver = webdriver.Chrome(executable_path=r"D:\ProgramData\Anaconda3\Scripts\chromedriver.exe",chrome_options=chrome_options)
        # 创建浏览器对象
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        # self.__login__()

        pass

    def __login__(self):
        try:
            # 登录页面
            self.driver.get('https://login.aliexpress.com/')
            # 切换到iframe（否则获取不到元素）
            self.driver.switch_to_frame("alibaba-login-box")
            time.sleep(3)
            # 账户
            self.driver.find_element_by_xpath('//*[@id="fm-login-id"]').send_keys('97565476@qq.com')
            time.sleep(1)
            # 密码
            self.driver.find_element_by_xpath('//*[@id="fm-login-password"]').send_keys('123456qwe')
            time.sleep(1)
            # 点击登录
            self.driver.find_element_by_xpath('//*[@id="login-form"]//button').click()

        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(err)

    # 点击商品链接，进入商品的详情页
    def __clawlerProtect__(self, product_link):
        try:
            try:
                self.driver.get(product_link)
            except:
                count = 1
                while count <= 5:
                    try:
                        self.driver.get(product_link)
                        break
                    except:
                        err_info = '__clawlerProtect__ reloading for %d time' % count if count == 1 else '__clawlerProtect__ reloading for %d times' % count
                        print(err_info)
                        count += 1
                if count > 5:
                    print("__clawlerProtect__ job failed!")

            js = "var q=document.documentElement.scrollTop=100"
            self.driver.execute_script(js)
            time.sleep(random.randint(1, 2))
            # 设置滚动条，让数据加载完全
            js = "var q=document.documentElement.scrollTop=1000"
            self.driver.execute_script(js)
            time.sleep(random.randint(1,2))
            product_html = self.driver.page_source

            title = self.driver.title
            # cookie = ''
            # for cookie_data in self.driver.get_cookies():
            #     cookie += str(cookie_data['name']) + '=' + str(cookie_data['value']) + ';'

            return product_html, title, product_link

        except Exception as err:
            print(err)

    def __getDescription__(self,url):
        self.driver.get(url)
        html = self.driver.page_source
        product_html = etree.HTML(html)
        # 商品描述（图片）
        description_img_list = product_html.xpath('//img/@src')
        description_img_list = [str(item) for item in description_img_list]
        description_img = json.dumps(description_img_list, ensure_ascii=False)
        # 商品描述（文本）
        description_text_list = product_html.xpath('/html//text()')
        description_text_list = [item for item in [item.strip() for item in description_text_list] if item]
        description_text = json.dumps(description_text_list, ensure_ascii=False)

        description = {'img':description_img,'text':description_text}
        return description

    # 解析提取商品数据
    def __parseProduct__(self, html, product_link):
        try:
            product_html = etree.HTML(html)
            data = json.loads(re.search(r'data: (.+),', html).group(1))
            product_info = {}
            # 商品id(看做sku或者asin)商品主体没有sku，变体才有
            product_info['product_id'] = re.search(r'/(\d+)\.html', product_link).group(1)
            # 商品名称
            product_info['product_name'] = re.sub(r' +',' ',data['titleModule']['subject'])
            # 店铺名称
            product_info['productStore'] = data['storeModule']['storeName']
            # 商品价格
            if  'formatedActivityPrice' in data['priceModule'].keys():
                product_info['price'] = data['priceModule']['formatedActivityPrice']
            else:
                product_info['price'] = data['priceModule']['formatedPrice']
            # 商品链接
            product_info['product_link'] = product_link
            # 星级
            productStarLevel = data['titleModule']['feedbackRating']['averageStar']
            if productStarLevel:
                product_info['grade_star'] = productStarLevel
            else:
                product_info['grade_star'] = ''

            # 评论数
            productReviewNumber = data['titleModule']['feedbackRating']['totalValidNum']
            if productReviewNumber:
                product_info['comment_volume'] = productReviewNumber
            else:
                product_info['comment_volume'] = ''

            # 成交量
            productVOL = data['titleModule']['tradeCount']
            if productVOL:
                product_info['productVOL'] = productVOL
            else:
                product_info['productVOL'] = ''


            # 商品图片
            product_img_list = data['imageModule']['imagePathList']
            product_info['product_img_list'] = product_img_list

            # 商品描述页（包含文本、图片）
            div_element = product_html.xpath('//*[@id="product-description"]')


            if div_element:
                description_html = etree.tostring(div_element[0], encoding="utf-8", pretty_print=True, method="html").decode('utf-8').replace('max-width: 650.0px;overflow: hidden;font-size: 0;clear: both;','display:none;')
                # 图片链接替换为本地链接
                description_img_url_list = re.findall(r'src="(.+?)"', description_html)
                description_img_url = []
                for img_url in description_img_url_list:
                    if img_url[:2] == '//':
                        img_url = 'https:' + img_url
                    description_img_url.append(img_url)
                description_html = re.sub(r'src="(.+?)"','src="{}"' ,description_html)
                description_img_dir = ()
                dir = os.getcwd().replace('utils', '') + '/amazon1/amazon/amazon/static/media/img/' + str(product_info['product_id']) + '/'
                for i in range(len(description_img_url)):
                    description_img_dir += (dir + 'description_' + str(i) + '.jpg' ,)
                description_html = description_html.format(*description_img_dir).replace('/home/BL_project/amazon1/amazon/amazon','')
                product_info['description_img'] = [(img_url,img_dir) for img_url,img_dir in zip(description_img_url,description_img_dir)]

                product_info['description'] = description_html
            else:
                product_info['description_img'] = []
                product_info['description'] = ''

            # 属性（变体信息）
            # 属性列表
            attr_list = []
            attr_data_list = data['skuModule']['productSKUPropertyList']
            for attr_data in attr_data_list:
                attr_name = attr_data['skuPropertyName']
                if attr_name == "Ships From":
                    continue
                attr_value = attr_data['skuPropertyValues']
                attr_value_dict = {str(item['propertyValueId']):item['propertyValueDisplayName'] for item in attr_value}
                if  'skuPropertyImagePath' in list(attr_data['skuPropertyValues'][0].keys()):
                    attr_img = {item['propertyValueDisplayName']:item['skuPropertyImagePath']   for item in attr_data['skuPropertyValues']}
                else:
                    attr_img = {}

                attr_list.append({'attr_name':attr_name,'attr_value':attr_value_dict,'attr_img':attr_img})

            product_info['attr_list'] = attr_list


            # 变体价格
            product_attr_list = data['skuModule']['skuPriceList']
            att_data_list = []
            for price_data in product_attr_list:
                att_datas = price_data['skuPropIds'].split(',')
                # for x, y in zip(att_datas, attr_list):
                #     if x in y['attr_value'].keys():
                #         att_data.append(y['attr_value'][x])
                # att_data = [y['attr_value'][x]  for x, y in zip(att_datas, attr_list) if x in y['attr_value'].keys()]
                att_data = [{y['attr_name']:y['attr_value'][x]}  for x, y in zip(att_datas, attr_list) if x in y['attr_value'].keys()]

                if attr_list[0]['attr_img']:
                    # att_imgUrl = attr_list[0]['attr_img'][att_data[0]]
                    att_imgUrl = attr_list[0]['attr_img'][att_data[0][list(att_data[0].keys())[0]]]
                else:
                    att_imgUrl = ''
                # att_data = ','.join(att_data)
                if 'skuActivityAmount' in price_data['skuVal'].keys():
                    att_price = price_data['skuVal']['skuActivityAmount']['formatedAmount']
                else:
                    att_price = price_data['skuVal']['skuAmount']['formatedAmount']
                att_skuId = price_data['skuId']
                att_data_list.append({'att_data':att_data,'att_price':att_price,'att_skuId':att_skuId,'att_imgUrl':att_imgUrl})

            product_info['att_data_list'] = att_data_list

            # 商品规格（属性）
            product_props_list = data['specsModule']['props']
            product_info['props'] = json.dumps({item['attrName']:item['attrValue'] for item in product_props_list})

            # print(product_info)
            print('解析商品：', product_info['product_id'], product_info['product_name'])

            return product_info


        except Exception as err:
            print(attr_list[0]['attr_img'],att_data)
            mylog.logs().exception(sys.exc_info())
            # print(data)
            # err: 'NoneType' object has no attribute 'group'
            traceback.print_exc()

    # 通过requests请求数据
    def __request__(self, product_link):
        try:

            headers = {
                "Host": "www.aliexpress.com",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                # "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60",
                "User-Agent": get_useragent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                "Referer": "www.aliexpress.com",
                # "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Cookie": "ali_apache_id=10.103.184.127.1567042969606.194236.9; cna=t4LrFXVP5hYCAXFXgoCTG1VY; _m_h5_tk=76fb994d62b899c5a3a78f4b03024341_1567050891422; _m_h5_tk_enc=fa1a18114c471f6aa64fb223b001cf01; aep_common_f=TUXthmIsl93/y2b1r7uLevLTygZjdA6uN1aYWXosMbAhRGTA9P9nag==; _bl_uid=yvjImzs0whq0b0yLj46a4b7f3z3R; XSRF-TOKEN=c1c9fae3-7356-41d0-92da-4efd2716f919; _uab_collina=156704302680944309441463; acs_usuc_t=x_csrf=13yyqqm0pncm3&acs_rt=79c4eb17f7f24c228dfbb705b85c9c38; n_cap_t=953ba0d089bb2a20f8b76a5bc86167ef6e759976; _hvn_login=13; xman_us_t=x_lid=cn261343849rwfae&sign=y&x_user=L4WYvYWMWkNHg/uwebKp9SPTeMAZAOw6cArfH1yJuRE=&ctoken=np7j9pq56pa&need_popup=y&l_source=aliexpress; aep_usuc_t=ber_l=A0; xman_f=OhO+KBCzyVtqF/lK+ASBatqjNkvAKV+RvYDYyoXTsS0tpWIzOq6phPAZQr/Pr3s+2txqnTgVFQcD8KoUvoJRb5kUE4u0a+yJNcWdRnVWJ7X3C2JLra1sJJZ9s3zzSnLNHNZDRTrRJGj74MSX6LQj/PQa9OZ2Hx0bnyCGk/Pe5IlcLmDdEWiDW6oVC7YjIGOtTmtxrf5SUIhU+7tLP4bp+ASzBSpJtjNutFJBWjc3UPojpgdpdZoekh9sKlSavEziPYJdzzUr3PwgytRBHlEe31os/MSmvd4g+p5A82wWlISEW7e/G8BzqWQyBIFMvCXXWZcyBBuAJ5NfgKREKx3vk9wzHVw2lvwAHsNF6z6W1XN8LmbK37ST9fnwxxokXiFST5ieMXdLzuIP4dK7fG6Yh+n89DB2H3xC9wlG2cuK1BQ=; re_ri_f=t1KdP3RIclJ8QKNn7MYiaZxBdbD138IMyTWVm9AqTzdrLSAt/vHyNembEWwk1xwH; _mle_tmp_enc0=Ey%2Fp8LswzxA3J47VsqxI%2B%2FOCZpSFjWP%2BpkzoIWovEmLVokjMNOcUEo%2Ft0SyEUkCwmXOtFgO%2Bqrgj3gDD9VY%2B2LYqWVak%2FyDqVzChRHaKtuSPATQObwe5DTXe3sFpnwo3; xman_us_f=zero_order=y&x_locale=en_US&x_l=1&last_popup_time=1567043004934&x_user=CN|CN|shopper|ifm|1861063758&no_popup_today=n; intl_locale=en_US; aep_usuc_f=site=glo&c_tp=USD&x_alimid=1861063758&isb=y&region=CN&b_locale=en_US; intl_common_forever=gac+SJDr86h1umcDpVPnXnPauXVk/oJ3X7rf2oWrYr+UPqwD3zczlQ==; aep_history=keywords%5E%0Akeywords%09%0A%0Aproduct_selloffer%5E%0Aproduct_selloffer%0932967610915%0932972838092%0932972838092; JSESSIONID=C107B02921EFE9FBFBE9E38A7D67BEFF; _ga=GA1.2.1800507116.1567043014; _gid=GA1.2.778471017.1567043014; _fbp=fb.1.1567043016814.1983595947; ali_apache_track=mt=1|ms=|mid=cn261343849rwfae; ali_apache_tracktmp=W_signed=Y; l=cBjeGvbnqF8ydS9yBOfwSQKbU7QTnIRb4sPP2NJiiICP93fkR3iAWZEuBnLDCnGVp6DWR3uIzI2gBeYBqCAMzpboTonLp; isg=BIaGZ1oKJ_bz9vOSjYRm7cJ613yk98hh3CBOPXCv-amEcyaN2HaKs5gJT-8aW8K5; xman_t=e+DFDBWsbpi3ZGApMi+Lwx9gAP5lP0itF8OV2JLQR+eI2ZtgOa4u+l7CwNxTkPentUrpImqC7AtQ2GuCRxKNTxfwot92XmdURT7Dba/zCa13UMt9JzaViBQPaBe/CdFdHG2ntFVXz8MpDrzp3PJd43FQl3RWpH7OwgVlNIUhjGeo5y81KH13mf5cneog4qlErIM6NRbtZm/91c+WpPVVnP7UeuRietZFdhx0719/lFA+/vTBz77l4RUCUiamIWnc6XHiQLexMIE5h2GwP5D66MJ6sAdIw+voc5xzv0XsMSxL9ws/zCtQWbay0i7sAYvmyHv4Ofao8b8qe/ZKZvb4y9aIW1MZ79GhZg7QmymA/Qh3Dzj3rkupJKy60azX/dzJgYd+4Xw39nIwOhoXP7ySrfsXEeCYKvWQkvPmzDg36I7KzMqiFKMfu3MzjGGztl36yRQk7r4fXHmbQkYFTTSqaA5ZBQ9F8HSvKb8A4I5O/zTnRhne9mjQaJyt+WsVUUNYLJe3WVArwb0NhAQvjLoBtTMcldASHhoC/N5Ms4/QrpR8AnFiHGEUrhVxShQrXSQaEGr5X3ojKy64wwC911Tz3ZnKuihYE0kX4wsMTsdhQ8EQShpm+7k+PMkY6znAyo8Aft+cWRcCEILyjbpIw0uT9A=="
            }


            try:
                res = self.s.get(product_link, headers=headers, verify = False, timeout=30, proxies = get_proxy())

            except:
                count = 1
                while count <= 5:
                    try:
                        res = self.s.get(product_link, headers=headers, verify=False, timeout=30, proxies = get_proxy())
                        break
                    except:
                        err_info = '__request__ reloading for %d time' % count if count == 1 else '__request__ reloading for %d times' % count
                        print(err_info)
                        count += 1
                if count > 5:
                    self.product_link_queue.put(product_link)
                    print("__request__ job failed!")
                    return

            html = res.text
            title = re.search(r'<title[ dir="ltr"]*>(.+)?</title>', res.text).group(1)

            return html, title, product_link

        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            traceback.print_exc()

    def __query_product__(self, product_id):
        sql = 'select id from amazonshop_goods  WHERE ASIN = \'%s\'  ' % product_id
        res1 = self.mysql.select(sql)
        sql = 'select id from amazonshop_deletedgoodasin  WHERE good_asin = \'%s\' ' % product_id
        res2 = self.mysql.select(sql)
        if (res1 or res2):
            return True
        else:
            return False
        pass

    # 商品数据采集
    def clawer(self,product_link):
        try:

            print('正在爬取商品：', product_link)
            # product_html, title, product_link = self.__request__(product_link)
            product_html, title, product_link = self.__clawlerProtect__(product_link)
            product_info = self.__parseProduct__(product_html, product_link)
            # 查询库中是否有该商品的数据
            flag = self.__query_product__(product_info['product_id'])
            if not flag:
                product_info = self.__save_img__(product_info)
                self.product_info_queue.put(product_info)
            else:
                print('商品已存在：{product_id:%s}'%product_info['product_id'])

        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            traceback.print_exc()

    # 保存图片
    def __save_img__(self, product_info):
        '''
        :param productId: 商品ID（goods表中id）
        :param img_url: 图片链接
        :return:
        '''
        product_id = product_info['product_id']
        # 主体图片
        product_img_list = product_info['product_img_list']
        # 变体数据
        att_data_list = product_info['att_data_list']
        # attr_img_list = [item['attr_img'] for item in product_info['attr_list']]
        # 商品描述信息图片
        # description_img = product_info['description']['img']


        # dir = os.getcwd().replace('spider1', '') + '/static/media/img/'
        dir = os.getcwd().replace('utils','') +  '/amazon1/amazon/amazon/static/media/img/' + str(product_id) + '/'
        if not os.path.exists(dir):
            os.makedirs(dir)

        # 主体
        i = 0
        img_list = []
        for img_url in product_img_list:
            i += 1
            img_dir = dir + str(i) + '.jpg'
            img_list.append({'img_url': img_url, 'img_dir': img_dir})


        # 变体
        att_img_list = []
        for img_data in att_data_list:
            att_skuId = img_data['att_skuId']
            img_dir = dir + str(att_skuId) + '.jpg'
            att_imgUrl = img_data['att_imgUrl']
            if att_imgUrl:
                att_img_list.append({'img_url':att_imgUrl,'img_dir':img_dir})

        # 描述
        description_img_list = [{'img_url':item[0],'img_dir':item[1]} for item in product_info['description_img']]

        img_dict =  {'img_list':img_list,'att_img_list':att_img_list,'description_img_list':description_img_list}
        product_info['img_dict'] = img_dict


        try:
            # 设置超时时间为30s(解决下载不完全问题且避免陷入死循环)
            # socket.setdefaulttimeout(30)
            for img_data in (img_list + att_img_list + description_img_list):
                img_url = img_data['img_url']
                img_dir = img_data['img_dir']
                try:
                    # urllib.request.urlretrieve(img_url, img_dir)
                    r = requests.get(img_url, timeout=30, verify=False)
                    with open(img_dir, 'wb') as f:
                        f.write(r.content)
                except:
                    count = 1
                    while count <= 5:
                        try:
                            # urllib.request.urlretrieve(img_url, img_dir)
                            r = requests.get(img_url, timeout=30, verify=False)
                            with open(img_dir, 'wb') as f:
                                f.write(r.content)
                            break
                        except:
                            err_info = '__save_img__ reloading for %d time' % count if count == 1 else '__save_img__ reloading for %d times' % count
                            print(err_info)
                            count += 1
                    if count > 5:
                        print("__save_img__ job failed!")
                        print(img_url)
            return product_info

        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(err)
            traceback.print_exc()

    def run(self):
        try:
            print('启动：', self.threadName)
            while not flag_clawer:
                try:
                    product_link = self.product_link_queue.get(timeout=3)
                except:
                    time.sleep(3)
                    continue
                self.clawer(product_link)
            print('退出：', self.threadName)
            self.driver.quit()
        except Exception as err:
            print(err)


class ThreadParse(Thread):

    def __init__(self, i, user_id, product_info_queue, url, source):
        Thread.__init__(self)
        self.user_id = user_id
        self.source = source
        self.url = url
        # self.product_total = product_total
        self.mysql = MysqlDb()
        self.threadName = '解析线程' + str(i)
        self.product_info_queue = product_info_queue

    # 将商品的排名信息写入排名表
    def __save_categorySalesRank__(self, productId, categorySalesRank, type):
        '''
        :param productId: 商品ID(goods表中id)
        :param categorySalesRank: 商品排名信息，list类型（[(排名1，类别1),(排名2，类别2)...]）
        :return:
        '''
        try:
            if type == 1:
                sql = 'insert ignore into amazonshop_categoryrank (good_id, ranking, sort) values (%s, %s, %s)'
                # sql = 'insert into amazonshop_categoryrank (good_id, ranking, sort) SELECT %s,\'%s\',\'%s\'  FROM  dual' \
                #       ' WHERE  NOT  EXISTS (SELECT id FROM amazonshop_categoryrank WHERE good_id = %s AND sort = \'%s\' )' % ()

            elif type == 2:
                sql = 'insert ignore into amazonshop_attrcategoryrank (good_attr_id, ranking, sort) values (%s, %s, %s)'

            value = []
            for data in categorySalesRank:
                value.append((productId,) + data)
            self.mysql.insert(sql, value)
        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(err)
            traceback.print_exc()

    # 将属性及属性值信息写入属性表（属性分类表、属性分类值表）
    def __save_dimensions__(self, dimension, dimensionValues):
        '''
        :param dimension: 商品的属性名称（如color、size）,str类型
        :param dimensionValues: 商品的属性值（如color的属性值有red、black、white）,list类型([])
        :return: 返回属性值的id（属性分类值表的id），list类型
        '''
        try:
            if 'Size' in dimension:
                export_name = 'size'
            elif 'Color' in dimension:
                export_name = 'color'
            elif 'Length' in dimension:
                export_name = 'size'
            elif 'Width' in dimension:
                export_name = 'size'
            elif 'Height' in dimension:
                export_name = 'size'
            else:
                export_name = ''

            # 写入属性信息
            sql = 'insert into amazonshop_attrcategory (attr_name,export_name) select \"%s\",\"%s\" from dual WHERE NOT  EXISTS  (SELECT id from amazonshop_attrcategory WHERE attr_name = \"%s\" ) ' % (
            dimension, export_name, dimension)
            cur = self.mysql.mysql.cursor()
            cur.execute(sql)
            cur.execute('commit')

            # 写入属性值信息
            sql = 'SELECT id FROM amazonshop_attrcategory WHERE attr_name = \"%s\" ' % dimension
            attr_id = self.mysql.select(sql)[0]['id']
            value = [(attr_id, attr_value) for attr_value in dimensionValues]
            sql = 'insert ignore into amazonshop_attrcategoryvalue (attrcategory_id, attr_value) values (%s,%s)'
            self.mysql.insert(sql, value)

            # 关闭游标
            cur.close()
        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(err)
            traceback.print_exc()

    # 将属性值组合信息写入商品属性表
    def __save_dimensionValues__(self, productId, product_info):
        '''
        :param productId: 商品ID（goods表中的id）
        :param product_info: 商品变体的信息，dict类型
        :return:
        '''
        try:
            attr_list = product_info['att_data_list']
            for attr_data in attr_list:
                attr_tuple = ()
                for attr_value in attr_data['att_data']:
                    name = list(attr_value.keys())[0]
                    value = list(attr_value.values())[0]
                    sql = 'select a.id from amazonshop_attrcategoryvalue a,amazonshop_attrcategory b where a.attr_value = \"%s\" AND  b.attr_name = \"%s\" AND a.attrcategory_id = b.id ' % (value, name)
                    id = self.mysql.select(sql)[0]['id']
                    attr_tuple += (id,)

                img_dir = '/static/media/img/' + str(product_info['product_id']) + '/' + str(attr_data['att_skuId']) + '.jpg'
                # 将商品的属性值组合信息写入商品属性表
                sql = 'insert ignore into amazonshop_goodsattr (good_attr,good_id,ASIN,brand_name,comment_volume,grade_star,product_name,price,selling_point,product_description,img_url,img_dir,good_url,source_id) values ' \
                      '(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                value = [(str(attr_tuple), productId, attr_data['att_skuId'], product_info['productStore'],
                         product_info['comment_volume'], product_info['grade_star'], product_info['product_name'],
                         attr_data['att_price'], product_info['props'],product_info['description'],
                         attr_data['att_imgUrl'], img_dir, product_info['product_link'],self.source)]

                self.mysql.insert(sql, value)


        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(err)
            traceback.print_exc()

    # 将商品信息写入商品表
    def __save_productInfo__(self, product_info, user_id):
            '''
            :param product_info: 商品信息
            :return: 返回商品ID
            '''
            try:
                # 主体
                img_list = product_info['img_dict']['img_list']
                img_dir = '/static' + img_list[0]['img_dir'].split('static')[1]

                sql = 'insert ignore into amazonshop_goods (ASIN,brand_name,comment_volume,grade_star,product_name,price,selling_point,product_description,user_id,img_url,img_dir,good_url,source_id) values ' \
                      '(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                value = [(product_info['product_id'], product_info['productStore'],product_info['comment_volume'],
                          product_info['grade_star'], product_info['product_name'],product_info['price'],
                          product_info['props'],product_info['description'], user_id,img_list[0]['img_url'],
                          img_dir, product_info['product_link'],self.source)]
                self.mysql.insert(sql, value)

                sql = 'select id from amazonshop_goods WHERE  ASIN = \'%s\' AND  user_id = %s ' % (
                    product_info['product_id'], user_id)
                productId = self.mysql.select(sql)[0]['id']

                return productId
            except Exception as err:
                mylog.logs().exception(sys.exc_info())
                print(err)
                traceback.print_exc()

    # 保存商品数据
    def __save_data__(self, product_info):
        try:
            # 保存主体商品信息，并返回商品id
            productId = self.__save_productInfo__(product_info, self.user_id)

            # 保存商品的属性信息
            attr_list = product_info['attr_list']
            for attr_data in attr_list:
                attr_name = attr_data['attr_name']
                attr_value = list(attr_data['attr_value'].values())
                self.__save_dimensions__(attr_name, attr_value)

            # 保存变体商品信息
            self.__save_dimensionValues__(productId, product_info)

        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            traceback.print_exc()

    def __save_process__(self, sum, num):

        # 更新数据库的采集进度
        sql = 'update amazonshop_usershopsurl set sum = %s, num = %s WHERE  shop_url = %s'
        self.mysql.update(sql,[(sum, num, self.url)])

        # 更新当前的采集进度（web展示）
        content = {"shop_url":self.url,"total":sum,"number":num,"user_id":self.user_id}
        # file_root = os.getcwd() + '/file/'
        file_root = os.getcwd().replace('utils','') + '/amazon1/amazon/amazon/static/file/'
        if not os.path.exists(file_root):
            os.makedirs(file_root)
        file_path = file_root + 'process.json'
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(content, json_file, ensure_ascii=False)
        pass

    def run(self):

        try:
            print('启动：', self.threadName)

            while not flag_parse:
                try:
                    product_info = self.product_info_queue.get(timeout=3)
                except:
                    time.sleep(3)
                    continue

                try:
                    self.__save_data__(product_info)
                    print('写入商品：', product_info['product_id'], product_info['product_name'])
                    # 保存采集进度
                    global sum, num
                    num += 1
                    self.__save_process__(sum, num)
                except:
                    pass

            print('退出：',self.threadName)
        except Exception as err:
            print(err)


class GetAllProductsLink(Thread):

    def __init__(self, i ,url, product_link_queue):
        '''
        :param url: 店铺链接
        :param product_link_queue: 商品链接队列
        '''
        Thread.__init__(self)
        self.threadName = '商品链接采集线程' + str(i)
        self.url = url
        self.product_link_queue = product_link_queue


        self.s = requests.session()

        # 创建一个参数对象，用来控制chrome以无界面的方式打开

        chrome_options = Options()
        # 设置浏览器参数

        # prefs = {
        #     'profile.default_content_setting_values': {
        #         'images': 1,
        #         'javascript': 2 # 禁用js
        #     }
        # }
        # chrome_options.add_experimental_option('prefs', prefs)

        prefs = {
            'profile.default_content_setting_values':
                {
                    'notifications': 2 # 禁止弹窗
                }
        }
        chrome_options.add_experimental_option('prefs', prefs)


        chrome_options.add_argument('--headless')  # 无界面
        chrome_options.add_argument('--disable-gpu') # 谷歌文档提到需要加上这个属性来规避bug
        chrome_options.add_argument('--start-maximized') # 窗口最大化
        chrome_options.add_argument('--no-sandbox')  # 让Chrome在root权限下跑
        chrome_options.add_argument('--disable-dev-shm-usage') # 防止在服务器上报错
        chrome_options.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
        chrome_options.add_argument(
            # 'User-Agent="Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16"'
            'User-Agent=\"%s\"' % get_useragent(),
        )
        # 设置开发者模式启动，该模式下webdriver属性为正常值   一般反爬比较好的网址都会根据这个反爬
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # chrome_options.binary_location = r'C:\Users\panda\Desktop\ChromePortable\App\Google Chrome\chrome.exe'
        # 创建浏览器对象
        # self.driver = webdriver.Chrome(executable_path=r"D:\ProgramData\Anaconda3\Scripts\chromedriver.exe",chrome_options=chrome_options)
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        # 设置页面最大加载时间
        # self.driver.set_page_load_timeout(10)
        # 默认打开登录页面
        # self.driver.get('https://login.aliexpress.com/')

    # 打开当前页面，返回当前页面的商品列表
    def __clawer__(self, next_url, url):

        try:
            n = 0
            html, url = self.__request__(next_url, url, n)
            next_url = self.__getProductlink__(html)
            time.sleep(random.randint(50, 60))

            return next_url, url

        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            traceback.print_exc()

    def __get_account__(self):
        account_list = [
            {'account_name':'97565476@qq.com','account_password':'123456qwe'},
            {'account_name':'382770108@qq.com','account_password':'123456Qwe'},
        ]
        account = random.choice(account_list)
        return account['account_name'], account['account_password']

    def __login__(self):
        try:
            # 登录页面
            try:
                self.driver.get('https://login.aliexpress.com/')
            except:
                pass
            time.sleep(3)
            # 获取账户
            account_name, account_password = self.__get_account__()
            # 切换到iframe（否则获取不到元素）
            self.driver.switch_to_frame("alibaba-login-box")
            # 账户
            self.driver.find_element_by_xpath('//*[@id="fm-login-id"]').send_keys(account_name)
            # self.driver.find_element_by_xpath('//*[@id="fm-login-id"]').send_keys('97565476@qq.com')
            # self.driver.find_element_by_xpath('//*[@id="fm-login-id"]').send_keys('382770108@qq.com')
            time.sleep(1)
            # 密码
            pwd = self.driver.find_element_by_xpath('//*[@id="fm-login-password"]')
            # 模拟输入密码错误，并再次输入
            pwd.send_keys('123456')
            time.sleep(random.random())
            pwd.clear()
            time.sleep(random.randint(1,2))
            pwd.send_keys(account_password)
            time.sleep(random.randint(2, 3))
            try:
                self.driver.find_element_by_xpath('//*[@id="nc_1_n1z"]')
                self.slide_to_verify()
            except:
                pass
            # 点击登录
            self.driver.find_element_by_xpath('//*[@id="login-form"]//button').click()

            cookie = {}
            for cookie_data in self.driver.get_cookies():
                cookie[cookie_data['name']] = cookie_data['value']

            return cookie

        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            # print(err)

    # 获取当前页面每件商品的链接
    def __getProductlink__(self, html_source):
        '''
        :param url: 店铺当前页的url
        :return: 返回当前页面的下一页链接
        '''
        try:

            html = etree.HTML(html_source)

            # 获取商品链接
            products_list = html.xpath("//ul[@class='items-list util-clearfix']/li/div[1]/div[1]/a/@href")

            global sum
            sum += len(products_list)

            # 获取下一页链接
            next_url = self.__getNextPage__(html)

            for product in products_list:
                protuct_link = str(product).replace('//', '')
                protuct_link = 'https://www.aliexpress.com/item/' + re.search(r'_(\d+\.html)', protuct_link).group(1)
                self.product_link_queue.put(protuct_link)

            return next_url

        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(err)
            traceback.print_exc()

    # 获取下一页链接
    def __getNextPage__(self, html):
        try:
            # 获取下一页url
            next_ = html.xpath('//a[@class="ui-pagination-next"]/@href')
            if next_:
                next_url = 'https:' + str(html.xpath('//a[contains(text(),"Next")]/@href')[0])
                return next_url
            else:
                # 下一页不存在
                return False
        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(err)
            traceback.print_exc()

    def __selenium__(self, url):
        try:
            self.driver.get(url)
            n = str(random.randint(500,2000))
            js = "var q=document.documentElement.scrollTop=" + n
            self.driver.execute_script(js)
            time.sleep(random.randint(1, 2))
            js = "var q=document.documentElement.scrollTop=300"
            self.driver.execute_script(js)
            time.sleep(random.randint(1, 2))
            js = "var q=document.documentElement.scrollTop=10000"
            self.driver.execute_script(js)
            time.sleep(random.randint(1, 2))

            html_source = self.driver.page_source
            title = self.driver.title
            # html = etree.HTML(html_source)
            # products_list = html.xpath("//ul[@class='items-list util-clearfix']/li/div[1]/div[1]/a/@href")
            return html_source, url ,title

        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(err)
            traceback.print_exc()

    def __request__(self, url, referer , n):

        headers = {
            "Host": "www.aliexpress.com",
            "Connection": "keep-alive",
            # "Cache-Control": " max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": get_useragent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Referer": referer,
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            # "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            # "Cookie": "ali_apache_id=10.103.166.17.1564972496692.314349.2; cna=MJHOFZFqTGQCAXd7hW7RbDW+; aep_common_f=s2S5iSRoLL/xeUxx4lElCqPxKHfC+NE2cmbLRdr/Q/pJRG74xU6jeg==; _ga=GA1.2.86522749.1564975934; _bl_uid=I4j9byz9xa2unv9jIi1jznwuLg8z; _uab_collina=156497664328006922363972; intl_locale=en_US; _gid=GA1.2.1446018449.1565658388; _fbp=fb.1.1565658388480.45105460; _hvn_login=13; aep_usuc_t=ber_l=A0; ali_apache_tracktmp=W_signed=Y; acs_usuc_t=acs_rt=ee7529d5ebb1455499561f995172aa0e&x_csrf=14pvv1zifx5zg; XSRF-TOKEN=b126ff26-c8f3-49b3-af46-833c1953d65a; JSESSIONID=11DABEF03410B74E0794AFDDFA7D5492; aep_history=keywords%5E%0Akeywords%09%0A%0Aproduct_selloffer%5E%0Aproduct_selloffer%0933051278895%0932909510019%0932810934777%0933035526367%0932838346044%0932892901920%0932996370174%0932955810487; _mle_tmp_enc0=Ey%2Fp8LswzxA3J47VsqxI%2B6mLKOTiqa5Lpi%2FMeleRq7d%2FDnMh%2BuxNdHkBA%2FvPee7Uwvd3%2BtwJIxFz83XYf1rXUOyeZSYZG7Zn7S34c%2FoOYeNNRL7NmRCDbYGKLNxVgInG; _m_h5_tk=2ce73230c0370b7114c70ef7a4989517_1565689765542; _m_h5_tk_enc=9081ea4fa22dafd65332d979c8c96db9; xman_us_t=x_lid=cn261343849rwfae&sign=y&x_user=E9UJox29XphkMz2HEDjFlkf+1oJDCte2RtkVXlSkbFM=&ctoken=qt8q29fiv41a&need_popup=y&l_source=aliexpress; xman_f=xoFBv51OtzNJvazeVF88u/4qcPNkY7xaV18nHEnDcZPHhdabyS5869iklKAM+5NJ1t6Y8bmuaryeVhrNhRca9qp3Ov8BBGHdMtfmHQrXwG9EmxJZNbUkP8JQq632/7i6JFmPPPVJusijX/XGve1EGcJo/JjHxQPAveziJI2vUWOe0NGTo2iIGRqBZfJhJobgaITZtk5wsv0I0REE/0A8aOlGNc9O9lDOFoiMcyT1VdO8hjRSroMegOSOlsJq0fjn3aGJNw74tIQK2sa+kmYw5ylmWC4/c+M/yZzrRYfHNbVzvHEWZIdK+glM6r+eeAiaF5CtQ5Tf7vh+r7k8zmgvDGP7UE3gw1ZD02hpeaekyNeU/PwXl5AWKzKwaCrHN+w0SH/bvfDCoNf7StW9++HlQeewXenJt5UlWI3T2UsAopU=; xman_us_f=zero_order=y&x_locale=en_US&x_l=1&last_popup_time=1564975927101&x_user=CN|CN|shopper|ifm|1861063758&no_popup_today=n; aep_usuc_f=site=glo&c_tp=USD&x_alimid=1861063758&isb=y&region=CN&b_locale=en_US; _gat=1; intl_common_forever=rXRSHRjB+kmZcdGqwzcSzbrzJ65rv9Y3OhEG3xK6JWFQSJ5a5GvVyQ==; ali_apache_track=mt=1|ms=|mid=cn261343849rwfae; xman_t=29QUM9dsDjrgXo5QP4S3GETnmYEH4zs+lH1fJJfUu4bYz2qXRJMollWOXCPH4gPj3uJUfYnSYqXyfyoahQVScBngWEx7zZEwgbNUoBtVQaSBVJT4q0VMBN6j7U9cdLBC/RWRAuaAVTlPAGa8HkfoEkamL2HVpubP97AE8uzjWNr84lDUS20H64+Xr2N/0ioXnTLMwAy1cUwZkWvp0PYtWqEx/97eHKIGdK9qFdAy6kuC645iT6GS+7xT7ik3uQlnJCUj/QhhHbxfrApUsH3U9j0c7+IduJ6lJY+rKNg7dM04x3gQXcgPqI3+wEx/KXerAGVzOwhH5rEktu4eipQEV3VO3z5HPqgMw5REYhc3g4aigO8Q4aSaq733z2LfYYQv5jnTlB7diXvdYhpmWxiiBD0PJF4pU5sGPjZ+yzgIos00/yMQY2i9sK4Y+IyDZjltS6okF/1h8zWt7Z6eLO6Upfpwqj8O6ioRBey+Qf1TN1uw5R8NdoYSLhmdcsOnnPSzYtr7QZeAy8Z8nuUCryqRc5IIHSAnReMd9VXmR/0YdYpNMX0vi8kcPq32HvQjK3mavAe7RI9dAAT/AcZ0GN+L1XDplm2mDyswWQXSVYssLjXfPKtd59sIrSdBwAGHo6o40uK3etDe6R1H97cyal/bgA==; isg=BNzcYxzx7b00n5mE26JrxgmtrfoiRYEDyA5DLrbc4kcnAX2L3mbgD9_zYSlcibjX; l=cBxuVc5qqMecYzDSBOfwSQKbLm7TnIOb8sPP2NRG-ICPO_55k6MPWZe2eFYXCnGVLsM2R37uMFCUBWYajyUIhHZY1KFS4-9N."
        }

        try:
            res = self.s.get(url, headers=headers, verify=False, proxies = get_proxy(), timeout = 30)
        except:
            count = 1
            while count <= 5:
                try:
                    res = self.s.get(url, headers=headers, verify=False, proxies = get_proxy(), timeout = 30)
                    break
                except:
                    err_info = '__request__ reloading for %d time' % count if count == 1 else '__request__ reloading for %d times' % count
                    print(err_info)
                    count += 1
            if count > 5:
                print("__request__ job failed!")
                return

        html_source = res.text

        # 验证是否获取到正确数据
        title = re.search(r'<title[ dir="ltr"]*>(.+)?</title>', html_source).group(1)
        if title == "AliExpress.com" or title == "Buy Products Online from China Wholesalers at Aliexpress.com":
            print("AliExpress.com--Request")
            n += 1
            while n <= 5:
                cookie = self.__login__()
                # 把cookie值转换为cookiejar类型，然后传给Session
                self.s.cookies = requests.utils.cookiejar_from_dict(cookie, cookiejar=None, overwrite=True)
                html_source, url = self.__request__(url, referer ,n)
                break
            else:
                html_source, url, title = self.__selenium__(url)
                # 验证是否获取到正确数据
                if title == "AliExpress.com" or title == "Buy Products Online from China Wholesalers at Aliexpress.com":
                    print("AliExpress.com--Selenium")
                    html_source, url = self.__request__(url, referer, n)
                else:
                    return html_source, url


        return  html_source, url

    def run(self):

        print('启动：', self.threadName)
        # 店铺总链接（默认店铺的第一页链接）
        next_url, url = self.url , self.url
        # 循环遍历店铺的所有商品页
        for i in range(1000):
            if next_url:

                print('正在获取该页面下的所有商品链接：',next_url)
                next_url, url = self.__clawer__(next_url, url)

            else:
                if next_url == 'Sorry':
                    print('获取链接失败！')
                self.driver.quit()
                print('退出：', self.threadName)
                break



def get_proxy():
    # 代理服务器
    proxyHost = "http-dyn.abuyun.com"
    proxyPort = "9020"

    # 代理隧道验证信息
    proxyUser = "H19SC127905HL13D"
    proxyPass = "7942D1D850E8D5C5"

    proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
        "host": proxyHost,
        "port": proxyPort,
        "user": proxyUser,
        "pass": proxyPass,
    }

    proxies = {
        "http": proxyMeta,
        "https": proxyMeta,
    }

    return proxies

def update_process():
    # 更新当前的采集进度（web展示）
    content = {}
    file_root = os.getcwd().replace('utils', '') + '/amazon1/amazon/amazon/static/file/'
    if not os.path.exists(file_root):
        os.makedirs(file_root)
    file_path = file_root + 'process.json'
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(content, json_file, ensure_ascii=False)
    pass

def get_useragent():
    useragent_list = [
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 UBrowser/4.0.3214.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
    ]
    return random.choice(useragent_list)
    pass


# 采集是否完成的标志
flag_clawer = False
# 解析是否完成的标志
flag_parse = False
# 创建日志
mylog = Mylog('clawer_aliexpress')
# 商品采集数
sum = 0
num = 0


def main(url,user_id,source):

    # 店铺链接转换（通过链接直接获取店铺下的所有商品）
    if 'all-wholesale-products' not in url:
        store_url = url
        sub_str = 'store/all-wholesale-products/' + re.search(r'/(\d+)\?', store_url).group(1) + '.html'
        all_products_url = store_url.replace(store_url[store_url.index('store'):], sub_str)
        all_products_url = all_products_url.replace('all-wholesale-products/','').replace('.html','/search/1.html?origin=n&SortType=bestmatch_sort')
    else:
        all_products_url = url

    # 商品链接队列
    product_link_queue = Queue()
    # 商品信息队列
    product_info_queue = Queue()

    # 商品总数
    # product_total = product_link_queue.qsize()


    # url = 'https://www.aliexpress.com/item/32867514670.html'
    # product_link_queue.put(url)

    # 存储1个采集商品链接线程的列表集合
    threadlink = []
    for i in range(1):
        thread = GetAllProductsLink(i, all_products_url, product_link_queue)
        thread.start()
        threadlink.append(thread)

    # 存储3个采集线程的列表集合
    threadcrawl = []
    for i in range(3):
        thread = ThreadClawerAliExpress(i, product_link_queue, product_info_queue, user_id)
        thread.start()
        threadcrawl.append(thread)

    # 存储1个解析线程
    threadparse = []
    for i in range(1):
        thread = ThreadParse(i, user_id, product_info_queue, url, source)
        thread.start()
        threadparse.append(thread)


    # for thread in threadlink:
    #     thread.join()


    # 等待队列为空，采集完成
    while not product_link_queue.empty():
        pass
    else:
        global flag_clawer
        flag_clawer = True

    for thread in threadcrawl:
        thread.join()


    #等待队列为空，解析完成
    while not product_info_queue.empty():
        pass
    else:
        global flag_parse
        flag_parse = True



    for thread in threadparse:
        thread.join()

    # 更新采集进程，web显示进度
    update_process()

    print('数据采集完成！')
    flag_clawer = False
    flag_parse = False

    # else:
    #     print('数据采集失败！')



if __name__ == '__main__':

    url = 'https://www.aliexpress.com/store/all-wholesale-products/4651052.html?spm=2114.12010615.pcShopHead_35211393.99' # 16
    # url = 'https://www.aliexpress.com/store/all-wholesale-products/3100086.html?spm=a2g1y.12024536.pcShopHead_53137125.99' # 20
    # url = 'https://www.aliexpress.com/store/2788034?spm=a2g0o.detail.100005.2.1f9e6cfeLeu0TU' #86

    main(url,user_id=2,source=2)

