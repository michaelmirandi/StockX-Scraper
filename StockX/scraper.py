import StockX
import random

print("Reading in headers... this may take a while.")
file_headers = open('headers.txt', 'r', encoding='utf8')
lst_headers = file_headers.read().splitlines()
random.shuffle(lst_headers)

file_links = open('test_links.txt', 'r')
lst_links = file_links.read().splitlines()

proxy = "http://4659b951bb7b4c1c8366ae870c52c6d8:@proxy.crawlera.com:8010/"


s = StockX.StockX_Scraper(proxy, lst_headers)

print('Number of combinations:', len(s.reqs))

s.historical_scraper_main_002()
