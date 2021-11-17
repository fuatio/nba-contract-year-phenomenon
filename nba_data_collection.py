import pandas as pd
from bs4 import BeautifulSoup,Comment
import requests
import numpy as np
import re
import random
import time
import string
from sklearn.utils import shuffle
from tqdm import tqdm

#-----------------------------------------------------------------------------#
#get the pages that have the box_scores
def get_transactions():
    ''' Get all the transactions from Real GM website '''
    
    years = ['1984','1985','1986','1987','1988','1989',
             '1990','1991','1992','1993','1994','1995','1996','1997','1998','1999',
             '2000','2001','2002','2003','2004','2005','2006','2007','2008','2009',
             '2010','2011','2012','2013','2014','2015','2016','2017','2018','2019']
    years = ['2003','2004']
    #get all the page_links to scrape:
    final_df = pd.DataFrame()
    for year in years:
        link = 'https://basketball.realgm.com/nba/transactions/league/' + year
        
        response = requests.get(link)
        soup = BeautifulSoup(response.text, "html.parser")
    
        text = []
        for li in soup.find_all('div',{'class':"portal widget fullpage"}):
            if bool(re.search('\w{3}\s\d{2},\s\d{4}', str(li)) or (re.search('\w{3}\s\d{1},\s\d{4}', str(li)))):
                text.append(li.text)
                
        z = pd.DataFrame(columns=['text'], data=text)
        #get all text between collapse all rows
        #collapse_locations = z[z['text'].str.contains('Collapse')].index.tolist()[-2:]
        #get all the text betweent he collapse indeces
        #z = z.loc[collapse_locations[0]+2:collapse_locations[1]-1, 'text']
        z['text'] = z['text'].str.replace('^\n\n','').str.replace('^\n','')
        z = z['text'].str.split('\n', expand=True)
        z.drop_duplicates(0, keep='last', inplace=True)
        #-----------------------------------------------------------------------------#
        z = z.replace('',np.nan).dropna(how='all')
        z = z.set_index(0)\
             .stack(level=0)\
             .reset_index(name='transaction')\
             .drop(columns='level_1')\
             .rename(columns={0:'date'})
        z['season'] = link.split('/')[-1]
        final_df = final_df.append(z)
    return final_df
#--------------------------------------------------------------------------------------------------------------------------#     
df = get_transactions()

#--------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------#
def get_match(dataframe, column, matching_column, **matching_values):
    '''
    dataframe = dataframe to 
    column = column to check for matches
    matching_column = column where you want the matching value to appear
    matching_values = matching values to check for, used as a dictionary where value replaces key value
    (i.e. pass dictionary with matching regex value in key, and string to replace in value)
    
    '''
    dataframe[matching_column] = np.nan
    
    for k, v in matching_values.items():
        dataframe[matching_column] = \
            np.where(dataframe[column].str.contains(k, flags=re.IGNORECASE), v, dataframe[matching_column])
#--------------------------------------------------------------------------------------------------------------------------#  
#--------------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------------#
'''create dictionary: player actions and team actions in subset '''

check = x[x['transaction'].str.contains('can match')]

