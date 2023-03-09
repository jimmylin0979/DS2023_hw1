#
import re
import time
import random
import sys
import json
from datetime import datetime
from tqdm import tqdm
from typing import List, Optional, Tuple

#
import requests
from bs4 import BeautifulSoup

# URLs
# PTT Beauty: https://www.ptt.cc/bbs/Beauty/index.html
URL_PTT_BEAUTY = "https://www.ptt.cc/bbs/Beauty/index{index}.html"

# At https://www.ptt.cc/bbs/Beauty/index3850.html, https://www.ptt.cc/bbs/Beauty/M.1661493905.A.756.html, list index out of range
# At https://www.ptt.cc/bbs/Beauty/index3771.html, https://www.ptt.cc/bbs/Beauty/M.1653881555.A.842.html, list index out of range

#
def str2Datetime(timeStamp: str) -> datetime:

    #
    times = timeStamp.strip(" ")
    times = timeStamp.split("/")
    month = int(times[0])
    date  = int(times[1])
    # print(f"{times}, {month}, {date}")

    #
    timeStamp = f"2022{month:02d}{date:02d}"
    res = datetime.strptime(timeStamp, "%Y%m%d")
    return res

def get_session():
    #
    # Create session to memorize every cookie for a certain time
    #   , avoid to pass cookie header every time
    payload = {
        "from": "/bbs/Beauty/index.html",
        "yes": "yes"
    }
    rs = requests.session()
    rs.post("https://www.ptt.cc/ask/over18", data=payload)
    return rs

def find_index_start():
    
    rs = get_session()
    
    # 
    index = 3600        # 20220101  https://www.ptt.cc/bbs/Beauty/index3642.html
    index_2022first = index
    # index = 3951      # 20221231
    progress_bar = tqdm(total=3636 + 1 - index)

    isContinue = True
    while isContinue:
        #
        # Search articles page by page
        url = URL_PTT_BEAUTY.format(index=index)
        progress_bar.update(1)
        index += 1
        res = rs.get(url)       # encoding = utf-8
        time.sleep(0.1 + random.random() * 2)

        #
        content = BeautifulSoup(res.text, "html.parser")
        content.encoding = "utf-8"
        web_popular = content.find_all("div", class_="nrec")
        web_articles = content.find_all("div", class_="title")
        web_articles_info = content.find_all("div", class_="meta")
        for i in range(len(web_articles)):

            try:

                # Check whether to stop the crawling (crawl the articles only in 2020) 
                # author = web_articles_info[i].find_all("div", class_="author")[0].get_text()
                timeStamp = web_articles_info[i].find_all("div", class_="date")[0].get_text()  
                if timeStamp == " 1/01":
                    isContinue = False
                    index_2022first = index - 1
                    break

            except Exception as ex:
                print(f"At {url}, {index - 1}, {ex}")
    
    return index_2022first

def fn_crawl() -> None:

    # Get a session instance
    rs = get_session()

    # file pointer
    fw_all_article = open("all_article.jsonl", "w", encoding="utf-8")
    fw_all_popular = open("all_popular.jsonl", "w", encoding="utf-8")

    #
    # index = 3636        # 20220101  https://www.ptt.cc/bbs/Beauty/index3642.html
    index = find_index_start()
    print(index)
    index_2022first = index
    # index = 3951      # 20221231
    progress_bar = tqdm(total=3951 - 3642)

    isContinue = True
    while isContinue:
        #
        # Search articles page by page
        url = URL_PTT_BEAUTY.format(index=index)
        progress_bar.update(1)
        index += 1
        res = rs.get(url)       # encoding = utf-8
        time.sleep(0.1 + random.random() * 2)

        #
        content = BeautifulSoup(res.text, "html.parser")
        content.encoding = "utf-8"
        web_popular = content.find_all("div", class_="nrec")
        web_articles = content.find_all("div", class_="title")
        web_articles_info = content.find_all("div", class_="meta")
        for i in range(len(web_articles)):

            try:
                # Check whether the article is popular or not
                is_popular = False
                popular_state = web_popular[i].get_text()
                is_popular = (popular_state == "爆")

                # Get article information, such as author, title, href etc.
                article = web_articles[i]
                title = article.find("a").get_text()
                if title.startswith("[公告]") or title.startswith("Fw: [公告]"):
                    continue
                href = article.find("a")["href"]
                href = f"https://www.ptt.cc{href}"

                # Check whether to stop the crawling (crawl the articles only in 2020) 
                # author = web_articles_info[i].find_all("div", class_="author")[0].get_text()
                timeStamp = web_articles_info[i].find_all("div", class_="date")[0].get_text()  
                if timeStamp == " 1/01" and index > index_2022first + 10:
                    isContinue = False
                    break
                elif timeStamp == "12/31" and index == index_2022first + 1:
                    isContinue = True
                    continue
                else:
                    isContinue = True
                
                # Transfer the time into datetime format
                # ex. ' 5/30'
                timeStamp = str2Datetime(timeStamp)
                # print(f"{index + 1}, {timeStamp.strftime('%m%d')}, {title}, {href}, {popular_state}")

                # Write into .jsonl files
                res = {"date": timeStamp.strftime("%m%d"), "title": title, "url": href}
                _str = json.dumps(res, ensure_ascii=False)
                fw_all_article.write(_str + "\n")
                if is_popular:
                    fw_all_popular.write(_str + "\n")

            except Exception as ex:
                print(f"At {url}, {href}, {ex}")

        # Flush
        fw_all_article.flush()
        fw_all_popular.flush()

    # Store information in jsonl format
    fw_all_article.close()
    fw_all_popular.close()

