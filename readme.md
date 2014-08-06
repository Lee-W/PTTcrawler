#PTTcraweler
This is a repo fork from https://github.com/wy36101299/PTTcrawler
I rewrite it to a module so that it can be extended for further usage.

#USAGE
This is the basic usage of this script
```python3
python3 pttcraweler.py [start-page] [end-page] [boardName]
```
the default value for start-page and end-page are the last page of the board
the default value for boardName is Gossiping
*Note that the sequence matters.*

After parsing from PTT, it will generte output.json.
The format is as below

    "a_ID": 編號,
    "b_作者": 作者名,
    "c_標題": 標題,
    "d_日期": 發文時間,
    "e_ip": 發文ip,
    "f_內文": 內文,
    "g_推文": {
        "推文編號": {
            "狀態": 推 or 噓 or →,
            "留言內容": 留言內容,
            "留言時間": 留言時間,
            "留言者": 留言者
        }
    },
    "h_推文總數": {
        "all": 推文數目,
        "噓": 噓數,
        "推": 推數,
        "none": →數
    }

#PREREQUISITES
python3
lib : beautifulsoup4, requests
```
sudo pip3 install -r requirements.txt
```