actions = \
    {'signed a contract':
          ['signed player to contract', 'signed contract',
           '(?P<player>.+?) signed a contract with the (?P<team>.+).'],
        
           
     'signed a multi-year contract':
          ['signed player to multi-year contract','signed multi-year contract',
           '(?P<player>.+?) signed a multi-year contract with the (?P<team>.+).'],

     '(?=.*signed multi)(?=.*can match)':
          ['can match contract', 'signed a multi-year offer sheet',
           '(?P<player>.+?) signed a multi-year offer (?:.+) the (?P<team>.+) can'],
           
     'signed a multi-year offer sheet':
          ['signed player to a multi-year offer sheet','signed multi-year offer sheet',
           '(?P<player>.+?) signed a multi-year contract with the (?P<team>.+).'],
    
     'signed a veteran extension':
          ['signed player to veteran extension','signed veteran extension',
           '(?P<player>.+?) signed a veteran extension with the (?P<team>.+).'],
           
     'signed a rookie scale extension':
          ['signed player to rookie scale extension','signed rookie scale extension',
           '(?P<player>.+?) signed a rookie scale extension with the (?P<team>.+).'],
          
     'signed a two-way contract':
          ['signed player to two-way contract','signed two-way contract',
           '(?P<player>.+?) signed a two-way contract with the (?P<team>.+).'],
         
     'ended the two-way contract':
          ['ended two-way contract','became free agent',
           '(?P<player>.+?) ended the two-way contract with the (?P<team>.+).'],
           
     'renounced their Draft Rights':
          ['renounced their Draft Rights', 'became an unrestricted free agent',
           'The (?P<team>.+?) renounced their Draft Rights to make (?P<player>.+?) an Unrestricted FA'],
     
     'terminated the 10 day contract':
          ['terminated 10 day contract', 'became a free agent',
           'The (?P<team>.+?) terminated the 10 day contract for (?P<player>.+).'],
           
     'tendered a Qualifying Offer':
          ['tendered a Qualifying Offer', 'became a restricted free agent',
           'The (?P<team>.+?) tendered a Qualifying Offer to make (?P<player>.+?) a Restricted'],
           
     'exercised a player option':
          ['player exercised option', 'exercised player option to extend contract',
           '(?P<player>.+?) exercised a Player Option to extend his contract.'],
      
     'exercised their Team Option to extend the contract of':
          ['exercised team option to extend contract', 'team extended contract',
           'The (?P<team>.+?) exercised their Team Option to extend the contract of (?P<player>.+).'],
           
     'exercised an Early Termination Option to void the remaining seasons on his contract':
         ['N/A', 'used early termination option - became a free agent',
          '(?P<player>.+?) exercised an Early Termination Option to void the remaining seasons on his contract'], 
          
     'voided his ability to terminate his contract':
         ['N/A', 'voided his ability to terminate his contract early',
          '(?P<player>.+?) voided his ability to terminate his contract early'],
            
      'renounced their free-agent exception rights':
          ['team renounced their exception rights', 'became a free agent',
           'The (?P<team>.+?) renounced their free-agent exception rights to (?P<player>.+).'],
           
      '(?=.*the contract of)(?=.*was voided)(?=.*immediately became a)':
          ['team voided contract', 'became a free agent',
           'The contract of (?P<player>.+?) was voided.'],
           
      #'(?=.*was|were)(?=.*acquired)':
      #    ['team traded player', 'traded',
      #     'N/A'],
           
      'matched the offer sheet':
          ['team matched offer sheet', 'signed contract',
           'The (?P<team>.+?) matched the offer sheet that (?P<player>.+) signed with'],
      
      '(?=.*placed the contract)(?=.*on waivers)':
          ['placed player on waivers', 'placed on waivers',
           'The (?P<team>.+?) placed the contract of (?P<player>.+) on waivers.'],
        
      'made a successful waiver claim':
          ['made successful waiver claim for player', 'signed contract',
           'The (?P<team>.+?) made a successful waiver claim for the contract of (?P<player>.+)'],
           
      'utilized the amnesty provision':
          ['utilized the amnesty provision', 'became a free agent',
           'The (?P<team>.+?) utilized the amnesty provision on the contract of (?P<player>.+)'],
    
      '(?=.*assigned)(?=.*G league)':
          ['assigned player to G league', 'assigned to G league',
           'The (?P<team>.+?) assigned (?P<player>.+) to the'],
           
      'NBA Draft':
          ['team selected player in draft', 'player selected in draft',
           'The (?P<team>.+?) selected (?P<player>.+?) in Round'],

      #'(?=.*trade)(?=.*voided)':
      #    ['trade voided', 'trade voided',
      #     'N/A'],
           
      'withdrew their Qualifying Offer':
          ['withdrew qualifying offer', 'became an unrestricted free agent',
           'The (?P<team>.+?) withdrew their Qualifying Offer to make (?P<player>.+?) an Unrestricted'],
       
      '(?=.*previously with the)(?=.*became a free agent)':
         ['N/A', 'became a free agent',
          '(?P<player>.+?), previously with the (?P<team>.+?), became a free agent.']
    }
      
     
#check['player'] = check['transaction'].str.extract('(?P<player>.+?) exercised a Player Option to extend his contract')
       
check = x[x['transaction'].str.contains('exercised',flags = re.IGNORECASE)]
#--------------------------------------------------------------------------------------------------------------------------#
x = df.copy()
#get_match(x, 'transaction', 'player_action', **player_actions)
#test = x[x['player_action']=='nan']
#--------------------------------------------------------------------------------------------------------------------------#
x['team_action'] = np.nan
for k, v in actions.items():
    x['team_action'] = \
        np.where(x['transaction'].str.contains(k, flags=re.IGNORECASE), v[0], x['team_action'])

x['player_action'] = np.nan
for k, v in actions.items():
    x['player_action'] = \
        np.where(x['transaction'].str.contains(k, flags=re.IGNORECASE), v[1], x['player_action'])
    
