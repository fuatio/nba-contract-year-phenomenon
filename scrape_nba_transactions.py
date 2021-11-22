import pandas as pd
import requests
from bs4 import BeautifulSoup



    
def get_transactions():
  ''' Get all the transactions from Real GM website '''
  
  # years = ['1984','1985','1986','1987','1988','1989',
  #          '1990','1991','1992','1993','1994','1995','1996','1997','1998','1999',
  #          '2000','2001','2002','2003','2004','2005','2006','2007','2008','2009',
  #          '2010','2011','2012','2013','2014','2015','2016','2017','2018','2019']
  years = ['2010','2011','2012','2013','2014','2015','2016','2017','2018','2019', '2020', '2021']
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


df = get_transactions()

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
        
check = x[x['player'] == 'Matt Barnes']
        
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
