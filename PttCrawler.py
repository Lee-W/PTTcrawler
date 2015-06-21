# coding=utf-8

import os
import re
import json
import requests

from time import sleep
from bs4 import BeautifulSoup


class PttCrawler(object):
    PTT_URL = "http://www.ptt.cc/"
    COOKIE = {"over18": "1"}

    def __init__(self):
        self.result = list()
        self._board_name = "Gossiping"
        self._export_path = "output"

    @property
    def board_name(self):
        return self._board_name

    @board_name.setter
    def board_name(self, value):
        self._board_name = value

    @property
    def export_path(self):
        return self._export_path

    @export_path.setter
    def export_pathe(self, value):
        self._export_path = value

    def crawl(self, start=None, end=None,
              display_progress=True, export_each=True):
        last_page_num = self.get_last_page_num(self.board_name)

        start = last_page_num if start is None else start
        end = last_page_num if end is None else end

        for page in reversed(range(start, end+1)):
            if display_progress is True:
                print('index is ' + str(page))

            board_URL = self.PTT_URL+"bbs/"+self.board_name+"/index"+str(page)+".html"
            req = requests.get(url=board_URL, cookies=self.COOKIE)
            soup = BeautifulSoup(req.text)

            article_counter = 0
            for tag in soup.find_all("div", "r-ent"):
                try:
                    link = str(tag.find_all("a")).split("\"")
                    link = self.PTT_URL + link[1]

                    article_counter = article_counter + 1
                    articleID = str(page)+"-"+str(article_counter)

                    article = self.__parse_article(link, articleID, display_progress)
                    if export_each:
                        self.export_article(article)
                    self.result.append(article)
                except Exception as e:
                    print("Error")
                    print(e)
            sleep(0.2)
        return self.result

    def __parse_article(self, link, articleID, displayProgress):
        req = requests.get(url=str(link), cookies=self.COOKIE)
        soup = BeautifulSoup(req.text)
        if displayProgress is True:
            print(articleID+"  "+req.url)
        data = list()

        # author
        author = soup.find(id="main-container") \
                     .contents[1].contents[0].contents[1].string.replace(' ', '')
        # title
        title = soup.find(id="main-container") \
                    .contents[1].contents[2].contents[1].string.replace(' ', '')
        # date
        date = soup.find(id="main-container").contents[1].contents[3].contents[1].string
        # ip
        try:
            ip = soup.find(text=re.compile(u"※ 發信站:"))
            ip = re.search("[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*", str(ip)).group()
        except:
            ip = "ip is not find"

        # contents
        a = str(soup.find(id="main-container").contents[1]).split("</div>")
        a = a[4].decode("utf-8").split(u"<span class=\"f2\">※ 發信站: 批踢踢實業坊(ptt.cc)")
        content = a[0].replace(' ', '').replace('\n', '').replace('\t', '')
        content = PttCrawler._strip_html(content)

        # message
        pushSummary, g, b, n, message = dict(), int(), int(), int(), list()
        for tag in soup.find_all("div", "push"):
            try:
                push_tag = tag.find("span", "f1 hl push-tag").string.replace(' ', '')
            except:
                push_tag = tag.find("span", "hl push-tag").string.replace(' ', '')

            push_userid = tag.find("span", "f3 hl push-userid").string.replace(' ', '')

            try:
                push_content = tag.find("span", "f3 push-content").string
            except:
                # if there is no content
                push_content = ""

            push_ipdatetime = tag.find("span", "push-ipdatetime").string.replace('\n', '')

            message.append({u"狀態": unicode(push_tag),
                            u"留言者": unicode(push_userid),
                            u"留言內容": unicode(push_content),
                            u"留言時間": unicode(push_ipdatetime)})
            if push_tag == u'推':
                g += 1
            elif push_tag == u'噓':
                b += 1
            else:
                n += 1
            pushSummary = {u"推": g, u"噓": b, "none": n, "all": len(message)}

        data = {u"a_ID": articleID,
                u"b_作者": unicode(author),
                u"c_標題": unicode(title),
                u"d_日期": date,
                u"e_ip": ip,
                u"f_內文": unicode(content),
                u"g_推文": message,
                u"h_推文總數": pushSummary,
                u"i_連結": unicode(link)}
        return data

    @staticmethod
    def __filter_space_character(content):
        return content.replace(' ', '').replace('\n', '').replace('\y', '')

    @staticmethod
    def get_last_page_num(board_name):
        current_url = PttCrawler.PTT_URL+"bbs/"+board_name+"/index.html"
        resp = requests.get(url=current_url, cookies=PttCrawler.COOKIE)
        if re.search(u"disabled\">下頁", resp.text) is not None:
            prevPageIdentifier = re.search(u"index[0-9]+\.html.*上頁", resp.text).group()
            prevPage = int(re.search("[0-9]+", prevPageIdentifier).group())
        return prevPage+1

    def export_article(self, article):
        try:
            os.makedirs(self.export_path+"/"+self.board_name, exist_ok=True)
        except Exception:
            pass

        file_name = self.export_path+"/"+self.board_name+"/"+str(article["a_ID"])
        with open(file_name, "w") as f:
            json_content = json.dumps(article, ensure_ascii=False, sort_keys=True, indent=4)
            f.write(json_content.encode("utf-8"))

    def export(self, fileName="output.json"):
        with open(fileName, 'w') as f:
            json.dump(self.result, f, ensure_ascii=False, indent=4, sort_keys=True)

    @staticmethod
    def _strip_html(html):
        content = re.compile(r'<.*?>')
        return content.sub('', html)


if __name__ == '__main__':
    import sys

    ptt = PttCrawler()
    if len(sys.argv) == 2:
        ptt.crawl(int(sys.argv[1]))
    elif len(sys.argv) == 3:
        ptt.crawl(int(sys.argv[1]), int(sys.argv[2]))
    elif len(sys.argv) == 4:
        ptt.board_name = sys.argv[3]
        ptt.crawl(int(sys.argv[1]), int(sys.argv[2]))
    else:
        ptt.crawl()