x['player'] = np.nan
x['team'] = np.nan
for k,v in actions.items():
    x.loc[x['transaction'].str.contains(k, flags=re.IGNORECASE), ['player','team']] = \
        x[x['transaction'].str.contains(k, flags=re.IGNORECASE)]['transaction'].str.extract(v[2])
        
        
        (?=.*placed the contract)(?=.*on waivers)
        
check = x[x['transaction'].str.contains('(?=.*signed)(?=.*can match)', flags=re.IGNORECASE)]
        
z = check['transaction'].str.extract('(?P<player>.+?) signed a multi-year offer (?:.+) the (?P<team>.+) can')


Michael Redd signed a multi-year offer sheet with the Dallas Mavericks. Since he is a restricted free agent, the Milwaukee Bucks can match.        
Zhizhi Wang signed a multi-year offer sheet with the Los Angeles Clippers. Since he is a restricted free agent, the Dallas Mavericks can match.
        
        
        
#--------------------------------------------------------------------------------------------------------------------------#
def create_df():
    '''
    '''
    x['player'] = None
    x['team'] = None
    
    for k,v in transactions.items():
        x.loc[x['transaction'].str.contains(k), ['player','team']] = \
            x[x['transaction'].str.contains(k)]['transaction'].str.extract(v)
        
        
    x.loc[x['date'].str.contains('Draft|Trade'), 'date'] = \
        x[x['date'].str.contains('Draft|Trade')]['date'].apply(lambda x: x.split(' - ')[0])
    
    x['date'] = pd.to_datetime(x['date'])
    
    x.sort_values(by=['player','date'],inplace=True)
    return x

x = create_df()
#--------------------------------------------------------------------------------------------------------------------------#
def get_player_links():
    alphabet = list(string.ascii_lowercase)
    
    links = []
    for letter in alphabet:
        link = 'https://www.basketball-reference.com/players/' + letter
        links.append(link)
    '''
    create a dataframe where we have all the players, their bball reference links,
    and their bball reference codename
    '''
    final_players_df = pd.DataFrame()
    for link in tqdm(links):
        try:
            response = requests.get(link)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            players_df = pd.DataFrame()
            for a in soup.find_all('a'):
                if link[-9:] in a['href']:
                    player = a.text
                    
                    player_code = a['href']
                    player_code = player_code.split('/')[-1].split('.')[0]
                    
                    player_link = 'https://www.basketball-reference.com' + a['href']
                    
                    df = {'player':[player], 'player_code':[player_code], 'link':[player_link]}       
                    df = pd.DataFrame(data=df)
                    players_df = players_df.append(df)
            
            players_df.drop_duplicates('player_code',inplace=True)
            players_df.reset_index(drop=True, inplace=True)
            final_players_df = final_players_df.append(players_df)
        except:
            continue
        #pause
        num = random.randint(4,7)
        time.sleep(num)
        
    return final_players_df
#-----------------------------------------------------------------------------------------------------------#
df_copy = df.copy()
salaries = df_salaries.copy()

check = df_copy[df_copy['player'].str.contains('Larry')]


df_copy['player'] = df_copy['player'].str.replace('\.|-','').str.replace('ć|č','c').str.replace('ņ','n').str.replace('ģ','g')\
                                     .str.replace('ū','u')
salaries['players'] = salaries['players'].str.replace('\.|-','')                         
                                     
x = pd.merge(salaries, df_copy, left_on='players',right_on='player', how='left')

#-----------------------------------------------------------------------------------------------------------#
def get_all():
    df = get_player_links()
    
    df = shuffle(df)
    
    lost_players = []
    
    df_salary_data = pd.DataFrame()
    df_regular_data = pd.DataFrame()
    df_playoff_data = pd.DataFrame()
    
    pbar = tqdm(df['link'])
    
    for link in pbar:
        response = requests.get(link)
        try: 
            soup_master = BeautifulSoup(response.text, 'html.parser')
            player_name = soup_master.find('title').text.split(' Stats')[0]
            code_name = link.split('/')[-1].split('.html')[0]
            
            df_salary = get_player_salary()
            df_salary_data = df_salary_data.append(df_salary)
            
            df_regular = get_regular_player_data()
            df_regular_data = df_regular_data.append(df_regular)
            
            df_playoff = get_playoff_player_data()
            df_playoff_data = df_playoff_data.append(df_playoff)
            
        except: 
            lost_players.append(code_name)
        
        #pbar.set_description("Processing %s" % link)
        
        #pause
        num = random.randint(5,10)
        time.sleep(num)
        
    return df_salary_data, df_regular_data, df_playoff_data

