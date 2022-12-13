#! python3
# coding:utf-8
import json

import requests
import os

# 出错自动重试
def retry(attempt):
    def decorator(func):
        def wrapper(*args, **kw):
            att = 0
            while att < attempt:
                try:
                    return func(*args, **kw)
                except Exception as e:
                    print('发生错误; 正在重试')
                    att += 1

        return wrapper

    return decorator

# 出错自动重试的下载请求
@retry(attempt=5)
def getResponse(sess, ref, url):
    header = {'Referer': ref}
    r = sess.get(url, headers=header)
    return r.content


# 带重试的HTTP get
@retry(attempt=5)
def rGet(sess, url):
    r = sess.get(url)
    return r


# 抓取作品ID
def getIllustID(sess, s_list, sm_list, m_list, mm_list, u_list):
    # sess:已登录的requests会话
    # s:单张图片list
    # sm:单张漫画list
    # m:多张图片list
    # mm:多张漫画list
    # u:动图List
    page_number = 1
    offset = (page_number - 1) * 48
    rest = 'show'
    while True:
        # TODO 修改逻辑; 自动根据userId查询收藏列表
        r = rGet(sess,
                 'https://www.pixiv.net/ajax/user/15455201/illusts/bookmarks?tag=&offset=%d&limit=48&rest=%s&lang=zh' % (
                     offset, rest))

        if rest == 'show':
            print('正在浏览公开收藏夹第 %d 页' % page_number)
        else:
            print('正在浏览非公开收藏夹第 %d 页' % page_number)
        text = json.loads(r.text)
        works = text['body']['works']
        total = text['body']['total']
        for work in works:
            if (work['illustType'] == 0):
                if (work['pageCount'] == 1):
                    # 抓取单张图片类型的作品ID
                    s_list.append(work['id'])
                else:
                    # 抓取多张图片类型的作品ID
                    m_list.append(work['id'])
            elif(['illustType'] == 2):
                if (work['pageCount'] == 1):
                    # 抓取单张漫画类型的作品ID
                    sm_list.append(work['id'])
                else:
                    # 抓取多张漫画类型的作品ID
                    mm_list.append(work['id'])
            elif (['illustType'] == 3):
                # 抓取动态图片类型的作品ID
                u_list.append(work['id'])
        # u_list.extend(ugoku_list)

        # 判断是否存在下一页
        if (total <= (page_number * 48)):
            if rest == 'show':
                print('抓取非公开收藏')
                rest = 'hide'
                page_number = 0
            else:
                break
        page_number += 1


# 取得指定作品ID的图片下载地址列表
def getFileLinkList(sess, id, type='single'):
    # sess: 已登录的requests会话
    # id: 作品ID
    # type: 作品类型：single：单图; multi：多图; ugoku：动图
    # 返回格式：(来源页面 url; [图片1 url,图片2 url,图片3 url……])

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
        text=json.loads(r.text)
        for i in text['body']:
            a = i['urls']['original']
            urls.append(a)

    return ref,urls
    # elif type == 'ugoku':
    #     # 如果是动图
    #     ref = 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id=%s' % id
    #     r = rGet(sess, ref)
    #     regx = r'pixiv.context.ugokuIllustFullscreenData  = {"src":"(\S+?)"'
    #     temp_list = [url.replace('\\', '') for url in re.findall(regx, r.text)]
    #     return ref, temp_list


def download(sess, ref, url, filename):
    # 创建目录
    pos = filename.rfind('/')
    if not os.path.exists(filename[:pos]):
        os.makedirs(filename[:pos])
    # 如果已经存在; 则不下载
    if os.path.exists(filename):
        print('跳过文件 ' + filename)
        return
    # 下载文件
    data = getResponse(sess, ref, url)
    with open(filename, "wb") as f:
        f.write(data)
        f.close()


def sDownload(sess, id, ref, url, type=''):
    # ref：来源地址
    # type：如果值为manga,则视为漫画类型
    # url：图片的url
    print('正在下载作品：' + id)
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
    print('正在下载多图作品：' + id)
    type_dir = 'multi'
    if type == 'manga':
        type_dir = 'multi-manga'
    for index, url in enumerate(urls):
        # 得到扩展名
        pos = url.rfind('.')
        ext = url[pos:]
        download(sess, ref, url,
                 'pixiv/' + type_dir + '/' + id + '/' + id + '_' + str(index + 1) + ext)


def uDownload(sess, id, ref, urls):
    print('正在下载动图作品：' + id)
    type_dir = 'ugoku'
    for index, url in enumerate(urls):
        # 得到扩展名
        pos = url.rfind('.')
        ext = url[pos:]
        download(sess, ref, url, 'pixiv/' + type_dir + '/' + id + ext)


if __name__ == '__main__':
    cookie = input('请输入cookie：')

    # 作品ID列表
    single_illust_id_list = []
    single_manga_illust_id_list = []
    multi_illust_id_list = []
    multi_manga_illust_id_list = []
    ugoku_illust_id_list = []

    # 登录
    s = requests.session()
    for line in cookie.split("; "):
        name, value = line.strip().split("=", 1)
        s.cookies.set(name, value)
    s.headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"}
    # 抓取
    getIllustID(s, single_illust_id_list, single_manga_illust_id_list,
                multi_illust_id_list, multi_manga_illust_id_list, ugoku_illust_id_list)

    print('总共找到单图画作 %d 件; 单图漫画 %d 件; 多图画作 %d 件; 多图漫画 %d 件; 动图 %d 件。' %
          (len(single_illust_id_list), len(single_manga_illust_id_list),
           len(multi_illust_id_list), len(multi_manga_illust_id_list),
           len(ugoku_illust_id_list)))

    # 获取下载地址
    # 格式:
    # {ID 1:(来源, [图片1, 图片2...]), ID 2:(来源, [图片])...}
    s_downlink = {}
    sm_downlink = {}
    m_downlink = {}
    mm_downlink = {}
    u_downlink = {}

    for id in single_illust_id_list:
        print('正在获取图片作品 ' + id + ' 的下载地址')
        s_downlink[id] = getFileLinkList(s, id)

    for id in single_manga_illust_id_list:
        print('正在获取漫画作品 ' + id + ' 的下载地址')
        sm_downlink[id] = getFileLinkList(s, id)

    for id in multi_illust_id_list:
        print('正在获取多图作品 ' + id + ' 的下载地址')
        m_downlink[id] = getFileLinkList(s, id, 'multi')

    for id in multi_manga_illust_id_list:
        print('正在获取多图漫画作品 ' + id + ' 的下载地址')
        mm_downlink[id] = getFileLinkList(s, id, 'multi')

    for id in ugoku_illust_id_list:
        print('正在获取动图作品 ' + id + ' 的下载地址')
        u_downlink[id] = getFileLinkList(s, id, 'ugoku')

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
