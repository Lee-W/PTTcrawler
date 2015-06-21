import os
import re
import json
import requests

from time import sleep
from bs4 import BeautifulSoup
from html2text import html2text


class PttCrawler:
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

        for page in range(start, end+1):
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
                except Exception as e:
                    print("Error")
                    print(e)
            sleep(0.2)

    def __parse_article(self, link, articleID, displayProgress):
        req = requests.get(url=str(link), cookies=self.COOKIE)
        soup = BeautifulSoup(req.text)
        if displayProgress is True:
            print(articleID+"  "+req.url)

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
            ip = soup.find(text=re.compile("※ 發信站:"))
            ip = re.search("[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*", str(ip)).group()
        except:
            ip = "ip is not find"

        # contents
        a = str(soup.find(id="main-container").contents[1]).split("</div>")
        a = a[4].split("<span class=\"f2\">※ 發信站: 批踢踢實業坊(ptt.cc)")
        content = a[0].replace(' ', '').replace('\n', '').replace('\t', '')
        content = html2text(content)

        # message
        pushSummary, g, b, n, message = dict(), int(), int(), int(), list()
        for tag in soup.find_all("div", "push"):
            push_tag = tag.find("span", "push-tag").string.replace(' ', '')
            push_userid = tag.find("span", "push-userid").string.replace(' ', '')
            try:
                push_content = PttCrawler.__filter_space_character(tag.find("span", "push_content"))
            except:
                # if there is no content
                push_content = ""
            push_ipdatetime = tag.find("span", "push-ipdatetime").string.replace('\n', '')

            message.append({"狀態": push_tag,
                            "留言者": push_userid,
                            "留言內容": push_content,
                            "留言時間": push_ipdatetime})
            if push_tag == '推':
                g += 1
            elif push_tag == '噓':
                b += 1
            else:
                n += 1
            pushSummary = {"推": g, "噓": b, "none": n, "all": len(message)}

        data = {"a_ID": articleID,
                "b_作者": author,
                "c_標題": title,
                "d_日期": date,
                "e_ip": ip,
                "f_內文": content,
                "g_推文": message,
                "h_推文總數": pushSummary,
                "i_連結": link}
        return data

    @staticmethod
    def __filter_space_character(content):
        return content.replace(' ', '').replace('\n', '').replace('\y', '')

    @staticmethod
    def get_last_page_num(board_name):
        current_url = PttCrawler.PTT_URL+"bbs/"+board_name+"/index.html"
        resp = requests.get(url=current_url, cookies=PttCrawler.COOKIE)
        if re.search("disabled\">下頁", resp.text) is not None:
            prevPageIdentifier = re.search("index[0-9]+\.html.*上頁", resp.text).group()
            prevPage = int(re.search("[0-9]+", prevPageIdentifier).group())
        return prevPage+1

    def export_article(self, article):
        try:
            os.makedirs(self.export_path+"/"+self.board_name, exist_ok=True)
        except Exception:
            pass

        file_name = self.export_path+"/"+self.board_name+"/"+str(article["a_ID"])
        with open(file_name, "w") as f:
            json.dump(article, f, ensure_ascii=False, indent=4, sort_keys=True)

    def export(self, fileName="output.json"):
        with open(fileName, 'w') as f:
            json.dump(self.result, f, ensure_ascii=False, indent=4, sort_keys=True)


if __name__ == '__main__':
    import sys

    ptt = PttCrawler()
    ptt.board_name = "Gossiping"
    if len(sys.argv) == 2:
        ptt.crawl(int(sys.argv[1]))
    elif len(sys.argv) == 3:
        ptt.crawl(int(sys.argv[1]), int(sys.argv[2]))
    elif len(sys.argv) == 4:
        ptt.board_name = sys.argv[3]
        ptt.crawl(int(sys.argv[1]), int(sys.argv[2]))
    else:
        ptt.crawl()