df_salary_data, df_regular_data, df_playoff_data = get_all()

df_regular_data['player_code'].nunique()
#-----------------------------------------------------------------------------------------------------------#    
def get_player_salary():              
    div = soup_master.find('div', {'id':'all_all_salaries'})
    try:  #if the div isn't empty
        comment = div.find_all(text=lambda text:isinstance(text, Comment))
        soup = BeautifulSoup(str(comment)[1:-1], 'html.parser')
        
        team = []
        for td in soup.find_all('td'):
            if td['data-stat'] == 'team_name':
                team.append(td.text)
        
        salary = []
        for td in soup.find_all('td'):
            if td['data-stat'] == 'salary':
                salary.append(td.text)
        
        season = []
        for th in soup.find_all('th'):
            if (th['data-stat'] == 'season') & (th['scope'] == 'row'):
                season.append(th.text)
                

    except AttributeError:
        team = ['no salary information']
        salary = ['no salary information']
        season = ['no salary information']
    
    df = {'team':team, 'season':season, 'salary':salary}
    df = pd.DataFrame(df)
    df['player'] = player_name
    df['player_code'] = code_name
    df = df[['player', 'player_code', 'season', 'team', 'salary']]
      
    return df
#-----------------------------------------------------------------------------------------------------------#
''' Get Player Statistics '''
#-----------------------------------------------------------------------------------------------------------#
def get_regular_player_data():
    
    columns = ['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS','MP','FG','FGA',
               'FG%','3P','3PA','3P%','2P','2PA','2P%','eFG%','FT','FTA',	
               'FT%','ORB','DRB','TRB','AST','STL','BLK','TOV','PF','PTS']
    
    div = soup_master.find('div', {'id':'all_totals'}) #get div containing comment section
    soup = BeautifulSoup(str(div), 'html.parser')
    comments = soup.find(text=lambda text:isinstance(text, Comment))
    soup = BeautifulSoup(str(comments), 'html.parser')
    tables = soup.find_all('table', attrs={'class':'row_summable sortable stats_table'})
       
    regular_data = []
    for table in tables:
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        for row in rows:
            cols_1 = row.find_all('th')
            cols_2 = row.find_all('td')
            cols = cols_1 + cols_2
            cols = [ele.text.strip() for ele in cols]
            cols = [player_name] + [code_name] + cols
            regular_data.append(cols)
    #---------------------------------------------------------------------------------------#
    tables = soup.find_all('thead')
    
    column_headers = []
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('th', {'scope':'col'})
            cols = [ele.text.strip() for ele in cols]
            column_headers.append(cols)
    
    column_headers = ['player_name', 'player_code'] + column_headers[0]
    
    regular_data = pd.DataFrame(regular_data, columns=column_headers)

    for column in columns:
        if column not in regular_data.columns:
            regular_data[column] = np.NaN
            
    regular_data = regular_data[columns]
    
    return regular_data
#-----------------------------------------------------------------------------------------------------------#        
def get_playoff_player_data():
    columns = ['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS','MP','FG','FGA',
               'FG%','3P','3PA','3P%','2P','2PA','2P%','eFG%','FT','FTA',	
               'FT%','ORB','DRB','TRB','AST','STL','BLK','TOV','PF','PTS']
    
    div = soup_master.find('div', {'id':'all_playoffs_totals'}) #get div containing comment section
    soup = BeautifulSoup(str(div), 'html.parser')
    comments = soup.find(text=lambda text:isinstance(text, Comment))
    soup = BeautifulSoup(str(comments), 'html.parser')
    tables = soup.find_all('table', attrs={'class':'row_summable sortable stats_table'})
    
    playoff_data = []
    for table in tables:
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        for row in rows:
            cols_1 = row.find_all('th')
            cols_2 = row.find_all('td')
            cols = cols_1 + cols_2
            cols = [ele.text.strip() for ele in cols]
            cols = [player_name] + [code_name] + cols
            playoff_data.append(cols)
    #---------------------------------------------------------------------------------------#  
    tables = soup.find_all('thead')      
    
    column_headers = []
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('th', {'scope':'col'})
            cols = [ele.text.strip() for ele in cols]
            column_headers.append(cols)
    
    column_headers = ['player_name', 'player_code'] + column_headers[0]
    
    playoff_data = pd.DataFrame(playoff_data, columns=column_headers)

    for column in columns:
        if column not in playoff_data.columns:
            playoff_data[column] = np.NaN
            
    playoff_data = playoff_data[columns]
    
    return playoff_data            
