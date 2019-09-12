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
        self.threadName = '采集线程' + str(i)
        self.product_link_queue = product_link_queue
        self.product_info_queue = product_info_queue


        # cap = DesiredCapabilities.PHANTOMJS.copy()  # 使用copy()防止修改原代码定义dict
        # service_args = [
        #     '--ssl-protocol=any', # 任何协议
        #     '--cookies-file=False',# cookies文件
        #     '--disk-cache=no',# 不设置缓存
        #     '--ignore-ssl-errors=true' # 忽略https错误
        # ]
        # headers = {
        #     "Host": "www.aliexpress.com",
        #     "Connection": "keep-alive",
        #     "Cache-Control": " max-age=0",
        #     "Upgrade-Insecure-Requests": "1",
        #     "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60",
        #     # "User-Agent": get_useragent(),
        #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        #     "Referer": "www.aliexpress.com",
        #     # "Accept-Encoding": "gzip, deflate, br",
        #     "Accept-Language": "zh-CN,zh;q=0.9",
        #     "Cookie": "ali_apache_id=10.103.166.17.1563934057953.180428.7; cna=Cpy9FdvlwGsCAXd7hZnAY+nZ; _ga=GA1.2.1037382476.1563934063; _bl_uid=mbjU5yznjjetqgp0ernnogR07s5O; _uab_collina=156412850518171280323644; _gid=GA1.2.1380136896.1564362589; intl_locale=en_US; XSRF-TOKEN=948f5c91-efe9-45e8-aeba-fbd29546662a; aep_usuc_t=ber_l=A0; aep_common_f=VjR+npTVveoBmRxPay48IN6WNrDS1AcIWlI0OxV+4Ildejg/87CTVQ==; acs_usuc_t=acs_rt=6660d304dffb4e8ea7ce88c68c3ff3db&x_csrf=64qvshjmgp1b; ali_apache_tracktmp=W_signed=Y; _mle_tmp_enc0=Ey%2Fp8LswzxA3J47VsqxI%2B8Dszs4CPipHhvMC9NArEbowg4%2BqX7d9T2rmqYMgdUK%2BU%2FfdsEWiIWsHhxhgcr6h5XfB0wo92Yrlc7VUGqcaT5yZRN9XnwSOUGxjIoowUXn6; _hvn_login=13; xman_us_t=x_lid=cn261343849rwfae&sign=y&x_user=Dff3syMKTDQ2Rjf0jsvrT38ajqbrDQ63MZDDUv8WUmo=&ctoken=ecf5sfmcxsqc&need_popup=y&l_source=aliexpress; xman_f=0ahpD2ay1o45kW3NkynOIBPoBD92GaQFrsAHksOUV7GuN5B7ReHpDVdFVeyyEWABNPckueshvgmSq1se47L5EKZ4/wlaA1LRloRznF2xj56iNa5DlyRtFgDai2qr5fLexTkqHfEASnS870EuIXQz21I78hoq/D9/ug5DTUz7ES3U0RqQl3FzoXa4aOLUaKcBvtf39ADsvPmp1Suv/D/PQA9npZvakXZWsbc53/s4WGfjPqArHcn8oTNTmuGvvua/MxPxjew3Hy13ilySDHhnpTM76Rglg2ShZS7luOS3SYLIlm3psKjuo27wJReldJvC07AD04z6D27+X/N9cV5i8PMLrKy8qaGIIr2tYRvDSsHWU08ep4DhZvBagIGo86RyOSKpT4ssUYzn7/hYLpXIhMFqjjlelAkK6KDcbNLQVMo=; xman_us_f=zero_order=y&x_locale=en_US&x_l=1&last_popup_time=1564387489279&x_user=CN|CN|shopper|ifm|1861063758&no_popup_today=n; aep_usuc_f=site=glo&c_tp=USD&x_alimid=1861063758&isb=y&region=US&b_locale=en_US; _m_h5_tk=0ffe7cedc6f3e6ac8e8c146092566422_1564394978214; _m_h5_tk_enc=3b12bf4a0a4304d929b4dcffee0af2f4; JSESSIONID=BD40E32DA3397689B708E5C85345FC69; aep_history=keywords%5E%0Akeywords%09%0A%0Aproduct_selloffer%5E%0Aproduct_selloffer%0932994287234%0932955810487%0932934280221%0932964701608%0932934280221%0932964701608%0932994287234%0932964701608; intl_common_forever=fDiYUzFvcq2oyuKVMDbCGOjY/L7iOzLiv5hVb3SxQYPZIg+dy85KJA==; ali_apache_track=mt=1|ms=|mid=cn261343849rwfae; l=cBxuVc5qqMecYSR9BOfwSQKbaF7OmIOb4sPP2N7GzICPOh1wrUcfWZ3e8iLeCnGVp6hWR3rCLlQLBeYBqIcTIM3BtaxdC; isg=BAAA-ADXSf32cDXwl-6Peg250Y5-meQmlp5_zHqQw5uX9aAfIpkz4YPHCR2QxZwr; xman_t=fvWLVy5wH1jkHAtD26xaFKmLN9VAqNpVz7UAr4KxZCrLx9SCucm1ofvS/kHpfLa2++6iFcUhcZ9Fs26u0oYeGUP7OYKHjAD40bCKEAaaNUfS0LDQOmIkfvGOxV5DUA68px+r1AsKo9iodHTOMDEN2eLu0jii4AVSMKV3+pERSFfP6vS6+rcokyMVFhFO/NLmbCQrlv1Hwglx5DgCH1pOsEBDW5P8w0RRgKvJoY0gN6rGvWGuTdWOyPEoJloEgZhTicKUF1PfvY+vSat9HgL/rhTjhiY8RV1MFnwXnPomBB1+uB2rRv4d/DcEAL4iJ4x00OcMB7vBWwfoVvpVEGkQjId6lVuVFQmLaGcUE1feJQbb+Qi8zO5nnwTWPcBds+CAfysB3pwbhqtDt0Nw2CJ3bWefj5xzJoZhEgOae6darUr5GR6YEwtLnBlGkQ2niATj1WD6etNxPPqdKuI8+brxkR1a8/Gc247ASljEhBU+ZMeZd1P5AB4pS53lmRFGtataLVty/9N2/jLWovckpc5Ay+XrxXUpHddIwixCromy/5WlTGojq01qzFVXKl4Vqs30moo0nJ1QOxSduQ7ctVcCs5W6GZbOtm3e8cSvTGtw0av73pCUH/IS4OxWpIQc7EJkIInd4MkTzWlTj8Tfw4uBmw==",
        # }
        # for key, value in headers.items():
        #     cap['phantomjs.page.customHeaders.{}'.format(key)] = value
        # self.driver = webdriver.PhantomJS(desired_capabilities=cap,service_args=service_args)
        # self.driver = webdriver.PhantomJS(service_args=service_args)

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
                        err_info = '__clawlerProtect__driver.get() reloading for %d time' % count if count == 1 else '__clawlerProtect__driver.get() reloading for %d times' % count
                        print(err_info)
                        count += 1
                if count > 5:
                    print("__clawlerProtect__driver.get() job failed!")

            js = "var q=document.documentElement.scrollTop=100"
            self.driver.execute_script(js)
            time.sleep(random.randint(1, 2))
            # 设置滚动条，让数据加载完全
            js = "var q=document.documentElement.scrollTop=1000"
            self.driver.execute_script(js)
            time.sleep(random.randint(1,2))
            product_html = self.driver.page_source
            title = self.driver.title
            cookie = ''
            for cookie_data in self.driver.get_cookies():
                cookie += str(cookie_data['name']) + '=' + str(cookie_data['value']) + ';'
            return product_html, cookie, title
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
            product_info['product_name'] = data['titleModule']['subject']
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
                description_html = etree.tostring(div_element[0], encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
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
                description_html = description_html.format(*description_img_dir)
                product_info['description_img'] = [(img_url,img_dir) for img_url,img_dir in zip(description_img_url,description_img_dir)]
                # 推荐商品
                # recommend_products = product_html.xpath('//div[@style="max-width: 650.0px;overflow: hidden;font-size: 0;clear: both;"]')
                # sub_html = etree.tostring(recommend_products[0], encoding="utf-8", pretty_print=True, method="html").decode('utf-8')
                # product_info['description'] = description_html.replace(sub_html,'')
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
                att_data = price_data['skuPropIds'].split(',')
                att_data = [y['attr_value'][x] for x,y in zip(att_data,attr_list)]
                if attr_list[0]['attr_img']:
                    att_imgUrl = attr_list[0]['attr_img'][att_data[0]]
                else:
                    att_imgUrl = ''
                att_data = ','.join(att_data)
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

        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(product_link)
            with open('html'+str(random.randint(1,1000))+'.html','w', encoding='utf-8') as file:
                file.write(html)
            # err: 'NoneType' object has no attribute 'group'
            traceback.print_exc()
        return product_info

    # 滑块验证
    def slide_to_verify(self, product_link):
        pass

    def get_proxy(self):

        # 代理服务器
        proxyHost = "http-dyn.abuyun.com"
        proxyPort = "9020"

        # 代理隧道验证信息
        proxyUser = "HIL217ZFCDHGJ6FD"
        proxyPass = "1375697BCADCD8BB"

        proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
            "host": proxyHost,
            "port": proxyPort,
            "user": proxyUser,
            "pass": proxyPass,
        }

        proxies = {
            "http": proxyMeta,
            # "https": proxyMeta,
        }

        return proxies

    # 通过requests请求数据
    def __request__(self, product_link, product_attr_asin, cookie):
        try:
            replace_str = 'dp/' + product_attr_asin + '/ref'
            product_link = re.sub(r'dp/(.+)/ref',replace_str,product_link) + '&th=1&psc=1'
            res_match = re.search(r'qid=(\d+)&refinements=(.+)&s=(.+)&sr=(.+)', product_link)
            post_data = {
                "qid": res_match.group(1),
                "refinements": res_match.group(2),
                "s": res_match.group(3),
                "sr": res_match.group(4),
                "th": "1",
                "psc": "1",
            }
            headers = {
                "Host": "www.aliexpress.com",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60",
                # "User-Agent": get_useragent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                "Referer": "www.aliexpress.com",
                # "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Cookie": "ali_apache_id=10.103.166.17.1563934057953.180428.7; cna=Cpy9FdvlwGsCAXd7hZnAY+nZ; _ga=GA1.2.1037382476.1563934063; _bl_uid=mbjU5yznjjetqgp0ernnogR07s5O; _uab_collina=156412850518171280323644; _m_h5_tk=b51f3fe5eae7c0af5337ba6e0ffcf114_1564371945886; _m_h5_tk_enc=4f193789c1fb06f1f4734b6502eef1e7; _gid=GA1.2.1380136896.1564362589; intl_locale=en_US; acs_usuc_t=acs_rt=6660d304dffb4e8ea7ce88c68c3ff3db&x_csrf=12ahlddf1rc82; XSRF-TOKEN=948f5c91-efe9-45e8-aeba-fbd29546662a; JSESSIONID=B189F2086C79DD1588D8CC0A246E1128; aep_history=keywords%5E%0Akeywords%09%0A%0Aproduct_selloffer%5E%0Aproduct_selloffer%0932982476715%0933012393862%0932982476715%0932964701608%0933026112079%0932964701608%0933026112079%0933002113837; _mle_tmp_enc0=Ey%2Fp8LswzxA3J47VsqxI%2BxsW0U%2Fzg%2BnhJa7ta1q6pqZjj3LOveiVHhgUwuo%2FJu6TZXAc53MkqXx6oXBPl5EcTgBONVQciMcvXU7kVl7bx2pjIQcm%2BLfLuxL6Ax65GVXk; xman_us_t=x_lid=cn261343849rwfae&sign=y&x_user=Dff3syMKTDQ2Rjf0jsvrT4LV/yMnw6CfEWBQSQEMWts=&ctoken=18k_e0bs4vx5f&l_source=aliexpress; aep_usuc_t=ber_l=A0; aep_common_f=VjR+npTVveoBmRxPay48IN6WNrDS1AcIWlI0OxV+4Ildejg/87CTVQ==; xman_f=aGta0qTFbrwxjIgbPZbVsgZ+WaeudAIxkrVctUiL3VSh5VkDJi8fFJL11ikL+hPHvrh1G3xbsnF798cgKCDllZnjHCklnN4ih6/zPIbHdtMAmbG4ZZxnSOdYKKWv5Vm2xj6sggEJI/+BUvW2JkvnE/BZjbwLqzWggAbG2BJsjm2lXzQBD/ihaXN8Zrl4BE+Q8XMaN5w8p2Gp+zHFPpUTSwsBPhrpZ+fCAotkTWEUqrT18PdYJwi0UsQqpueauO8vW8c20gnMJ8cLU02ZnQcjzHORQd0M/olsNcyRYtncEhKz4OEPbx7qNlUXQk+7elNeuobhE6W3a6TAyFl7DVzpWg2HRDcmPDhnRLCjxi0AJU0=; xman_us_f=zero_order=y&x_locale=en_US&x_l=1&x_user=CN|CN|shopper|ifm|1861063758; aep_usuc_f=site=glo&c_tp=USD&x_alimid=1861063758&isb=y&region=US&b_locale=en_US; ali_apache_tracktmp=W_signed=Y; intl_common_forever=3MfbAyZk9mgz01dS33+lH0mkD05jwt19U0W4Nu8yezj8NvMHGstyYg==; l=cBxuVc5qqMecYL_tBOCNZQKbaF7OdIRAguSJGNcvi_5CB1L1jtQOk2ypHep6cjWdtf8B4k6UXwp9-etkifeGv2Gv5mP5.; isg=BBUVRQhn5GphK8CfugWyTRjCJBFjAslRgzXq45e6_gzb7jXgX2eP9LmsvLJ9buHc; ali_apache_track=mt=1|ms=|mid=cn261343849rwfae; xman_t=1yQHQbRNavaWrniP6DxTfSDGas3L/Qf+Rg3UMNVb2h7Lewn992tiTV+RTd9xWYbmRnDFBUSCC1al932Qf6mmriS6KRZwWWyP5oGSpVPJP2QBQOGfhPQUQSWru3z5x6f2htbFIisAQKvHMYcVsuip5GXQahbpX3t/FdMnG/mIX6N7XW3cBQRI3oZ1xx9llqH/K/nKbe2ZjIV+NXaYA8PDHvKR969DCnIjDDxwsK3q4I4nKPje4wSH2I2x9K+UHyaeclbGsYYW/n5gbBqzCGDPjmXx7vzK0yanKmMTbgVtoqc5xLcZ3OfacIVrxIqBj6gPMMcDSiLdGMUG0EG5hBUS1s50vvh4GXju5Rc5pcAZ/nCOEZjKefgy+QIPue3k5/by9Tan9rMGJCeFQlxUuqB70O70zQs4vN4G/Hr9+HtRmhAHpAyI5LYNHAGJKDOsojEOREPghmZHoPZwdLEn0K/+sYJ+S6HysEVhH6Wbw5FgUOT6xCqdwqUi0HWSqkhMeWYIoHUMvMlYLuRLuJUrXfNAtsaZaSAlIP+I7yFT9hD7exXFWeFWtHBdgOhKrdcZLc18hkrPwFbvMVdj46WC8xiZxAiNn4R32A07v0nvCwdP3NPUx0O3twQhZVwcItZWxZIlIyUi2ocueJc=",
            }

            # proxies = self.get_proxy()
            # s = requests.session()
            # s.keep_alive = False
            # html = s.post(product_link, headers=headers, proxies = proxies, data = post_data).text

            try:
                res = requests.post(product_link, headers=headers, data=post_data, verify = False, timeout=30)
                # res_txt = requests.get(url="http://icanhazip.com/", proxies=proxies).text
                # res = requests.post(product_link, headers=headers, data=post_data, verify = False, timeout=30, proxies = proxies)
            except:
                count = 1
                while count <= 5:
                    try:
                        res = requests.post(product_link, headers=headers, data=post_data, verify=False, timeout=30)
                        # res = requests.post(product_link, headers=headers, data=post_data, verify=False, timeout=30,proxies=proxies)
                        break
                    except:
                        err_info = '__request__ reloading for %d time' % count if count == 1 else '__request__ reloading for %d times' % count
                        print(err_info)
                        count += 1
                if count > 5:
                    print("__request__ job failed!")

            html = res.text
            return html, product_link
        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(err)
            traceback.print_exc()

    def __query_product__(self, product_id):
        sql = 'select id from amazonshop_goods WHERE ASIN = \'%s\' ' % product_id
        res = self.mysql.select(sql)
        if res:
            return True
        else:
            return False
        pass

    # 商品数据采集
    def clawer(self,product_link):
        try:

            print('正在爬取商品：', product_link)
            product_html, cookie, title = self.__clawlerProtect__(product_link)
            product_info = self.__parseProduct__(product_html, product_link)
            # 查询库中是否有该商品的数据
            flag = self.__query_product__(product_info['product_id'])
            flag = 0
            if not flag:
                product_info = self.__save_img__(product_info)
                self.product_info_queue.put(product_info)
            else:
                print('商品已存在：{product_id:%s}'%product_info['product_id'])

        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(err)
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
            socket.setdefaulttimeout(30)
            for img_data in (img_list + att_img_list + description_img_list):
                img_url = img_data['img_url']
                img_dir = img_data['img_dir']
                try:
                    urllib.request.urlretrieve(img_url, img_dir)
                except:
                    count = 1
                    while count <= 5:
                        try:
                            urllib.request.urlretrieve(img_url, img_dir)
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
                product_link = self.product_link_queue.get()
                self.clawer(product_link)
            print('退出：', self.threadName)
            self.driver.quit()
        except Exception as err:
            print(err)

