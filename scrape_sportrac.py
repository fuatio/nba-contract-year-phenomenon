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
    
    import numpy as np
    
    def get_team_names():
        '''
        Instead of manually creating the list of team names to extract from the transaction
        field, pull all the team names from the syntax 'Waived by [team_name]' since
        every team should have waived a player at least once in the past ten years. 
        '''
        df_subset = df[df['transaction'].str.contains('Waived by')]
        teams = df_subset['transaction'].apply(lambda x: x.split('Waived by ')[1].split(r')')[0] + ')').unique()
        teams = '|'.join(teams)
        team_regex = '(' + ''.join(['\\' + letter if re.match('\(|\)', letter) else letter for letter in teams]) + ')'
        return team_regex
    
    def extract_transactions(action_type, columns, regex):
        if isinstance(columns, list)==True:
            for column in columns:
                if column not in df.columns:
                    df[column] = None
        else:
            if columns not in df.columns:
                df[columns] = None
        df['Action_Type'] = np.where(df['transaction'].str.contains(regex),
                                     action_type,
                                     df['Action_Type'])
        
        transaction_idx = df[df['Action_Type'] == action_type].index.values
        
        df.loc[transaction_idx, columns] = np.where(df.loc[transaction_idx, columns].isnull(), 
                                                    df.loc[transaction_idx, 'transaction'].str.extract(regex, expand=False), 
                                                    df.loc[transaction_idx, columns])
        return df
    
    df = read_files()
    df = clean_dataframe(df)
    # df = df[0:1000]
    df['Action_Type'] = None

    team_regex = get_team_names()
    
    # Agreed to a 3 year $31.5 million contract with Milwaukee (MIL)
    # Signed a contract with Golden State (GSW) - Exhibit 10
    # Signed a 5 year $189.9 million maximum contract with Golden State (GSW)
    df = extract_transactions('Signed a contract',
                              ['Action_Details', 'Team'], 
                              regex='^(?:Signed|Agreed) (?:a )?(.*?extension|.*?contract) with ' + team_regex)
    
    # Atlanta (ATL) exercised $2.6 million option for 2019-20
    df = extract_transactions('Team Exercised Option',
                              ['Team', 'Action_Details'],
                              regex = '^' + team_regex + ' exercised ' + '(.*option)')
    # Cleveland (CLE) declined $3.87 million option for 2020-21
    df = extract_transactions('Team Declined Option',
                              ['Team', 'Action_Details'],
                              regex = '^' + team_regex + ' declined ' + '(.*option)')
    
    # Exercised $27.09 million option with Miami (MIA) for 2019-20
    # Exercised $27.1 million Player Option with Charlotte (CHA) for 2020-21
    # Exercised $4.25 million Player Option for the 2012-2013 season
    df = extract_transactions('Player Exercised Option',
                              ['Team', 'Action_Details'],
                              regex = '^(?:Exercised|^Exercsied) (.*) (?:option|Option)(?: with )?' + team_regex + '?')
    
    # Declined $25.1 million option with Sacramento (SAC) for 2019-20
    df = extract_transactions('Player Declined Option',
                              ['Action_Details', 'Team'],
                              regex = '^Declined (.*) option with ' + team_regex)
    
    # Washington (WAS) fully guaranteed salary for 2019-20
    # Miami (MIA) guaranteed $1 million for 2019-20
    df = extract_transactions('Team Guaranteed Salary',
                              ['Team', 'Action_Details'],
                              regex = '^' + team_regex + '.*guaranteed(?: salary)? (.*) for')
    
    # Milwaukee (MIL) extended $3,021,354 Qualifying Offer; becomes Restricted Free Agent
    # Brooklyn (BKN) extended Qualifying Offer; becomes a Restricted Free Agent
    df = extract_transactions('Team Extended Qualifying Offer',
                              ['Team', 'Action_Details'],
                              regex = '^' + team_regex + '.*extended (.*)(?:Qualifying Offer)')
    
    # Houston (HOU) declined Qualifying Offer; becomes Unrestricted Free Agent
    # New Orleans (NOP) declined to extend Qualifying Offer; becomes Unrestricted Free Agent
    # New York (NYK) declined $2,024,075 Qualifying Offer; becomes Unrestricted Free Agent
    # Los Angeles (LAL) withdrew Qualifying Offer; becomes Unrestricted Free Agent
    df = extract_transactions('Team Declined Qualifying Offer',
                              ['Team', 'Action_Details'],
                              regex = '^' + team_regex + '.*(?:declined|withdrew)(?:to extend )?(.*) (?:Qualifying Offer)')
    
    # Brooklyn (BKN) renounced their free-agent exception rights
    df = extract_transactions('Team Renounced their free-agent exception rights',
                              'Team',
                              regex = '^' + team_regex + ' renounced')
    
    # Waived by Los Angeles (LAL)
    df = extract_transactions('Team Waived Player',
                              'Team',
                              regex = 'Waived by ' + team_regex)
    
    
    # Drafted by Orlando (ORL): Round 1 (#16 overall)
    # Drafted 2nd Round by Miami (MIA): Round 2 (#32 overall)
    df = extract_transactions('Team Drafted Player',
                              ['Team', 'Action_Details'],
                              regex = '^Drafted.*by ' + team_regex + ': (.*)')
    
    # Fined $2,000 for ejection from LAL-ORL game
    df = extract_transactions('Player Fined',
                              'Action_Details',
                              regex = '^Fined (.*)')
    
    # Suspended 2 games (forfeit $379,374) for fighting during MIN-PHI game
    # Suspended 6 games (forfeit $500,690) for failure to adhere to team policies, violation of team rules and continued insubordination
    df = extract_transactions('Player Suspended',
                              'Action_Details',
                              regex = '^Suspended (.*)')
    
    # Traded to New Orleans (NOP) from Milwaukee (MIL) as part of a 3-team trade: Detroit (DET) traded  Stanley Johnson to New Orleans (NOP); Milwaukee (MIL) traded  Thon Maker to Detroit (DET); Milwaukee (MIL) traded 2021 2nd round pick, 2020 2nd round pick, 2020 2nd round pick and 2019 2nd round pick to New Orleans (NOP); New Orleans (NOP) traded  Nikola Mirotic to Milwaukee (MIL)
    df = extract_transactions('Team Traded Player',
                              ['Action_Details', 'Team'],
                              regex = '^Traded (to.*) from ' + team_regex)
    
    # Released by Indiana (IND)
    # Released from 10-day contract by Brooklyn (BKN)
    df = extract_transactions('Team Released Player',
                              'Team',
                              regex = '^Released.*by ' + team_regex)
    
    check = df[df['Action_Type'].isnull()]
    
    
    
    
    
    
    
    
    
    
    
    
    df = extract_transactions('Waived by Team',
                              'Team',
                              regex = '^(?:Waived by )' + team_regex)
    
    regex_team_1 = '(Suspended|Fined|Traded)|(^|by )' + team_regex
    player_transactions = df[~df['transaction'].str.contains(regex_team_1)].index.values
    team_transactions = df[df['transaction'].str.contains(regex_team_1)].index.values
    
    df.loc[player_transactions, 'Player_Action'] = True
    df.loc[team_transactions, 'Player_Action'] = False
    '''
    Action Types:
    - Player signed a contract
        Signed a 2 year contract extension with Denver (DEN)
        Signed a two-way contract with Charlotte (CHA) - converted Exhibit 10 contract
        Signed a 2 year $70.14 million veteran contract extension with Washington (WAS) - includes 2022-23 Player Option
        Signed a 3 year $100 million contract extension with Portland (POR)
        
        ^(Signed)
        
    - Team exercised 
    'exercised'
    'declined'
    'withdrew|declined Qualifying Offer'
    'renounced their free agent exception rights'
    'extended Qualifying Offer'
    'declined Qualifying Offer'
    '''
    df = extract_transactions(['Action', 'Action_Type', 'Team'], 
                              player_transactions, 
                              regex='^(Signed)(with ' + team_regex)
    
    df = extract_transactions(['Action', 'Team'], player_transactions, regex='^(Waived).*by ' + team_regex)
    
    # 
    
    df = extract_transactions(['Action', 'Team'], player_transactions, regex='^(\w*).*with ' + team_regex)
    df = extract_transactions(['Action', 'Team'], team_transactions, regex = '^(\w*).*by ' + team_regex)
    df = extract_transactions(['Team', 'Action'], team_transactions, regex='^' + team_regex + ' (.*?ed|Offer) ')
    df = extract_transactions(['Action', 'Action_Details'], team_transactions, regex='(Fined).*for (.*)')
    
    check = df[df['transaction'].str.contains('Agreed')]
    




