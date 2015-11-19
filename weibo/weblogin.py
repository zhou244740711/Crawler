# -*- coding: utf8 -*-
__author__ = 'fangc'
# http://www.idataskys.com/python%E6%A8%A1%E6%8B%9F%E5%BE%AE%E5%8D%9A%E7%99%BB%E9%99%86%E5%B9%B6%E6%8A%93%E5%8F%96%E5%BE%AE%E5%8D%9A%E7%9B%B8%E5%85%B3%E6%95%B0%E6%8D%AE/
import urllib2
import urllib
import cookielib
import sqlite3
import lxml.html as HTML
from lxml.html import soupparser
import random

class Fetcher(object):
    def __init__(self, username=None, pwd=None, cookie_filename=None):
        self.cj = cookielib.LWPCookieJar()
        if cookie_filename is not None:
            self.cj.load(cookie_filename)
        self.cookie_processor = urllib2.HTTPCookieProcessor(self.cj)
        self.opener = urllib2.build_opener(self.cookie_processor, urllib2.HTTPHandler)
        urllib2.install_opener(self.opener)

        self.username = username
        self.pwd = pwd
        self.headers = {'User-Agent': random.choice(['Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0.1', 'Mozilla/5.0 (Linux; Android 4.3; Nexus 10 Build/JSS15Q) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2307.2 Safari/537.36']),
                        'Referer':'','Content-Type':'application/x-www-form-urlencoded'}


    def get_rand(self, url):
        headers = {'User-Agent':'Mozilla/5.0 (Windows;U;Windows NT 5.1;zh-CN;rv:1.9.2.9)Gecko/20100824 Firefox/3.6.9',
                   'Referer':''}
        req = urllib2.Request(url ,urllib.urlencode({}), headers)
        resp = urllib2.urlopen(req)
        login_page = resp.read()
        rand = HTML.fromstring(login_page).xpath("//form/@action")[0]
        passwd = HTML.fromstring(login_page).xpath("//input[@type='password']/@name")[0]
        vk = HTML.fromstring(login_page).xpath("//input[@name='vk']/@value")[0]
        return rand, passwd, vk

    def login(self, username=None, pwd=None, cookie_filename=None):
        if self.username is None or self.pwd is None:
            self.username = username
            self.pwd = pwd
        assert self.username is not None and self.pwd is not None

        url = 'http://login.weibo.cn/login/?ns=1&revalid=2&backURL=http%3A%2F%2Fweibo.cn%2F&backTitle=%CE%A2%B2%A9&vt='
        rand, passwd, vk = self.get_rand(url)
        data = urllib.urlencode({'mobile': self.username,
                                 passwd: self.pwd,
                                 'remember': 'on',
                                 'backURL': 'http://weibo.cn/',
                                 'backTitle': '新浪微博',
                                 'vk': vk,
                                 'submit': '登录',
                                 'encoding': 'utf-8'})
        url = 'http://3g.sina.com.cn/prog/wapsite/sso/' + rand
        req = urllib2.Request(url, data, self.headers)
        resp = urllib2.urlopen(req)
        page = resp.read()
        link = HTML.fromstring(page).xpath("//a/@href")[0]
        if not link.startswith('http://'): link = 'http://weibo.cn/%s' % link
        req = urllib2.Request(link, headers=self.headers)
        urllib2.urlopen(req)
        if cookie_filename is not None:
            self.cj.save(filename=cookie_filename)
        elif self.cj.filename is not None:
            self.cj.save()
        print 'login success!'

    def fetch(self, url):
        print 'fetch url: ', url
        req = urllib2.Request(url, headers=self.headers)
        return urllib2.urlopen(req).read()


class Database(object):
    def __init__(self):
        self.con = sqlite3.connect("/home/database/weibo.db")
        self.cur = self.con.cursor()

    def __del__(self):
        self.con.commit()
        self.cur.close()
        self.con.close()

    def geturls(self):
        l = set()
        self.cur.execute("select url from weibo")
        results = self.cur.fetchall()
        for result in results:
            l.add(result[0])
        return list(l)


    def createtable(self):
        self.cur.execute("create table weibo(id integer primary key,url VARCHAR(255) UNIQUE , keys VARCHAR(255), username varchar(100), email varchar(100))")
        self.con.commit()

    def insert(self, url, keys, username, email):
        self.cur.execute("insert into weibo(url, keys, username) values('%s','%s','%s','%s')" % (url, keys, username, email))
        self.con.commit()

    def getkeys(self, url):
        self.cur.execute("select keys from weibo where url = '%s'" % url)
        result = self.cur.fetchone()
        return result[0]

    def update(self, url, keys):
        self.cur.execute("update weibo set keys = '%s' where url='%s'" % (keys, url))
        self.con.commit()

    def isinurls(self, url):
        if url in self.geturls():
            return True
        else:
            return False

    def isinkeys(self, url, key):
        if key in self.getkeys(url):
            return True
        else:
            return False


def main():
    login = Fetcher(username='', pwd='')
    database = Database()
    login.login()
    urls = database.geturls()
    for url in urls:
        text = login.fetch(url)
        soup = soupparser.fromstring(text)
        hrefs = soup.xpath(".//div[@class='c']")
        ids = set()
        for i in hrefs:
            try:
                ids.add(i.attrib['id'])
            except KeyError:
                pass

        if database.getkeys(url) == 'default':
            keys = ','.join(list(ids))
            database.update(url, keys)


        for id in list(ids):
            if database.isinkeys(url, id):
                pass
            else:
                time = soup.xpath('//*[@id="%s"]/div/span[@class="ct"]' % id)[0]
                content = soup.xpath('//*[@id="%s"]/div/span[@class="ctt"]' % id)[0]
                # 这里就是添加到需要发送邮件的位置。
                print time, content


if __name__ == '__main__':
    # login = Fetcher(username='', pwd='')
    # login.login()
    # url = "http://weibo.cn/xiaocang520"
    # text = login.fetch(url)
    # soup = soupparser.fromstring(text)
    # for i in soupparser.fromstring(text).xpath(".//div[@class='c']"):print i.attrib
    # with open('namei.txt','w') as f:
    #     f.write(text)
    pass
    # http://weibo.cn/1818471621/profile
    # http://weibo.cn/xiayike233
    #  http://weibo.cn/u/2751220871