#-----------------------------------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------------------------------#
            

df_regular_data.to_csv('df_regular_season_player.csv',index=False)
df_playoff_data.to_csv('df_playoff_player.csv',index=False)
df_salary_data.to_csv('df_salary_player.csv',index=False)


df_salary = pd.read_csv('df_salary_player.csv')

test = pd.merge(df_salary, x, on=['player','team','season'],how='inner')

df_salary['season'] = df_salary['season'].apply(lambda x: x.split('-')[0])

df_salar


#-----------------------------------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------------------------------#
''' Graveyard Code '''
#-----------------------------------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------------------------------#
            
            
#-----------------------------------------------------------------------------------------------------------#
def get_regular_player_data():
    
    div = soup_master.find('div', {'id':'all_totals'}) #get div containing comment section
    soup = BeautifulSoup(str(div), 'html.parser')
    comments = soup.find(text=lambda text:isinstance(text, Comment))
    soup = BeautifulSoup(str(comments), 'html.parser')
    tables = soup.find_all('table', attrs={'class':'row_summable sortable stats_table'})
    
    regular_data = []
    for table in tables:
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        for row in rows:
            cols_1 = row.find_all('th')
            cols_2 = row.find_all('td')
            cols = cols_1 + cols_2
            cols = [ele.text.strip() for ele in cols]
            cols = [player_name] + [code_name] + cols
            regular_data.append(cols)
            
    try:            
        regular_data = pd.DataFrame(regular_data,
            columns = ['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS','MP','FG','FGA',
                       'FG%','3P','3PA','3P%','2P','2PA','2P%','eFG%','FT','FTA',	
                       'FT%','ORB','DRB','TRB','AST','STL','BLK','TOV','PF','PTS'])    
     
    except AssertionError:
        try:
            regular_data = pd.DataFrame(regular_data,
                columns = ['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS',
                           'MP','FG','FGA','FG%','FT','FTA','FT%','ORB','DRB','TRB','AST','STL',
                           'BLK','TOV','PF','PTS'])
        
        
            regular_data['2P'] = regular_data['FG']
            regular_data['2PA'] = regular_data['FGA']
            regular_data['2P%'] = regular_data['FG%']
            regular_data['3P'] = np.NaN
            regular_data['3PA'] = np.NaN
            regular_data['3P%'] = np.NaN
            regular_data['eFG%'] = np.NaN
    
        except AssertionError:
            try:
                regular_data = pd.DataFrame(regular_data,
                    columns = ['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS',
                               'MP','FG','FGA','FG%','FT','FTA','FT%','TRB','AST','PF','PTS'])
             
            except AssertionError:
                try:
                    regular_data = pd.DataFrame(regular_data,
                        columns = ['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS','MP','FG','FGA',
                                   'FG%','3P','3PA','3P%','2P','2PA','2P%','eFG%','FT','FTA',	
                                   'FT%','ORB','DRB','TRB','AST','TOV','PF','PTS'])  
                    regular_data['BLK'] = np.NaN
                    regular_data['STL'] = np.NaN
                    
                except AssertionError:
                    regular_data = pd.DataFrame(regular_data,
                    columns = ['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS',
                               'MP','FG','FGA','FG%','FT','FTA','FT%','ORB','DRB','TRB','AST','STL',
                               'BLK','PF','PTS'])
                
                    regular_data['TOV'] = np.NaN
                    regular_data['2P'] = regular_data['FG']
                    regular_data['2PA'] = regular_data['FGA']
                    regular_data['2P%'] = regular_data['FG%']
                    regular_data['3P'] = np.NaN
                    regular_data['3PA'] = np.NaN
                    regular_data['3P%'] = np.NaN
                    regular_data['eFG%'] = np.NaN
#-----------------------------------------------------------------------------------------------------------#
columns = ['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS','MP','FG','FGA',
           'FG%','3P','3PA','3P%','2P','2PA','2P%','eFG%','FT','FTA',	
           'FT%','ORB','DRB','TRB','AST','STL','BLK','TOV','PF','PTS']


for column in columns:
     if column not in regular_data:
        regular_data[column] = np.NaN
        
        

regular_data = [regular_data[column] = np.NaN if column not in regular_data.columns for column in columns]
                    
    
    regular_data = regular_data[['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS','MP',
                                 'FG','FGA','FG%','3P','3PA','3P%','2P','2PA','2P%','eFG%','FT','FTA',	
                                 'FT%','ORB','DRB','TRB','AST','STL','BLK','TOV','PF','PTS']]


    return regular_data
