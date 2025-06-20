import datetime
import json
import random
import re
import time

import requests
import os

'''
# 监听本地代理
proxies = {
    'http': 'http:127.0.0.1:10809',
    'https': 'http:127.0.0.1:10809'
}
'''


# 出错自动重试
def retry(attempt):
    def decorator(func):
        def wrapper(*args, **kw):
            att = 0
            while att < attempt:
                try:
                    return func(*args, **kw)
                except Exception as e:
                    print('发生错误; 正在重试 ' + str(datetime.datetime.now()))
                    att += 1

        return wrapper

    return decorator


# 出错自动重试的下载请求
@retry(attempt=5)
def getResponse(sess, ref, url):
    sleeptime = random.randint(0, 3)
    time.sleep(sleeptime)
    header = {'Referer': ref}
    # 取消监听本地代理端口
    # r = sess.get(url, headers=header, proxies = proxies)
    r = sess.get(url, headers=header)
    return r.content


# 带重试的HTTP get
@retry(attempt=5)
def rGet(sess, url):
    sleeptime = random.randint(0, 3)
    time.sleep(sleeptime)
    # 取消监听本地代理端口
    # r = sess.get(url, proxies = proxies)
    r = sess.get(url)
    return r


# 抓取作品ID
def getIllustID(sess, s_list, sm_list, m_list, mm_list, u_list, unuseful_list, n):
    # sess:已登录的requests会话
    # s:单张图片list
    # sm:单张漫画list
    # m:多张图片list
    # mm:多张漫画list
    # u:动图List

    user_id = ''
    page_num = 1

    rest = 'show'
    # 自动根据userId查询收藏列表
    regix = re.compile(r'(?<=user_id=)\d*(?==)')
    stre = str(sess.cookies.get_dict())
    userIds = regix.findall(stre)
    if (userIds is None):
        print('未获取当前用户信息，请检查cookie ' + str(datetime.datetime.now()))
    else:
        user_id = userIds[0]

    if n == 0:
        while True:

            offset = (page_num - 1) * 48

            if rest == 'show':
                print(str(datetime.datetime.now()) + ' ' + '抓取公开收藏夹第 %d 页' % page_num)
            else:
                print(str(datetime.datetime.now()) + ' ' + '抓取非公开收藏夹第 %d 页' % page_num)
            r = rGet(sess,
                     'https://www.pixiv.net/ajax/user/%s/illusts/bookmarks?tag=&offset=%d&limit=48&rest=%s&lang=zh' % (
                         user_id, offset, rest))
            text = json.loads(r.text)
            works = text['body']['works']
            total = text['body']['total']
            for work in works:

                if (work['isMasked'] is True):
                    unuseful_list.append(work['id'])
                    continue

                if (work['illustType'] == 0):
                    if (work['pageCount'] == 1):
                        # 抓取单张图片类型的作品ID
                        s_list.append(work['id'])
                    else:
                        # 抓取多张图片类型的作品ID
                        m_list.append(work['id'])
                elif (work['illustType'] == 1):
                    if (work['pageCount'] == 1):
                        # 抓取单张漫画类型的作品ID
                        sm_list.append(work['id'])
                    else:
                        # 抓取多张漫画类型的作品ID
                        mm_list.append(work['id'])
                # elif (work['illustType'] == 2):
                #     # 抓取动态图片类型的作品ID
                #     u_list.append(work['id'])
                else:
                    print(str(datetime.datetime.now()) + ' ' + '未获取图片' + work['id'] + '类型')

            print(str(datetime.datetime.now()) + ' 本页共 ' + str(len(works)) + ' 张')
            # 判断是否存在下一页
            if (total <= (page_num * 48)):
                if rest == 'show':
                    print(str(datetime.datetime.now()) + ' ' + '抓取非公开收藏')
                    rest = 'hide'
                    page_num = 0
                else:
                    break
            page_num += 1
    else:
        page_num = n

        offset = (page_num - 1) * 48
        print(str(datetime.datetime.now()) + ' ' + '抓取公开收藏夹第 %d 页' % page_num)
        r_show = rGet(sess,
                 'https://www.pixiv.net/ajax/user/%s/illusts/bookmarks?tag=&offset=%d&limit=48&rest=%s&lang=zh' % (
                     user_id, offset, 'show'))

        text_show = json.loads(r_show.text)
        works_show = text_show['body']['works']
        for work in works_show:

            if (work['isMasked'] is True):
                unuseful_list.append(work['id'])
                continue

            if (work['illustType'] == 0):
                if (work['pageCount'] == 1):
                    # 抓取单张图片类型的作品ID
                    s_list.append(work['id'])
                else:
                    # 抓取多张图片类型的作品ID
                    m_list.append(work['id'])
            elif (work['illustType'] == 1):
                if (work['pageCount'] == 1):
                    # 抓取单张漫画类型的作品ID
                    sm_list.append(work['id'])
                else:
                    # 抓取多张漫画类型的作品ID
                    mm_list.append(work['id'])
            # elif (work['illustType'] == 2):
            #     # 抓取动态图片类型的作品ID
            #     u_list.append(work['id'])
            else:
                print(str(datetime.datetime.now()) + ' ' + '未获取图片' + work['id'] + '类型')

        print(str(datetime.datetime.now()) + ' 本页共 ' + str(len(works_show)) + ' 张')

        print(str(datetime.datetime.now()) + ' ' + '抓取非公开收藏夹第 %d 页' % page_num)
        r_hide = rGet(sess,
                      'https://www.pixiv.net/ajax/user/%s/illusts/bookmarks?tag=&offset=%d&limit=48&rest=%s&lang=zh' % (
                          user_id, offset, 'hide'))
        text_hide = json.loads(r_hide.text)
        works_hide = text_hide['body']['works']
        for work in works_hide:

            if (work['isMasked'] is True):
                unuseful_list.append(work['id'])
                continue

            if (work['illustType'] == 0):
                if (work['pageCount'] == 1):
                    # 抓取单张图片类型的作品ID
                    s_list.append(work['id'])
                else:
                    # 抓取多张图片类型的作品ID
                    m_list.append(work['id'])
            elif (work['illustType'] == 1):
                if (work['pageCount'] == 1):
                    # 抓取单张漫画类型的作品ID
                    sm_list.append(work['id'])
                else:
                    # 抓取多张漫画类型的作品ID
                    mm_list.append(work['id'])
            # elif (work['illustType'] == 2):1
            #     # 抓取动态图片类型的作品ID
            #     u_list.append(work['id'])
            else:
                print(str(datetime.datetime.now()) + ' ' + '未获取图片' + work['id'] + '类型')

        print(str(datetime.datetime.now()) + ' 本页共 ' + str(len(works_hide)) + ' 张')



