import pandas as pd
import requests
from bs4 import BeautifulSoup



url = 'https://basketball.realgm.com/nba/transactions'

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

df_year = pd.DataFrame()
for grouped_transaction in soup.find_all('div', {'class' : 'portal widget fullpage'}):
    df_day = {'date': '', 'transactions': []}
    for date in grouped_transaction.find_all('h3'):
        df_day['date'] = date.text
        for transaction in grouped_transaction.find_all('li'):
            df_day['transactions'].append(transaction.text)
    df_day = pd.DataFrame.from_dict(df_day)
    df_year = df_year.append(df_day)
    
    