#-----------------------------------------------------------------------------------------------------------#   
def get_playoff_player_data():
    
    div = soup_master.find('div', {'id':'all_playoffs_totals'}) #get div containing comment section
    soup = BeautifulSoup(str(div), 'html.parser')
    comments = soup.find(text=lambda text:isinstance(text, Comment))
    soup = BeautifulSoup(str(comments), 'html.parser')
    tables = soup.find_all('table', attrs={'class':'row_summable sortable stats_table'})
    
    playoff_data = []
    for table in tables:
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        for row in rows:
            cols_1 = row.find_all('th')
            cols_2 = row.find_all('td')
            cols = cols_1 + cols_2
            cols = [ele.text.strip() for ele in cols]
            cols = [player_name] + [code_name] + cols
            playoff_data.append(cols)
            
    try:            
        playoff_data = pd.DataFrame(playoff_data,
            columns = ['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS','MP','FG','FGA',
                       'FG%','3P','3PA','3P%','2P','2PA','2P%','eFG%','FT','FTA',	
                       'FT%','ORB','DRB','TRB','AST','STL','BLK','TOV','PF','PTS'])    
    except AssertionError:
        try:
            playoff_data = pd.DataFrame(playoff_data,
                columns = ['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS',
                           'MP','FG','FGA','FG%','FT','FTA','FT%','ORB','DRB','TRB','AST','STL',
                           'BLK','TOV','PF','PTS'])
            playoff_data['2P'] = playoff_data['FG']
            playoff_data['2PA'] = playoff_data['FGA']
            playoff_data['2P%'] = playoff_data['FG%']
            playoff_data['3P'] = np.NaN
            playoff_data['3PA'] = np.NaN
            playoff_data['3P%'] = np.NaN
            playoff_data['eFG%'] = np.NaN

        except AssertionError:
            try:
                playoff_data = pd.DataFrame(playoff_data,
                    columns = ['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS',
                               'MP','FG','FGA','FG%','FT','FTA','FT%','TRB','AST','PF','PTS'])
                playoff_data['ORB'] = np.NaN
                playoff_data['DRB'] = np.NaN
                playoff_data['STL'] = np.NaN
                playoff_data['BLK'] = np.NaN
                playoff_data['TOV'] = np.NaN
                playoff_data['2P'] = playoff_data['FG']
                playoff_data['2PA'] = playoff_data['FGA']
                playoff_data['2P%'] = playoff_data['FG%']
                playoff_data['3P'] = np.NaN
                playoff_data['3PA'] = np.NaN
                playoff_data['3P%'] = np.NaN
                playoff_data['eFG%'] = np.NaN      
                
            except AssertionError:
                try:
                    playoff_data = pd.DataFrame(playoff_data,
                        columns = ['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS','MP','FG','FGA',
                                   'FG%','3P','3PA','3P%','2P','2PA','2P%','eFG%','FT','FTA',	
                                   'FT%','ORB','DRB','TRB','AST','TOV','PF','PTS'])  
                    playoff_data['BLK'] = np.NaN
                    playoff_data['STL'] = np.NaN
                    
                except AssertionError:
                    playoff_data = pd.DataFrame(playoff_data,
                    columns = ['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS',
                               'MP','FG','FGA','FG%','FT','FTA','FT%','ORB','DRB','TRB','AST','STL',
                               'BLK','PF','PTS'])
                
                    playoff_data['TOV'] = np.NaN
                    playoff_data['2P'] = playoff_data['FG']
                    playoff_data['2PA'] = playoff_data['FGA']
                    playoff_data['2P%'] = playoff_data['FG%']
                    playoff_data['3P'] = np.NaN
                    playoff_data['3PA'] = np.NaN
                    playoff_data['3P%'] = np.NaN
                    playoff_data['eFG%'] = np.NaN
    
    playoff_data = playoff_data[['player_name','player_code','Season','Age','Tm','Lg','Pos','G','GS','MP',
                                 'FG','FGA','FG%','3P','3PA','3P%','2P','2PA','2P%','eFG%','FT','FTA',	
                                 'FT%','ORB','DRB','TRB','AST','STL','BLK','TOV','PF','PTS']] 
    return playoff_data
    #-----------------------------------------------------------------------------------------------------------#        

