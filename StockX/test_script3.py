import SoleML_V2

proxy = "http://4659b951bb7b4c1c8366ae870c52c6d8:@proxy.crawlera.com:8010/"
lst_headers = ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:36.0) Gecko/20100101 Firefox/36.0',
              'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:37.0) Gecko/20100101 Firefox/37.0']
s = SoleML_V2.StockX_Scraper(proxy, lst_headers)
s.historical_scraper_main_002()