def findIndexOfDate(articles, start_date: str, end_date: str) -> Tuple[int, int]:
    
    # # Find the first index of start_date in articles
    # idx_start = 0
    # l, r = 0, len(articles)
    # while l < r:
    #     mid = l + (r - l) // 2
    #     if articles[mid]["date"] >= start_date:
    #         r = mid
    #     else:
    #         l = mid + 1
    # idx_start = r

    # # Find the first index of end_date in articles 
    # idx_end = 0
    # l, r = 0, len(articles)
    # while l < r:
    #     mid = l + (r - l) // 2
    #     if articles[mid]["date"] > end_date:
    #         r = mid - 1
    #     else:
    #         l = mid + 1
    #         idx_end = l
    # idx_end = l

    idx_start, idx_end = -1, -1
    for i in range(len(articles)):        
        if articles[i]["date"] < start_date:
            idx_start = i
        if articles[i]["date"] <= end_date:
            idx_end = i

    return idx_start, idx_end

def fn_push(start_date, end_date) -> None:
    
    # Load json instance into memory
    with open("./all_article.jsonl", "r", encoding="utf-8") as fr:
        jsonls = list(fr)
    
    articles = []
    for jsonl in jsonls:
        article = json.loads(jsonl)
        articles.append(article)

    # Get the interval of selected dates
    idx_start, idx_end = findIndexOfDate(articles=articles, start_date=start_date, end_date=end_date)
    print(idx_start, idx_end)
    rs = get_session()
    num_all_like, num_all_boo = 0, 0
    like_authors, boo_authors = {}, {}
    for i in tqdm(range(idx_start + 1, idx_end + 1)):
        # 
        web = rs.get(articles[i]["url"])
        web = BeautifulSoup(web.text, "html.parser")
        web.encoding = "utf-8"
        # 
        web_pushs = web.find_all("div", class_="push")
        for web_push in web_pushs:
            # extract push label, and then record the appear time of each
            push_tag = web_push.find_all("span")[0].get_text()
            userid = web_push.find_all("span")[1].get_text()
            if push_tag == "推 ":
                num_all_like += 1
                if userid not in like_authors.keys():
                    like_authors[userid] = 0
                like_authors[userid] += 1

            elif push_tag == "噓 ":
                num_all_boo += 1
                if userid not in boo_authors.keys():
                    boo_authors[userid] = 0
                boo_authors[userid] += 1

            elif push_tag == "→ ":
                pass
            else:
                pass

    # Fill the json object  
    res = {
        "all_like" : num_all_like,
        "all_boo" : num_all_boo,
    }
    sorted_like_authors = sorted(like_authors.items(), key=lambda x: -x[1])
    sorted_boo_authors = sorted(boo_authors.items(), key=lambda x: -x[1])

    sorted_like_authors = sorted(sorted_like_authors, key=lambda x: (x[1], x[0]), reverse=True)
    sorted_boo_authors = sorted(sorted_boo_authors, key=lambda x: (x[1], x[0]), reverse=True)

    for i, (k, v) in enumerate(sorted_like_authors):
        if i == 10: break
        res[f"like {i + 1}"] = {"user_id": k, "count": v}    
    for i, (k, v) in enumerate(sorted_boo_authors):
        if i == 10: break
        res[f"boo {i + 1}"] = {"user_id": k, "count": v}
    
    # Write into .json file with custom format
    with open(f"push_{start_date}_{end_date}.json", "w") as fw_push:
        fw_push.write("{\n")
        for k, v in res.items():
            # 
            if isinstance(v, dict):
                _str = json.dumps(v, ensure_ascii=False)
                fw_push.write(f"\t\"{k}\": {_str}")
            else:
                fw_push.write(f"\t\"{k}\": {v}")
            
            #
            if k != "boo 10":
                fw_push.write(",")
            fw_push.write("\n")
        fw_push.write("}")

