# encoding=utf-8

from bs4 import BeautifulSoup
import requests
from itertools import chain
import codecs


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
        with codecs.open(self.outfile, mode, 'utf-8') as fp:
            for post in chain(*results):
                fp.write(u'\n-----------------------------------------------------------\n')
                fp.write(post)


if __name__ == '__main__':
    # s = Spider('http://bbs.tianya.cn/post-no05-422979-{}.shtml'.format, 1, 10, 'klingkun', u'揭开脸谱看封神------解读《封神演义》.txt')
    # s = Spider('http://bbs.tianya.cn/post-no05-412828-{}.shtml'.format, 1, 22, 'klingkun', u'西游记中计.txt')
    # s = Spider('http://bbs.tianya.cn/post-no05-383603-{}.shtml'.format, 1, 7, 'klingkun', u'品读《三国演义》中的三大主角.txt')
    s = Spider('http://bbs.tianya.cn/post-no05-363532-{}.shtml'.format, 1, 4, 'klingkun', u'解读《水浒传》里的大反派.txt')
    s.run()
