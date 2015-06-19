import os
import re
import json
import requests

from time import sleep
from bs4 import BeautifulSoup
from html2text import html2text


class PTTCrawler:
    def __init__(self):
        self.PTT_URL = "http://www.ptt.cc/"
        self.COOKIE = {"over18": "1"}

        self.result = list()
        self.boardName = str()

    def crawl(self, start=None, end=None, boardName="Gossiping",
              displayProgress=True, reserve_content_format=False):
        self.boardName = boardName
        start = self.get_last_page_num(boardName) if start is None else start
        end = self.get_last_page_num(boardName) if end is None else end

        for page in range(start, end+1):
            if displayProgress is True:
                print('index is ' + str(page))

            board_URL = self.PTT_URL+"bbs/"+boardName+"/index"+str(page)+".html"
            req = requests.get(url=board_URL, cookies=self.COOKIE)
            soup = BeautifulSoup(req.text)

            articleCounter = 0
            for tag in soup.find_all("div", "r-ent"):
                try:
                    link = str(tag.find_all("a")).split("\"")
                    link = self.PTT_URL + link[1]
                    articleCounter = articleCounter + 1
                    articleID = str(page)+"-"+str(articleCounter)
                    self.__parse_article(link, articleID, displayProgress, reserve_content_format)
                except Exception:
                    print("Error")
                    pass
            sleep(0.2)
        return self.result

    def __parse_article(self, link, articleID, displayProgress, reserve_content_format):
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
        a = a[4].split("<span class=\"f2\">※ 發信站: 批踢踢實業坊(ptt.cc),")
        content = a[0].replace(' ', '').replace('\n', '').replace('\t', '')
        content = content if reserve_content_format is True else html2text(content)

        # message
        pushSummary, g, b, n, message = dict(), int(), int(), int(), list()
        for tag in soup.find_all("div", "push"):
            push_tag = tag.find("span", "push-tag").string.replace(' ', '')
            push_userid = tag.find("span", "push-userid").string.replace(' ', '')
            try:
                push_content = PTTCrawler.__filter_space_character(tag.find("span", "push_content"))
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
                "h_推文總數": pushSummary}
        self.result.append(data)

    @staticmethod
    def __filter_space_character(content):
        return content.replace(' ', '').replace('\n', '').replace('\y', '')

    def get_last_page_num(self, boardName="Gossiping"):
        current_url = self.PTT_URL+"bbs/"+self.boardName+"/index.html"
        resp = requests.get(url=current_url, cookies=self.COOKIE)
        if re.search("disabled\">下頁", resp.text) is not None:
            prevPageIdentifier = re.search("index[0-9]+\.html.*上頁", resp.text).group()
            prevPage = int(re.search("[0-9]+", prevPageIdentifier).group())
        return prevPage+1

    def export(self, fileName="output.json"):
        with open(fileName, 'w') as f:
            json.dump(self.result, f, ensure_ascii=False, indent=4, sort_keys=True)

    def export_each_article(self, export_dir="output"):
        try:
            os.makedirs(export_dir+"/"+self.boardName, exist_ok=False)
        except Exception:
            pass

        for article in self.result:
            path = export_dir+"/"+self.boardName+"/"+str(article["a_ID"])
            with open(path, 'w') as f:
                json.dump(article, f, ensure_ascii=False, indent=4, sort_keys=True)


if __name__ == '__main__':
    import sys

    ptt = PTTCrawler()
    if len(sys.argv) == 2:
        ptt.crawl(int(sys.argv[1]))
    elif len(sys.argv) == 3:
        ptt.crawl(int(sys.argv[1]), int(sys.argv[2]))
    elif len(sys.argv) == 4:
        ptt.crawl(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
    else:
        ptt.crawl()

    ptt.export_each_article()
