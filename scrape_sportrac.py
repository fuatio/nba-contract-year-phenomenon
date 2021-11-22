# from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# import re
# import sys
from bs4 import BeautifulSoup
import pandas as pd

class ScrapeSportTrac:
    def __init__(self):
        self.link = 'https://www.spotrac.com/nba/transactions/'
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(options=self.options)
    
    def get_transaction_data(self):
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        self.driver.close()
        transactions = {'date' : [], 'player_name' : [], 'player_link' : [], 'transaction' : []}
        for article in soup.find_all('article', {'class':'odd'}):
            for span in article.find_all('span', {'class':'date'}):
                transactions['date'].append(span.getText())
            for div in article.find_all('div', {'class':'cnt'}):
                for h3 in div.find_all('h3'):
                    for player_link in h3.find_all('a', href=True):
                        transactions['player_link'].append(player_link['href'])
                    transactions['player_name'].append(h3.getText().split(',')[0])
                for p in div.find_all('p'):
                    transactions['transaction'].append(p.getText())
        df = pd.DataFrame.from_dict(transactions)
        df.to_csv('nba_transactions.csv',index=False)
    
    def scroll_down_transaction_page(self):
        self.driver.get(self.link)
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        self.driver.find_element(By.CLASS_NAME, 'show-more').click()
        i = 0
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") #Scroll down to bottom
        while True:
            try: # Click on element to load more comments
                print(i)
                WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.CLASS_NAME, "show-more"))).click()
                i += 1
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") #Scroll down to bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                if i % 25 == 0:
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    last_date = soup.find_all('span', {'class' : 'date'})[-1].getText()
                    print(last_date)
                if i == 51:
                    break
            except:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") #Scroll down to bottom

    def scrape_sportrac(self):
        self.scroll_down_transaction_page()
        self.get_transaction_data()

if __name__ == '__main__':
    ScrapeSportTrac().scrape_sportrac()
    

  

    
