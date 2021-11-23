# from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import glob
from bs4 import BeautifulSoup
import pandas as pd
import re

class SportTracData:
    
    def __init__(self):
        self.years = [2013, 2012, 2011, 2010]
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(options=self.options)
        
    def extract(self):
        for year in self.years:
            self.scroll_down_transaction_page(year)
            self.get_transaction_data(year)
        self.driver.close()
        
    def scroll_down_transaction_page(self, year):
        self.link = 'https://www.spotrac.com/nba/transactions/' + str(year) + '/all/'
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
                # if i == 51:
                #     break
            except:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") #Scroll down to bottom
                
    def get_transaction_data(self, year):
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
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
        df.to_csv('data/extract/nba_transactions_' + str(year) + '.csv',index=False)
    
    def transform():
        df = read_files()
        df = clean_dataframe(df)
        
    
    def read_files():
        df_all = pd.DataFrame()
        for file in glob.glob('data/extract/*'):
            df = pd.read_csv(file)
            df_all = pd.concat([df_all, df])
        df_all.reset_index(drop=True,inplace=True)
        return df_all
    
    def clean_dataframe(df):
        df['transaction'] = df['transaction'].str.strip()
        return df
    
    # def get_team_names():
    #     '''
    #     Instead of manually creating the list of team names to extract from the transaction
    #     field, pull all the team names from the syntax 'Waived by [team_name]' since
    #     every team should have waived a player at least once in the past ten years. 
    #     '''
    #     df_subset = df[df['transaction'].str.contains('Waived by')]
    #     teams = df_subset['transaction'].apply(lambda x: x.split('Waived by ')[1].split(r')')[0] + ')').unique()
    #     teams = '|'.join(teams)
    #     return teams
        
    def transactions():
        '''
        < TEAM NAME >
            - Use get_team_names() method to get team name variables and pull
            
        < DOLLAR AMOUNT >
            - Use regex to pull dollar amounts
            
        < ACTIONER > 
            - Was the action committed via the Player or the Team?
        
        < ACTION > 
            - Use regex to pull what type of action was conducted
            - signed / exercised / declined / extended
            
        < CONTRACT/OFFER > 
            - Use regex to pull what type of offer/contract it is:
                
        < CONTRACT/OFFER DETAILS >
        

            
        ----------------------------------------------------------------------
        ##############
        Player Actions
        ##############
        < ACTION > a <CONTRACT OFFER> with <TEAM > - <CONTRACT DETAILS> 
            - Signed a 3 year $4.2 million contract with Charlotte (CHA) - $500k guaranteed 			
            - Signed a two-way contract with Houston (HOU) - converted Exhibit 10 
            - Signed a contract with Memphis (MEM) - Exhibit 10 		
            
            
        Retired from Professional Basketball
            
        ##############
        Team Actions
        ##############
        <TEAM > <ACTION> <CONTRACT/OFFER TYPE> for <YEAR>
            - Charlotte (CHA) exercised $5.35 million option for 2020-21 
            - Memphis (MEM) declined $8.93 million option for 2020-21 	
        
        <TEAM > <ACTION> <CONTRACT/OFFER TYPE>; <CONTRACT/OFFER TYPE DETAILS>
            - Sacramento (SAC) extended $6,265,631 Qualifying Offer; becomes Restricted Free Agent 
            - Boston (BOS) declined $1,876,700 Qualifying Offer; becomes Unrestricted Free Agent 				 
				
        <ACTION> by <TEAM >
            - Waived by Boston (BOS) 	
            
        < TEAM > <ACTION> < YEAR >
            - New Orleans (NOP) fully guaranteed salary for 2019-20 	
        
    '''
    df['team'] = None
    df['actioner'] = None
    df['action'] = None
    df['contract_offer'] = None
    df['contract_offer_details'] = None
    
    actions = {
        'Waived' : [
            ['action', 'team', 'contract_offer_details'], 
            '(?P<action>\w*) by (?P<team>.*\))(?P<contract_offer_details>.*)?'
            ],
         # Declined $16.2 million Player Option with San Antonio (SAS) for 2017-18
        'Signed|Declined' : [
            ['action', 'contract_offer', 'team', 'contract_offer_details'],
            '(?P<action>\w*) (?P<contract_offer>.*) with (?P<team>.*\))(?P<contract_offer_details>.*)'
            ],
        # Declined $16.2 million Player Option with San Antonio (SAS) for 2017-18
        # 'Declined' : [
        #     ['action', 'contract_offer', 'team', 'contract_offer_details'],
        #     '(?P<action>\w*) (?P<contract_offer>.*) with (?P<team>.*\))(?P<contract_offer_details>.*)'
        #     ],
        # New York (NYK) declined $1.42 million option for 2019-20
        # Charlotte (CHA) exercised $5.35 million option for 2020-21 
        'option' : [
            ['team', 'action', 'contract_offer'],
            '(?P<team>.*\))\s(?P<action>\w*)\s(?P<contract_offer>.*option)'],
        # Sacramento (SAC) extended $6,265,631 Qualifying Offer; becomes Restricted Free Agent 
        # Boston (BOS) declined $1,876,700 Qualifying Offer; becomes Unrestricted Free Agent 	
        'Qualifying Offer' : [
            ['team', 'action', 'contract_offer', 'contract_offer_details'],
            '(?P<team>.*\))\s(?P<action>\w*)\s(?P<contract_offer>.*);\s(?P<contract_offer_details>.*)'],
        'renounced' : [
            ['team', 'action'],
            '(?P<team>.*\))\s(?P<action>.*)'],
        # New Orleans (NOP) guaranteed salary for 2019-20
        # New Orleans (NOP) fully guaranteed salary for 2019-20
        'guaranteed.*salary': [
            ['team', 'action'],
            '(?P<team>.*\))\s(?P<action>.*) for'],
        }
    
    df_empty = df[df['action'].isnull()]
    df_not_empty = df[df['transaction'].str.contains('Declined',na=False, flags=re.IGNORECASE)]
    
    for k, v in actions.items():
        indices_to_change = df[df['transaction'].str.contains(k)].index.values
        df.loc[indices_to_change, v[0]] = df.loc[indices_to_change, 'transaction'].str.extract(v[1])
    
    
    
      '(?=.*assigned)(?=.*G league)':
          ['assigned player to G league', 'assigned to G league',
           'The (?P<team>.+?) assigned (?P<player>.+) to the'],
          
    
    df.loc[df['transaction'].str.contains('Waived', flags=re.IGNORECASE), ['action','team', 'contract_offer_details']] = \
        df[df['transaction'].str.contains('Waived', flags=re.IGNORECASE)]['transaction']\
            .str.extract('(?P<action>.*) by (?P<team>.*\))(?P<action_details>.*)?')
    
    df.loc[df['transaction'].str.contains('Signed', flags=re.IGNORECASE), 
           ['action', 'contract_offer', 'team', 'contract_offer_details']] = \
        df[df['transaction'].str.contains('Signed', flags=re.IGNORECASE)]['transaction']\
            .str.extract('(?P<action>.*) a (?P<contract_offer>.*) with (?P<team>.*\))(?P<contract_offer_details>.*)')
    
    
    
    
    
    
    
for k,v in actions.items():
    x.loc[x['transaction'].str.contains(k, flags=re.IGNORECASE), ['player','team']] = \
        x[x['transaction'].str.contains(k, flags=re.IGNORECASE)]['transaction'].str.extract(v[2])
    
for k, v in actions.items():
    x['team_action'] = \
        np.where(x['transaction'].str.contains(k, flags=re.IGNORECASE), v[0], x['team_action'])
    
    
    
    
    
    
    
    
    
    


if __name__ == '__main__':
    ScrapeSportTrac().run()
    

  

    