#--------------------------------------------------------------------------------------------------------------------------#
def get_salaries():
    seasons = ['1990-1991','1991-1992','1992-1993','1993-1994','1994-1995','1995-1996','1996-1997','1997-1998',
               '1998-1999','1999-2000','2000-2001','2001-2002','2002-2003','2004-2005','2005-2006','2006-2007',
               '2007-2008','2009-2010','2010-2011','2011-2012','2012-2013','2013-2014','2014-2015','2015-2016',
               '2016-2017','2017-2018','2018-2019']
    
    random.shuffle(seasons)
    
    seasons = ['2019-20']
    df_salaries = pd.DataFrame()
    for season in seasons:
        base_link = 'https://hoopshype.com/salaries/players/'
        link = base_link + season + '/'
        print(link)
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        players = []
        salary = []
        div = soup.find('div',{'class':"hh-salaries-ranking"})
        for td in div.find_all('td',{'class':'name'}):
            player = td.text.strip()
            players.append(player)
        salaries = []
        for td in div.find_all('td',{'class':'hh-salaries-sorted'}):
            salary = td.text.strip()
            salaries.append(salary)
        
        df_salaries = pd.DataFrame({'players':players[1:],
                                   'salary':salaries[1:]})
        
        #salaries = np.array(salaries)
        #salaries = salaries.reshape(int(len(salaries)/2), 2)
        #salaries = pd.DataFrame(salaries, columns=['salary','salary_inflated'])
        #salaries['player'] = players[1:]
        #salaries['season'] = soup.find('title').text[:9]
        #salaries = salaries[['season','player','salary','salary_inflated']]
        #df_salaries = df_salaries.append(salaries)
        #pause
        num = random.randint(7,12)
        time.sleep(num)
    return df_salaries
#--------------------------------------------------------------------------------------------------------------------------#
df_salaries = get_salaries()
y = df_salaries.copy()
#--------------------------------------------------------------------------------------------------------------------------#
y.loc[y['season'].str.contains('1999'), 'season'] = '2000'
y.loc[y['season'].str.contains('2000/01'), 'season'] = '2001'

z = pd.merge(x, y, on=['player','season'], how='left')
        
        
        
#-----------------------------------------------------------------------------------------------------------#     
seasons = ['1990-1991','1991-1992','1992-1993','1993-1994','1994-1995','1995-1996','1996-1997','1997-1998',
           '1998-1999','1999-2000','2000-2001','2001-2002','2002-2003','2004-2005','2005-2006','2006-2007',
           '2007-2008','2009-2010','2010-2011','2011-2012','2012-2013','2013-2014','2014-2015','2015-2016',
           '2016-2017','2017-2018','2018-2019']

random.shuffle(seasons)

df_salaries = pd.DataFrame()
for season in seasons:
    base_link = 'https://hoopshype.com/salaries/players/'
    link = base_link + season + '/'
    print(link)
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')
    players = []
    salary = []
    div = soup.find('div',{'class':"hh-salaries-ranking"})
    for td in div.find_all('td',{'class':'name'}):
        player = td.text.strip()
        players.append(player)
    salaries = []
    for td in div.find_all('td',{'style':'color:black'}):
        salary = td.text.strip()
        salaries.append(salary)
    
    salaries = np.array(salaries)
    salaries = salaries.reshape(int(len(salaries)/2), 2)
    salaries = pd.DataFrame(salaries, columns=['salary','salary_inflated'])
    salaries['player'] = players[1:]
    salaries['season'] = soup.find('title').text[:9]
    salaries = salaries[['season','player','salary','salary_inflated']]
    df_salaries = df_salaries.append(salaries)
#-----------------------------------------------------------------------------------------------------------#







                        
                    if td['data-stat'] == 'salary':
                        salary.append(td.text)
    
            
        soup = BeautifulSoup(response.text , 'html.parser')
        
        soup = BeautifulSoup(str(test), 'html.parser')
        comments = soup.find_all(text=lambda text:isinstance(text, Comment))
        
        for comment in comments:
            if 'salary' in comment:
                print(comment)
        
        for comment in comments:
            for tr in comment.find('tr'):
                print(tr)
        
        tr = comment.find('tr')
        
        commentsoup = BeautifulSoup(comment , 'html.parser')
        
            for comment in comments:
                for tr in commentsoup.find_all('tr'):
                    print(tr)
                    
            print(div)
            for td in div.find_all('td'):
                print(td)            
            
            
            
            
        test = ''.join(test)
        
        
        
            
            if td['data-stat'] == 'salary':
                print(td)
                
                
            for tr in div.find_all('tr '):
                print(tr)
        
        ("div", {"id": "all_all_salaries"})
    
                
    




t = x[x['transaction'].str.contains('Redd')]


player_actions.items()

