import os
import re
import json
import requests

from time import sleep
from bs4 import BeautifulSoup


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

        for page in reversed(range(start, end+1)):
            if display_progress is True:
                print('index is ' + str(page))

            board_url = self.PTT_URL+"bbs/"+self.board_name+"/index"+str(page)+".html"
            req = requests.get(url=board_url, cookies=self.COOKIE)
            soup = BeautifulSoup(req.text)

            article_counter = 0
            for tag in soup.find_all("div", "r-ent"):
                try:
                    link = str(tag.find_all("a")).split("\"")
                    link = self.PTT_URL + link[1]

                    article_counter = article_counter + 1
                    article_id = str(page)+"-"+str(article_counter)

                    article = self.__parse_article(link, article_id, display_progress)
                    if export_each:
                        self.export_article(article)
                    self.result.append(article)
                except AttributeError:
                    print("Article removed")
            sleep(0.2)
        return self.result

    def __parse_article(self, link, article_id, display_progress):
        req = requests.get(url=str(link), cookies=self.COOKIE)
        soup = BeautifulSoup(req.text)
        if display_progress is True:
            print(article_id+"  "+req.url)

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
            ip = re.search(r"[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*", str(ip)).group()
        except AttributeError:
            ip = "ip is not find"

        # contents
        content = str(soup.find(id="main-container").contents[1]).split("</div>")
        content = content[4].split("<span class=\"f2\">※ 發信站: 批踢踢實業坊(ptt.cc)")
        content = content[0].replace(' ', '').replace('\n', '').replace('\t', '')
        content = PttCrawler._strip_html(content)

        # message
        push_summary, good, bad, none, message = dict(), int(), int(), int(), list()
        for tag in soup.find_all("div", "push"):
            try:
                push_tag = tag.find("span", "f1 hl push-tag").string.replace(' ', '')
            except AttributeError:
                push_tag = tag.find("span", "hl push-tag").string.replace(' ', '')

            push_userid = tag.find("span", "f3 hl push-userid").string.replace(' ', '')

            try:
                push_content = tag.find("span", "f3 push-content").string
            except AttributeError:
                # if there is no content
                push_content = ""

            push_ipdatetime = tag.find("span", "push-ipdatetime").string.replace('\n', '')

            message.append({"狀態": push_tag,
                            "留言者": push_userid,
                            "留言內容": push_content,
                            "留言時間": push_ipdatetime})
            if push_tag == '推':
                good += 1
            elif push_tag == '噓':
                bad += 1
            else:
                none += 1
            push_summary = {"推": good, "噓": bad, "none": none, "all": len(message)}

        data = {"a_ID": article_id,
                "b_作者": author,
                "c_標題": title,
                "d_日期": date,
                "e_ip": ip,
                "f_內文": content,
                "g_推文": message,
                "h_推文總數": push_summary,
                "i_連結": link}
        return data

    @staticmethod
    def __filter_space_character(content):
        return content.replace(' ', '').replace('\n', '').replace(r'\y', '')

    @staticmethod
    def get_last_page_num(board_name):
        current_url = PttCrawler.PTT_URL+"bbs/"+board_name+"/index.html"
        resp = requests.get(url=current_url, cookies=PttCrawler.COOKIE)
        if re.search("disabled\">下頁", resp.text) is not None:
            prev_page_identifer = re.search(r"index[0-9]+\.html.*上頁", resp.text).group()
            prev_page = int(re.search("[0-9]+", prev_page_identifer).group())
        return prev_page+1

    def export_article(self, article):
        try:
            os.makedirs(self.export_path+"/"+self.board_name, exist_ok=True)
        except FileExistsError:
            pass

        file_name = self.export_path+"/"+self.board_name+"/"+str(article["a_ID"])
        with open(file_name, "w") as f:
            json.dump(article, f, ensure_ascii=False, indent=4, sort_keys=True)

    def export(self, file_name="output.json"):
        with open(file_name, 'w') as f:
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
