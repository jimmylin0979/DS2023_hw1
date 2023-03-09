import json

def main(filepath, filename):

    #
    print("Reading ...")
    articles = None
    with open(f"{filepath}", "r", encoding="utf-8") as fr:
        articles = json.load(fr)

    #
    print("Aggregating ...")
    urls = set()
    for i in range(len(articles["image_urls"])):
        url = articles["image_urls"][i]
        urls.add(url)

    #
    print("Sorting ...")
    urls = list(urls)
    urls = sorted(urls)
    with open(filename, "w") as fw:
        for i in urls:
            fw.write(f"{i}\n")

if __name__ == "__main__":
    
    # #
    # filepath = f"./popular_1001_1231.json"
    # filename = f"./popular_1001_1231_sort.txt"
    # #
    filepath = "./keyword_正妹_0101_0301.json"
    filename = "./keyword_正妹_0101_0301_sort.txt"
    main(filepath, filename)