class ThreadParse(Thread):

    def __init__(self, i, user_id, product_info_queue, product_total, url, source):
        Thread.__init__(self)
        self.user_id = user_id
        self.source = source
        self.url = url
        self.product_total = product_total
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
            dimension, export_name,dimension)
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
                for attr_value in attr_data['att_data'].split(','):
                    sql = 'select id from amazonshop_attrcategoryvalue where attr_value = \"%s\" ' % attr_value
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
            print(err)
            traceback.print_exc()

    def __save_process__(self, num):

        # 更新数据库的采集进度
        sql = 'update amazonshop_usershopsurl set sum = %s, num = %s WHERE  shop_url = %s'
        self.mysql.update(sql,[(self.product_total, num, self.url)])

        # 更新当前的采集进度（web展示）
        content = {"shop_url":self.url,"total":self.product_total,"number":num,"user_id":self.user_id}
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

                # 保存采集进度
                global num
                num += 1
                self.__save_process__(num)
                print('写入商品：', product_info['product_id'],product_info['product_name'])
                self.__save_data__(product_info)

            print('退出：',self.threadName)
        except Exception as err:
            print(err)

class GetAllProductsLink(object):

    def __init__(self, url, product_link_queue):
        '''
        :param url: 店铺链接
        :param product_link_queue: 商品链接队列
        '''
        self.url = url
        self.product_link_queue = product_link_queue

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
        # 创建浏览器对象
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        # 设置页面最大加载时间
        self.driver.set_page_load_timeout(10)
        # 默认打开登录页面
        # self.driver.get('https://login.aliexpress.com/')

    # 打开当前页面，返回当前页面的商品列表
    def __clawer__(self, url):
        try:

            # try:
            #     self.driver.get(url)
            # except:
            #     count = 1
            #     while count <= 5:
            #         try:
            #             self.driver.get(url)
            #             break
            #         except:
            #             err_info = '__clawer__driver.get() reloading for %d time' % count if count == 1 else '__clawer__driver.get() reloading for %d times' % count
            #             print(err_info)
            #             count += 1
            #     if count > 5:
            #         print("__clawer__driver.get() job failed!")

            current_url = self.driver.current_url
            # 再次登录
            if 'login.aliexpress.com' in current_url:
                print('login.aliexpress.com--需要再次登录！')
                try:
                    # 切换到iframe（否则获取不到元素）
                    self.driver.switch_to_frame("alibaba-login-box")
                    self.driver.find_element_by_xpath('//*[@id="login"]/div/div/div[3]/button').click()
                except:
                    pass
                # self.__login__()
                try:
                    self.driver.get(url)
                except:
                    pass
            title = self.driver.title
            # 滑块验证
            if title == 'AliExpress.com':
                print('AliExpress.com--滑块验证！')
                time.sleep(random.randint(1, 2))
                self.slide_to_verify()
                self.driver.refresh()
                self.driver.delete_all_cookies()
                self.driver.refresh()
                time.sleep(random.randint(1,2))
                try:
                    # 切换到iframe（否则获取不到元素）
                    self.driver.switch_to_frame("alibaba-login-box")
                    self.driver.find_element_by_xpath('//*[@id="login"]/div/div/div[3]/button').click()
                except:
                    pass

            # time.sleep(random.random())
            # self.driver.refresh()
            # time.sleep(random.random())
            # self.slide_to_verify()
            # time.sleep(random.random())
            # self.driver.refresh()

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
            html = etree.HTML(html_source)
            products_list = html.xpath("//ul[@class='items-list util-clearfix']/li/div[1]/div[1]/a/@href")
            return products_list, html, title
        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(err)
            traceback.print_exc()

    def __set_cookies__(self):
        for cookie_data in self.driver.get_cookies():
            if cookie_data['name'] != 'umdata_':
                self.driver.add_cookie(cookie_data)
                # cookies += cookie_data + '=' + str(cookie_data['value']) + ';'

    def __get_account__(self):
        account_list = [
            {'account_name':'97565476@qq.com','account_password':'123456qwe'},
            {'account_name':'382770108@qq.com','account_password':'123456Qwe'},
        ]
        account = random.choice(account_list)
        return account['account_name'], account['account_password']

    def __login__(self):
        try:
            # # 登录页面
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
            # self.driver.find_element_by_xpath('//*[@id="fm-login-password"]').send_keys('123456qwe')
            # self.driver.find_element_by_xpath('//*[@id="fm-login-password"]').send_keys('123456Qwe')
            time.sleep(random.randint(2, 3))
            try:
                self.driver.find_element_by_xpath('//*[@id="nc_1_n1z"]')
                self.slide_to_verify()
            except:
                pass
            # 点击登录
            self.driver.find_element_by_xpath('//*[@id="login-form"]//button').click()
            time.sleep(random.randint(5,8)) # 多等一会，否则报错
            js = "var q=document.documentElement.scrollTop=2000"
            self.driver.execute_script(js)
            time.sleep(random.randint(1,2))

        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(err)

    # 获取当前页面每件商品的链接
    def __getProductlink__(self, url):
        '''
        :param url: 店铺当前页的url
        :return: 返回当前页面的下一页链接
        '''
        try:
            # 获取产品列表（网站打开默认是中文，要转换成英文）
            products_list, html, title = self.__clawer__(url)
            next_url = self.__click_nextPage__(html)
            # next_url = self.__getNextPage__(html)
            for product in products_list:
                protuct_link = str(product).replace('//','')
                protuct_link = 'https://www.aliexpress.com/item/' + re.search(r'_(\d+\.html)', protuct_link).group(1)
                self.product_link_queue.put(protuct_link)
            return  next_url
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

    def __click_nextPage__(self,html):
        try:
            # 获取下一页url
            next_ = html.xpath('//a[@class="ui-pagination-next"]/@href')
            if next_:
                next_url = 'https:' + str(html.xpath('//a[contains(text(),"Next")]/@href')[0])
                try:
                    self.driver.find_element_by_xpath('//a[@class="ui-pagination-next"]').click()
                except:
                    pass
                return next_url
            else:
                return False
        except Exception as err:
            mylog.logs().exception(sys.exc_info())
            print(err)
            traceback.print_exc()

    # 滑块验证
    def slide_to_verify(self):
        slide_button = self.driver.find_element_by_xpath('//*[@id="nc_1_n1z"]')
        slide_div = self.driver.find_element_by_xpath('//*[@id="nc_1__scale_text"]')
        slide_length = slide_div.size['width'] - slide_button.size['width']
        tracks = self.__get_track__(slide_length)
        self.__move_to_gap__(slide_button, tracks)

    def __get_track__(self, distance):  # distance为传入的总距离
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 4 / 5
        # 计算间隔
        t = 0.3
        # 初速度
        v = 0

        while current < distance:
            if current < mid:
                # 加速度为2
                a = 2
            else:
                # 加速度为-2
                a = -3
            v0 = v
            # 当前速度
            v = v0 + a * t
            # 移动距离
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
        return track

    def __move_to_gap__(self, slider, tracks):  # slider是要移动的滑块,tracks是要传入的移动轨迹
        ActionChains(self.driver).click_and_hold(slider).perform()
        for x in tracks:
            ActionChains(self.driver).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.driver).release().perform()

    def run(self):
        '''
        :return: 返回店铺的所有商品链接
        '''
        # 店铺总链接（默认店铺的第一页链接）
        # print('正在爬取店铺：', self.url)
        next_url = self.url
        self.__login__()
        try:
            self.driver.get(next_url)
        except:
            pass
        # 循环遍历店铺的所有商品页
        for i in range(100):
            if next_url:
                print('正在获取该页面下的所有商品链接：',next_url)
                next_url = self.__getProductlink__(next_url)
            else:
                if next_url == 'Sorry':
                    print('获取链接失败！')
                else:
                    print('已获取店铺所有商品的链接！')
                self.driver.quit()
                break

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
num = 0