def fn_popular(start_date, end_date):

    # Load json instance into memory
    with open("./all_popular.jsonl", "r", encoding="utf-8") as fr:
        jsonls = list(fr)
    
    articles = []
    for jsonl in jsonls:
        article = json.loads(jsonl)
        articles.append(article)

    # Get the interval of selected dates
    idx_start, idx_end = findIndexOfDate(articles=articles, start_date=start_date, end_date=end_date)
    print(idx_start, idx_end)
    res = {"number_of_popular_articles": idx_end - idx_start, "image_urls": []}
    rs = get_session()
    for i in tqdm(range(idx_start + 1, idx_end + 1)):
        # 
        web = rs.get(articles[i]["url"])
        # web = BeautifulSoup(web.text, "html.parser")
        # web.encoding = "utf-8"
        
        # Use regular expression to find out the img url
        regex = re.compile(r'"https?://[^"]*.(?:jpg|jpeg|png|gif)"')
        imgs = regex.findall(web.text)
        imgs_set = set()
        for img in imgs:
            img = img[1:-1]
            img = img.replace(" ", "\n")
            _imgs = img.split("\n")
            for _img in _imgs:
                if "https://cache.ptt.cc" in _img:  continue
                if not _img.startswith("http"):     continue
                if not (_img.endswith(".jpg") or _img.endswith(".jpeg") or _img.endswith(".png") or _img.endswith(".gif")): continue 
                imgs_set.add(_img)
        res["image_urls"].extend(list(imgs_set))
    
    # 
    with open(f"popular_{start_date}_{end_date}.json", "w", encoding="utf-8") as fw:
        _str = json.dumps(res, ensure_ascii=False, indent=4)
        fw.write(_str + "\n")

def fn_keyword(keyword, start_date, end_date):
    
    # Load json instance into memory
    with open("./all_article.jsonl", "r", encoding="utf-8") as fr:
        jsonls = list(fr)
    
    articles = []
    for jsonl in jsonls:
        article = json.loads(jsonl)
        articles.append(article)

    # Get the interval of selected dates
    idx_start, idx_end = findIndexOfDate(articles=articles, start_date=start_date, end_date=end_date)
    res = {"image_urls": []}
    rs = get_session()
    for i in tqdm(range(idx_start + 1, idx_end + 1)):
        # 
        web = rs.get(articles[i]["url"])
        # web = BeautifulSoup(web.text, "html.parser")
        # web.encoding = "utf-8"
        
        # Find whether this article have stop signal
        idx_e = web.text.find("※ 發信站")
        if idx_e == -1:
            continue

        # Check whether this article contain keyword inside
        web_article_content = web.text[:idx_e]
        if web_article_content.find(keyword) == -1:
            continue

        #
        # Use regular expression to find out the img url
        regex = re.compile(r'"https?://[^"]*.(?:jpg|jpeg|png|gif)"')
        imgs = regex.findall(web.text)
        # print(imgs)
        imgs_set = set()
        for img in imgs:
            img = img[1:-1]
            img = img.replace(" ", "\n")
            _imgs = img.split("\n")
            for _img in _imgs:
                if "https://cache.ptt.cc" in _img:  continue
                if not _img.startswith("http"):     continue
                if not (_img.endswith(".jpg") or _img.endswith(".jpeg") or _img.endswith(".png") or _img.endswith(".gif")): continue 
                imgs_set.add(_img)
        
        # print("=" * 80)
        # print(articles[i]["url"], imgs_set)
        res["image_urls"].extend(list(imgs_set))
    
    # 
    with open(f"keyword_{keyword}_{start_date}_{end_date}.json", "w", encoding="utf-8") as fw:
        _str = json.dumps(res, ensure_ascii=False, indent=4)
        fw.write(_str + "\n")

# Main entry point
if __name__ == "__main__":

    # Read arguments from input stream, and then perform function via input command
    command = sys.argv[1]
    if command == "crawl":
        fn_crawl()
    elif command == "push":
        fn_push(sys.argv[2], sys.argv[3])
    elif command == "popular":
        fn_popular(sys.argv[2], sys.argv[3])
    elif command == "keyword":
        fn_keyword(sys.argv[2], sys.argv[3], sys.argv[4])