for k, v in player_actions.items():
    dataframe[matching_column] = \
                np.where(dataframe[column].str.contains(k), v, dataframe[matching_column])
    


matching_value = 'signed a contract']

for x in player_actions:
    print(x)

    matching_value = ('placed&on waivers', 'placed on waivers')
    
    len(matching_value) > 2
    
len(player_actions[6]) > 1

'placed the contract of Michael Cage on waivers.'

get_match(x, 'transaction', 'player_action', **player_actions)
    
    
z['transaction_type'] = \
    np.where(z['transaction'].str.lower().str.contains('waiver'), 'placed on waivers',
    np.where(z['transaction'].str.lower().str.contains('signed a contract'), 'signed a contract',
    np.where(z['transaction'].str.lower().str.contains('signed a multi-year contract'), 'signed a multi-year contract', 
    np.where(z['transaction'].str.lower().str.contains('signed a veteran extension'), 'signed a veteran extension', 
    np.where(z['transaction'].str.lower().str.contains('signed a rookie scale extension'), 'signed a rookie scale extension',
    np.where(z['transaction'].str.lower().str.contains('terminated the 10 day contract'), 'terminated the 10 day contract',
    np.where(z['transaction'].str.lower().str.contains('exercised a player option'), 'exercised a player option',
    np.where(z['transaction'].str.lower().str.contains('exercised their team option'), 'exercised their team option',
    np.where(z['transaction'].str.lower().str.contains('renounced their free-agent exception rights'), 'renounced their free-agent exception rights',
    np.where(z['transaction'].str.lower().str.contains('tendered a qualifying offer'), 'tendered a qualifying offer',
    np.where(z['transaction'].str.lower().str.contains('signed a two-way contract'), 'signed a two-way contract',
    np.where(z['transaction'].str.lower().str.contains('ended the two-way contract'), 'ended a two-way contract',    
    np.where(z['transaction'].str.lower().str.contains('assigned'), 'assigned to G league',
    np.where(z['transaction'].str.lower().str.contains('recalled'), 'recalled from G league',
    np.where(z['transaction'].str.lower().str.contains('free agent'), 'became a free agent',
    np.where(z['transaction'].str.lower().str.contains('unrestricted fa'), 'became an unrestricted free agent',
    np.where(z['transaction'].str.lower().str.contains('utilized the amnesty provision'), 'amnestied',
    np.where(z['transaction'].str.lower().str.contains('exchange for'), 'traded',
    np.where(z['transaction'].str.lower().str.contains('matched the offer sheet'),'offer sheet matched',
    np.where(z['transaction'].str.lower().str.contains('exercised an early termination option'),'exercised an early termination option',
    np.where(z['transaction'].str.lower().str.contains('voided his ability to terminate his contract early'),'voided ability to terminate his contract early',
             np.nan)))))))))))))))))))))










test = z[z['transaction_type']=='nan']


    action_list = ['on waivers', 'signed a contract']
z['transaction_type_2'] = np.where(z['transaction'].str.lower().str.contains('waiver'), 'placed on waivers', z['transaction_type_2'])

x = []
for string in z['transaction']:
    for action in action_list:
        if action in string:
            x.append(action)
        else:
            x.append('')
            
lst = [j + k for j in s1 for k in s2]
[(j, k) for j in s1 for k in s2]

for j in s1:
  for k in s2:
    print(j, k)






action_list = ['on waivers', 'signed a contract']

z['transaction_type_2'] = [x if x in z['transaction'] else '' for x in action_list]

z['transaction_type_2'] = [action for string in z['transaction'] if action in string for action in action_list]

x = [action for action in action_list for string in z['transaction'] if action in string]

test.dropna(axis=1,how='all',inplace=True)

test.melt()

df.set_index(["location", "name"])
         .stack()
         .reset_index(name='Value')





x = z.str.split('\n', expand=True)


x = z[3]

z.loc[3, 'text'].split('\n\n')

text[3].split(lambda x: '\n\n')
    
    ''.join(li.split)
        
        z = text.copy()
        z['text'] = z['text'].str.split('\n')[0]

z = pd.DataFrame(columns=['text'], data=z)
        
z['oink'] = z[z['text'].apply(lambda x: bool(re.match('^(\s)\w{3}\s\d{2},\s\d{4}', x)))]
        

        if '/player' in a['href']:
            print(a.text)
    
    for a in soup.find_all('a'):
        if '/player' in a['href']:
            print(a.text)
            
            
            print(a.text)
    
    for y in soup.find_all('td',{'class':'center '}):
        for a in y.find_all('a'):
            links.append(a['href']) 
            
            
            