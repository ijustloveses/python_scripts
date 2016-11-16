# encoding=utf-8

from bs4 import BeautifulSoup
import requests
from itertools import chain
import codecs
import time


def tryfunc(msg):
    def wrapper(fn):
        def inner(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception, e:
                print msg
                raise e
        return inner
    return wrapper


class Spider(object):
    def __init__(self, urlformat, startpage, lastpage, author, outfile):
        self.urlformat = urlformat
        self.startpage =startpage
        self.lastpage = lastpage
        self.author = author
        self.outfile = outfile

    @tryfunc("Failed to parse url, crawler halt")
    def url_to_soup(self, url):
        print "> parsing url: %s" % url
        r = requests.get(url)
        r.encoding = 'utf-8'
        return BeautifulSoup(r.text, "html.parser")

    @tryfunc("Failed to parse url page, crawler halt")
    def parse_page(self, i):
        url = self.urlformat(i)
        soup = self.url_to_soup(url)
        posts = soup.findAll('div', {'class': 'atl-item'})
        # 注意这里，第一页的第一个帖子是“前言”，前言部分没有作者行，故此调用 get_post_name 会失败
        results = []
        if i == 1:  # 第一页的第一个帖子内容永远收集
            results.append(self.get_post_content(posts[0]))
            posts = posts[1:]
        return results + [self.get_post_content(p) for p in posts if self.get_post_name(p) == self.author]

    def get_post_name(self, post):
        """
        <div class='atl-info'><span>\u4f5c\u8005\uff1a
            <a class='js-vip-check' href='http://www.tianya.cn/116322493' target='_blank'
                uid='116322493' uname='ty_\u9676\u5b50953'>ty_\u9676\u5b50953
            </a>
        </span><span>\u65f6\u95f4\uff1a2016-08-03 14:23:51</span></div>
        """
        return post.find('div', {'class': 'atl-info'}).find('a').attrs['uname']

    def get_post_content(self, post):
        return post.find('div', {'class': 'bbs-content'}).text.strip()

    def run(self, mode='w'):
        # will be list of list
        results = []
        for i in range(self.startpage, self.lastpage + 1):
            results.append(self.parse_page(i))
            time.sleep(3)
        with codecs.open(self.outfile, mode, 'utf-8') as fp:
            for post in chain(*results):
                fp.write(u'\n-----------------------------------------------------------\n')
                fp.write(post)


if __name__ == '__main__':
    posts = [
        #  ['no05', '422979', 1, 12, u'klingkun', u'揭开脸谱看封神------解读《封神演义》.txt'],
        #  ['no05', '412828', 1, 22, u'klingkun', u'西游记中计.txt'],
        #  ['no05', '383603', 1, 7, u'klingkun', u'品读《三国演义》中的三大主角.txt'],
        #  ['no05', '363532', 1, 4, u'klingkun', u'解读《水浒传》里的大反派.txt'],
        #  ['no05', '265690', 1, 75, u'曹铜爵', u'少不读水浒——揭秘水浒传.txt'],
        #  ['no05', '380273', 1, 30, u'布衣卿相0', u'《五代风云》（最细致的人性五代史）- undone.txt'],
        #  ['no05', '271597', 1, 48, u'YOU2YOU3YOU62005', u'西晋五十年.txt'],
        #  ['no05', '239864', 1, 45, u'李晓润', u'唐诗演义.txt'],
        #  ['no05', '236376', 1, 38, u'月映长河', u'揭秘北洋舰队为什么打不过联合舰队.txt'],
        #  ['no05', '214629', 1, 92, u'醉罢君山', u'血战天下——战国全史.txt'],
        #  ['no05', '134367', 1, 41, u'醉罢君山', u'铁血时代——以霸业为主线的春秋战国史.txt'],
        #  ['no05', '111344', 1, 74, u'醉罢君山', u'虽远必诛——大汉帝国的扩张.txt`'],
        #  ['no05', '269514', 1, 56, u'o宇微o', u'五代刀锋 朱温、李存勖.txt'],
        #  ['no05', '228429', 1, 53, u'宇_为', u'刘秀和云台二十八将的传奇史诗.txt'],
        ['no05', '113393', 1, 57, u'雪域桃源', u'东汉帝国往事.txt'],
        ['no05', '124391', 1, 132, u'曹三公子', u'嗜血的皇冠——光武皇帝之刘秀的秀.txt'],
    ]
    for label, pid, start, end, author, name in posts:
        print u"fetching {} ...".format(name)
        fmt = 'http://bbs.tianya.cn/post-{}-{}-'.format(label, pid) + '{}.shtml'
        s = Spider(fmt.format, start, end, author, name)
        s.run()