# 取得指定作品ID的图片下载地址列表
def getPicUrls(sess, id, type='single'):
    # 作品类型: single: 单图; multi: 多图; ugoku: 动图
    # 返回格式: (来源页面 url; [图片1 url,图片2 url,图片3 url……])

    urls = []
    if type == 'single':
        # 如果是单图
        ref = 'https://www.pixiv.net/ajax/illust/%s?lang=zh' % id
        r = rGet(sess, ref)
        text = json.loads(r.text)
        a = text['body']['urls']['original']
        urls.append(a)
    elif type == 'multi':
        # 如果是多图
        ref = 'https://www.pixiv.net/ajax/illust/%s/pages?lang=zh' % id
        r = rGet(sess, ref)
        text = json.loads(r.text)
        for i in text['body']:
            a = i['urls']['original']
            urls.append(a)
    # elif type == 'ugoku':
    #     ref = 'https://www.pixiv.net/touch/ajax/illust/details?illust_id=%s' % id
    #     r = rGet(sess, ref)
    #     text = json.loads(r.text)
    #     a = text['body']['illust_details']['ugoira_meta']['src']
    #     urls.append(a)

    return ref, urls


def download(sess, ref, url, filename):
    # 创建目录
    pos = filename.rfind('/')
    if not os.path.exists(filename[:pos]):
        os.makedirs(filename[:pos])
    # 如果已经存在; 则不下载
    if os.path.exists(filename):
        print(str(datetime.datetime.now()) + ' 文件 ' + filename + ' 已存在' + ' ')
        return
    # 下载文件
    data = getResponse(sess, ref, url)
    with open(filename, "wb") as f:
        f.write(data)
        f.close()


def sDownload(sess, id, ref, url, type=''):
    # ref: 来源地址
    # type: 如果值为manga,则视为漫画类型
    # url: 图片的url
    print(str(datetime.datetime.now()) + ' 正在下载作品: ' + id + ' ')
    type_dir = 'single'
    if type == 'manga':
        type_dir = 'manga'
    # 取出地址
    url = url[0]
    # 得到扩展名
    pos = url.rfind('.')
    ext = url[pos:]
    download(sess, ref, url, 'pixiv/' + type_dir + '/' + id + ext)


