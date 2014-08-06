import re
import sys
import json
import requests
from time import sleep
from bs4 import BeautifulSoup


class pttCrawler:
    def __init__(self):
        self.pttURL = "http://www.ptt.cc/bbs/"
        pass

    def crawl(self, start, end, boardName="Gossiping"):
        page = start
        times = end-start+1
        articleID = 0

        for t in range(times):
            print('index is ' + str(page))
            req = requests.get(url=self.pttURL + boardName+"/index" + str(page) + ".html",
                               cookies={"over18": "1"})
            soup = BeautifulSoup(req.text)
            for tag in soup.find_all("div", "r-ent"):
                try:
                    link = str(tag.find_all("a"))
                    link = link.split("\"")
                    link = self.pttURL + link[1]
                    articleID = articleID+1
                    self.parseContent(link, articleID)
                except:
                    pass
            sleep(0.2)
            page += 1

    def parseContent(self, link, articleID):
        req = requests.get(url=str(link), cookies={"over18": "1"})
        soup = BeautifulSoup(req.text)
        print(req)

        # author
        author = soup.find(id="main-container").contents[1].contents[0].contents[1].string.replace(' ', '')
        # title
        title = soup.find(id="main-container").contents[1].contents[2].contents[1].string.replace(' ', '')
        # date
        date = soup.find(id="main-container").contents[1].contents[3].contents[1].string
        # ip
        try:
            ip = soup.find(text=re.compile("※ 發信站:"))
            ip = re.search("[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*", str(ip)).group()
        except:
            ip = "ip is not find"
        # contents
        a = str(soup.find(id="main-container").contents[1])
        a = a.split("</div>")
        a = a[4].split("<span class=\"f2\">※ 發信站: 批踢踢實業坊(ptt.cc),")
        content = a[0].replace(' ', '').replace('\n', '').replace('\t', '')
        # message
        num, g, b, n, message = 0, 0, 0, 0, {}
        for tag in soup.find_all("div", "push"):
            num += 1
            push_tag = tag.find("span", "push-tag").string.replace(' ', '')
            push_userid = tag.find("span", "push-userid").string.replace(' ', '')
            push_content = tag.find("span", "push-content").string.replace(' ', '').replace('\n', '').replace('\t', '')
            push_ipdatetime = tag.find("span", "push-ipdatetime").string.replace('\n', '')

            message[num] = {"狀態": push_tag, "留言者": push_userid, "留言內容": push_content, "留言時間": push_ipdatetime}
            if push_tag == '推 ':
                g += 1
            elif push_tag == '噓 ':
                b += 1
            else:
                n += 1
            messageNum = {"g": g, "b": b, "n": n, "all": num}
            # json-data
            d = {"a_ID": articleID,
                 "b_作者": author,
                 "c_標題": title,
                 "d_日期": date,
                 "e_ip": ip,
                 "f_內文": content,
                 "g_推文": message,
                 "h_推文總數": messageNum}
            json_data = json.dumps(d, ensure_ascii=False, indent=4, sort_keys=True)+','

            self.store(json_data)

    def getLastPageNum(self, boardName="Gossiping"):
        resp = requests.get(url="http://www.ptt.cc/bbs/"+boardName+"/index.html",
                            cookies={"over18": "1"})
        if re.search("disabled\">下頁", resp.text) is not None:
            prevPageIdentifier = re.search("index[0-9]+\.html.*上頁", resp.text).group()
            prevPage = int(re.search("[0-9]+", prevPageIdentifier).group())
        return prevPage+1

    def store(self, data):
        with open('data.json', 'a') as f:
            f.write(data)

    def export(self):
        self.store('[')
        self.crawl(int(sys.argv[1]), int(sys.argv[2]))
        self.store(']')
        with open('data.json', 'r') as f:
            p = f.read()
        with open('data.json', 'w') as f:
            f.write(p.replace(',]', ']'))