def main(url,user_id,source):

    # 店铺链接转换（通过链接直接获取店铺下的所有商品）
    if 'all-wholesale-products' not in url:
        store_url = url
        sub_str = 'store/all-wholesale-products/' + re.search(r'/(\d+)\?', store_url).group(1) + '.html'
        all_products_url = store_url.replace(store_url[store_url.index('store'):], sub_str)
    else:
        all_products_url = url

    # 商品链接队列
    product_link_queue = Queue()
    # 商品信息队列
    product_info_queue = Queue()

    get_all_products_link = GetAllProductsLink(all_products_url, product_link_queue)
    get_all_products_link.run()


    # product_link_queue.put('https://www.aliexpress.com/item/32955725064.html')

    # 商品总数
    product_total = product_link_queue.qsize()

    if not product_link_queue.empty():

        # 存储3个采集线程的列表集合
        threadcrawl = []
        for i in range(1):
            thread = ThreadClawerAliExpress(i, product_link_queue, product_info_queue, user_id)
            thread.start()
            threadcrawl.append(thread)

        # 存储1个解析线程
        threadparse = []
        for i in range(3):
            thread = ThreadParse(i, user_id, product_info_queue, product_total, url, source)
            thread.start()
            threadparse.append(thread)

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

    else:
        print('数据采集失败！')


if __name__ == '__main__':

    url = 'https://www.aliexpress.com/store/all-wholesale-products/4651052.html?spm=2114.12010615.pcShopHead_35211393.99' # 16
    # url = 'https://www.aliexpress.com/store/all-wholesale-products/3100086.html?spm=a2g1y.12024536.pcShopHead_53137125.99' # 20
    # url = 'https://www.aliexpress.com/store/2788034?spm=a2g0o.detail.100005.2.1f9e6cfeLeu0TU' #82

    main(url,user_id=1,source=2)

