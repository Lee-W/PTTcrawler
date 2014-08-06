import re
import json
import requests
from time import sleep
from bs4 import BeautifulSoup


class PTTCrawler:
    def __init__(self):
        self.pttURL = "http://www.ptt.cc/"
        self.result = list()

    def crawl(self, start=None, end=None, boardName="Gossiping"):
        start = self.getLastPageNum(boardName) if start is None else start
        end = self.getLastPageNum(boardName) if end is None else end
        articleID = int()

        for page in range(start, end+1):
            print('index is ' + str(page))
            req = requests.get(url=self.pttURL+"bbs/"+boardName+"/index"+str(page)+".html",
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
        return self.result

    def parseContent(self, link, articleID):
        req = requests.get(url=str(link), cookies={"over18": "1"})
        soup = BeautifulSoup(req.text)
        print(req.url)

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
        messageNum, g, b, n, message = int(), int(), int(), int(), dict()
        for tag in soup.find_all("div", "push"):
            messageNum += 1
            push_tag = tag.find("span", "push-tag").string.replace(' ', '')
            push_userid = tag.find("span", "push-userid").string.replace(' ', '')
            try:
                push_content = tag.find("span", "push-content").string.replace(' ', '').replace('\n', '').replace('\t', '')
            except:
                # if there is no content
                push_content = ""
            push_ipdatetime = tag.find("span", "push-ipdatetime").string.replace('\n', '')

            message[messageNum] = {"狀態": push_tag, "留言者": push_userid, "留言內容": push_content, "留言時間": push_ipdatetime}
            if push_tag == '推 ':
                g += 1
            elif push_tag == '噓 ':
                b += 1
            else:
                n += 1
            messageN = {"g": g, "b": b, "n": n, "all": messageNum}

        data = {"a_ID": articleID,
                "b_作者": author,
                "c_標題": title,
                "d_日期": date,
                "e_ip": ip,
                "f_內文": content,
                "g_推文": message,
                "h_推文總數": messageN}
        self.result.append(data)

    def getLastPageNum(self, boardName="Gossiping"):
        resp = requests.get(url="http://www.ptt.cc/bbs/"+boardName+"/index.html",
                            cookies={"over18": "1"})
        if re.search("disabled\">下頁", resp.text) is not None:
            prevPageIdentifier = re.search("index[0-9]+\.html.*上頁", resp.text).group()
            prevPage = int(re.search("[0-9]+", prevPageIdentifier).group())
        return prevPage+1

    def export(self, fileName="output.json"):
        with open(fileName, 'w') as f:
            json.dump(self.result, f, ensure_ascii=False, indent=4, sort_keys=True)


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

    ptt.export()