def mDownload(sess, id, ref, urls, type=''):
    print(str(datetime.datetime.now()) + ' 正在下载多图作品: ' + id)
    type_dir = 'multi'
    if type == 'manga':
        type_dir = 'multi-manga'
    for index, url in enumerate(urls):
        # 得到扩展名
        pos = url.rfind('.')
        ext = url[pos:]
        download(sess, ref, url,'pixiv/' + type_dir + '/' + id + '/' + id + '_' + str(index + 1) + ext)


def uDownload(sess, id, ref, urls):
    print('正在下载动图作品: ' + id + ' ' + str(datetime.datetime.now()))
    type_dir = 'ugoku'
    for index, url in enumerate(urls):
        # 得到扩展名
        pos = url.rfind('.')
        ext = url[pos:]
        download(sess, ref, url, 'pixiv/' + type_dir + '/' + id + ext)


if __name__ == '__main__':

    cookie = ''
    with open("cfg.txt", encoding="gbk") as f:
        cookie = f.read()

    # 作品ID列表
    single_illust_id_list = []
    single_manga_illust_id_list = []
    multi_illust_id_list = []
    multi_manga_illust_id_list = []
    ugoku_illust_id_list = []
    unuseful_illust_id_list = []

    # 登录
    s = requests.session()
    for line in cookie.split("; "):
        name, value = line.strip().split("=", 1)
        s.cookies.set(name, value)
    s.headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"}


    print('输入需要下载的收藏第几页作品，回车默认下载全部收藏: ')
    n = 0
    input = input()
    if input != '':
        n = int(input)
    # 抓取收藏作品
    getIllustID(s, single_illust_id_list, single_manga_illust_id_list,
                multi_illust_id_list, multi_manga_illust_id_list,
                ugoku_illust_id_list, unuseful_illust_id_list, n)


    print('总共找到单图画作 %d 件; 单图漫画 %d 件; 多图画作 %d 件; 多图漫画 %d 件; 动图 %d 件; 失效稿件 %d 件。' %
          (len(single_illust_id_list), len(single_manga_illust_id_list),
           len(multi_illust_id_list), len(multi_manga_illust_id_list),
           len(ugoku_illust_id_list), len(unuseful_illust_id_list)) + ' ' + str(datetime.datetime.now()))

    # 判断本地是否存在作品，存在则从下载队列中排除

    # 获取下载地址
    # 格式:
    # {ID 1:(来源, [图片1, 图片2...]), ID 2:(来源, [图片])...}
    s_downlink = {}
    sm_downlink = {}
    m_downlink = {}
    mm_downlink = {}
    u_downlink = {}

    s_num = 1
    for id in single_illust_id_list:
        print(str(datetime.datetime.now()) + ' 正在获取第' + s_num.__str__() + '图片作品 ' + id.__str__() + ' 的下载地址' + ' ')
        s_downlink[id] = getPicUrls(s, id)
        s_num += 1

    sm_num = 1
    for id in single_manga_illust_id_list:
        print(str(datetime.datetime.now()) + ' 正在获取第' + sm_num.__str__() + '漫画作品 ' + id.__str__() + ' 的下载地址' + ' ')
        sm_downlink[id] = getPicUrls(s, id)
        sm_num += 1
    sm_num = 1

    m_num = 1
    for id in multi_illust_id_list:
        print(str(datetime.datetime.now()) + ' 正在获取第' + m_num.__str__() + '多图作品 ' + id.__str__() + ' 的下载地址' + ' ')
        m_downlink[id] = getPicUrls(s, id, 'multi')
        m_num += 1

    mm_num = 1
    for id in multi_manga_illust_id_list:
        print(tr(datetime.datetime.now()) + ' 正在获取第' + mm_num.__str__() + '多图漫画作品 ' + id.__str__() + ' 的下载地址' + ' ')
        mm_downlink[id] = getPicUrls(s, id, 'multi')
        mm_num += 1

    u_num = 1
    for id in ugoku_illust_id_list:
        print(str(datetime.datetime.now()) + ' 正在获取第' + u_num.__str__() + '动图作品 ' + id + ' 的下载地址' + ' ')
        u_downlink[id] = getPicUrls(s, id, 'ugoku')
        u_num += 1

    # 开始下载
    for id, (ref, url) in s_downlink.items():
        sDownload(s, id, ref, url, 'single')

    for id, (ref, url) in sm_downlink.items():
        sDownload(s, id, ref, url, 'manga')

    for id, (ref, url) in m_downlink.items():
        mDownload(s, id, ref, url, 'single')

    for id, (ref, url) in mm_downlink.items():
        mDownload(s, id, ref, url, 'manga')

    for id, (ref, url) in u_downlink.items():
        uDownload(s, id, ref, url)