column = ['Action', 'Team']
transactions = team_transactions    
regex = '(Waived) by ' + team_regex
    
    df['Contract_Offer'] = df[player_transactions]['transaction'].str.extract('\w* (?:a? ?)(.*) with')
    df['Contract_Offer_Details'] = df[player_transactions]['transaction'].str.extract('- (.*)')
    
    
    df[['Action', 'Team']] = df.loc[team_transactions, 'transaction'].str.extract('(Waived) by ' + team_regex)
    
    (?P<action>\w*) by (?P<team>.*\))
    
    

    
        
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
    
    df = read_files()
    df = clean_dataframe(df)
    team_regex = get_team_names()
    actions = {
        'Waived' : [
            ['action', 'team', 'contract_offer_details'], 
            '(?P<action>\w*) by (?P<team>.*\))(?P<contract_offer_details>.*)?'
            ],
        # Signed a two-way contract with Washington (WAS) - converted Standard contract
        # Signed a 2 year $70.14 million veteran contract extension with Washington (WAS) - includes 2022-23 Player Option
        # Signed with New York (NYK) for the remainder of 2012-2013
        # Declined $16.2 million Player Option with San Antonio (SAS) for 2017-18
        # Declined $25.1 million option with Sacramento (SAC) for 2019-20
        # Declined player option for the 2012-2013 season; becomes an unrestricted free agent
        # Declined a $1.4 million option for 2011-2012
        '(Signed|Declined).*contract' : [
            ['action', 'contract_offer', 'team', 'contract_offer_details'],
            '(?P<action>\w*) (?P<contract_offer>.*) with (?P<team>.*\))(?P<contract_offer_details>.*)'
            ],
        # New York (NYK) declined $1.42 million option for 2019-20
        # Charlotte (CHA) exercised $5.35 million option for 2020-21 
        team_regex + '.*option' : [
            ['action', 'contract_offer', 'team', 'contract_offer_details'],
            '(?P<team>.*\))\s(?P<action>\w*)\s(?P<contract_offer>.*option)(?P<contract_offer_details>.*)'],
        # Sacramento (SAC) extended $6,265,631 Qualifying Offer; becomes Restricted Free Agent 
        # Boston (BOS) declined $1,876,700 Qualifying Offer; becomes Unrestricted Free Agent 	
        team_regex + '.*Qualifying Offer' : [
            ['team', 'action', 'contract_offer', 'contract_offer_details'],
            '(?P<team>.*\))\s(?P<action>\w*)\s(?P<contract_offer>.*);\s(?P<contract_offer_details>.*)'],
        team_regex + '.*renounced' : [
            ['team', 'action'],
            '(?P<team>.*\))\s(?P<action>.*)'],
        # New Orleans (NOP) guaranteed salary for 2019-20
        # New Orleans (NOP) fully guaranteed salary for 2019-20
        team_regex + '.*guaranteed.*salary': [
            ['team', 'action'],
            '(?P<team>.*\))\s(?P<action>.*) for'],
        }
    
    x ='\(' + team_regex  + '.*Qualifying Offer\)'
    df_empty = df[df['action'].isnull()]
    df_not_empty = df[df['transaction'].str.contains('Signed',na=False, flags=re.IGNORECASE)]
    
    for k, v in actions.items():
        indices_to_change = df[df['transaction'].str.contains(k)].index.values
        df.loc[indices_to_change, v[0]] = df.loc[indices_to_change, 'transaction'].str.extract(v[1], expand=True)
    
    
    
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
    

  

    
