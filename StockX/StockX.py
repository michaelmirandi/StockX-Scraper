import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import os
import time
import random
from itertools import cycle
from pymongo import MongoClient
from datetime import datetime

class req:
    def __init__(self, h):
        self.header = {"User-Agent": h}

    def validate(self, test_url):
        try:
            r = requests.get(test_url, headers=self.header, proxies=self.proxy)
            return (r.status_code == 200)
        except Exception:
            return False


class StockX_Scraper():
    '''
    Class based view for quickly creating scrapers that can be threaded.
    '''
    def __init__(self, proxy, lst_headers):
        # can't stop me... try again https://www.perimeterx.com/whywasiblocked/
        # set a list of headers to cycle through
        print('Testing all proxy and headers for validity. This may take a while...')
        self.reqs = []
        for header in lst_headers:
            r = req(header)
            self.reqs.append(req(header))
        self.req_pool = cycle(self.reqs)
        self.lst_links = []
        self.proxy = {'http': "http://" + proxy,}
        self.client = MongoClient("mongodb+srv://soelml:WheresMyBelt29!@soleml-sandbox-s5fy7.mongodb.net/test?retryWrites=true&w=majority")
        self.db = self.client.SoleML
        self.col_products = self.db['products']
        self.col_transactions = self.db['test_transactions']

    def historical_scraper_main_002(self):
        lst_failed = []
        global total_scraped
        total_scraped = 0; count = 0; product_count = 0

        for product in self.col_products.find():
            count += 1
            if count > 4:
                break
            else:
                try:
                    self.get_historical_product_data_001(product['_id'])
                    product_count += 1
                except Exception as e:
                    print('Error', str(e))
                    print('Could not scrap:', product['name'])
                    lst_failed.append(product['_id'])
                    self.sleep(2, 3, 'Sleeping for')
                    pass
            print(product_count, 'product(s) scraped so far.')
        print('Total scraped:', total_scraped)
        print(lst_failed)

    def get_historical_product_data_001(self, sku):
        '''
        Function: get_historical_product_data()
        Parameters: sku (specific sku that you want to get information on)
        Returns: Nothing
        Purpose: To collect the historical data on a certain sku and store in MongoDB
        Update for last time scraped...
        '''

        global total_scraped
        df_historicaldata = pd.DataFrame()
        page_count = 1
        while True:

            url = 'https://stockx.com/api/products/' + \
            sku + \
            '/activity?state=480&currency=USD&limit=20000&page='+ \
            str(page_count) + '&sort=createdAt&order=DESC&country=US'
            count = 0
            while True:
                print('Getting valid request for ', url)
                req = next(self.req_pool)
                header = req.header
                r = requests.get(url, headers=header, proxies=self.proxy)
                if r.status_code == 200: break; self.sleep(1, 1, None)
                count += 1
                if count > 2:
                    count = 0
                    self.sleep(90, 110, '---Resting for')

            data_historical = r.json()
            if 0 < data_historical['Pagination']['total'] < 20000:
                df_historicaldata = df_historicaldata.append(pd.DataFrame(list(data_historical['ProductActivity'])))
                page_count += 1
                total_scraped += data_historical['Pagination']['total']
                break
            elif (page_count - 1) * 20000 <= data_historical['Pagination']['total'] <= page_count * 20000:
                    df_historicaldata = df_historicaldata.append(pd.DataFrame(list(data_historical['ProductActivity'])))
                    page_count += 1
                    self.sleep(2, 3, 'Sleeping for')
            elif data_historical['Pagination']['total'] == 0:
                break
            else:
                total_scraped += data_historical['Pagination']['total']
                break

        if df_historicaldata.empty: print('No records for', sku)
        df_historicaldata['productId'] = df_historicaldata['productId'].apply(lambda x: sku)
        df_historicaldata = df_historicaldata.rename(columns={'createdAt': 'soldAt'})
        df_historicaldata = df_historicaldata[['productId', 'soldAt', 'shoeSize', 'amount']]
        df_historicaldata = df_historicaldata.astype({'soldAt': 'datetime64[ns]'})
        self.col_transactions.insert_many(df_historicaldata.to_dict(orient='records'))
        self.sleep(2, 3, 'Sleeping for')

    def product_link_scraper_001(self, home_page, start_page, end_page):
        '''
        Function: get_product_information_002_002()
        Parameters: product_link (link of product to gather)
        Returns: Nothing
        Purpose: To collect the links for products in lst_links
        Call this first to get the links of what you want to scrap
        Need to fix to automatically detect the start and end pages...
        '''
        for page in range(start_page, end_page):
            url = home_page + '&page=' + str(page)
            count = 0
            while True:
                count += 1
                print('Getting valid request for ', url)
                req = next(self.req_pool)
                header = req.header
                r = requests.get(url, headers=header, proxies=self.proxy)
                if r.status_code == 200: break
                if count > 3:
                    count = 0
                    self.sleep(90, 110, '---Resting for')
            soup = BeautifulSoup(r.content, 'html.parser')
            #print(soup)
            results = soup.find_all('div', {'data-testid':'product-tile'})
            for div_tag in results:
                for a_tag in div_tag.find_all('a'):
                    self.lst_links.append('https://stockx.com' + a_tag['href'])

            self.sleep(2, 3, 'Sleeping for')


    def product_info_main_001(self, home_page, start_page, end_page):
        '''
        Gather all product links, then get all product info from the links
        '''
        self.product_link_scraper_001(home_page, start_page, end_page)
        random.shuffle(self.lst_links)

        for link in self.lst_links:
            try:
                # inserts the product information into the products collection
                self.get_product_information_002(link)
                sleep_time = random.randint(2,4)
                print('Sleeping for', sleep_time, 'seconds...')
                time.sleep(sleep_time)
            except Exception as e:
                print('---Error:', e)
                print('Could not get ', link)
                self.sleep(2, 3, 'Sleeping for')
                pass

    def get_product_information_002(self, product_link):
        '''
        Function: get_product_information_002_002()
        Parameters: product_link (link of product to gather)
        Returns: Nothing
        Purpose: To collect the product information for the product_scraper function
        '''
        count = 0
        while True:
            print('Getting valid request for ', product_link)
            req = next(self.req_pool)
            header = req.header
            r = requests.get(product_link, headers=header, proxies=self.proxy)
            if r.status_code == 200: break; time.sleep(1)
            count += 1
            if count > 2:
                count = 0
                self.sleep(90, 110, '--- Resting for')
        # parse the request into a BS object using BS4
        soup = BeautifulSoup(r.content, 'html.parser')
        if soup.find("span", {"data-testid":'product-detail-style'}) is not None:
            style_num = soup.find("span", {"data-testid":'product-detail-style'}).text
        else:
            style_num = None

        script_tag = json.loads(soup.find_all('script', type='application/ld+json')[3].text)


        if 'releaseDate' not in script_tag: script_tag['releaseDate'] = None
        if '--' == script_tag['releaseDate']: script_tag['releaseDate'] = None
        if script_tag['releaseDate'] is not None: script_tag['releaseDate'] = datetime.strptime(script_tag['releaseDate'], '%Y-%m-%d')
        if 'sku' not in script_tag: script_tag['sku'] = None

        dict_product = {'_id': script_tag['sku'], 'name': script_tag['name'], 'brand': script_tag['brand'],
                        'model': script_tag['model'], 'style': style_num, 'color': script_tag['color'],
                        'releasedate': script_tag['releaseDate']}
        self.col_products.insert_one(dict_product)
        print("Inserted", script_tag['name'])

    def sleep(self, lower_time, upper_time, message):
        '''
        Function to sleep for a set amount of time
        '''
        sleep_time = random.randint(lower_time, upper_time)
        print(message, sleep_time, 'seconds...')
        time.sleep(sleep_time)

    def main(self, home_page, start_page, end_page):
        '''
        Main function to call other functions that gather links, gather product info, and gather historical data
        '''
        self.product_info_main_001(home_page, start_page, end_page)
        self.historical_scraper_main_002()