import pandas as pd
import requests as req
from bs4 import BeautifulSoup


states = pd.read_csv('data/state_info/state_codes.csv')

# Print header
print('code,party,turnout')

for state, code in zip(states['name'],states['postal_code']):
    name = state.replace(' ', '-').lower()
    url = f'https://www.politico.com/election-results/2018/{name}/house/' 
    page = req.get(url)
    soup = BeautifulSoup(page.text, features="html.parser")


    results = []
    for div in soup.find_all('div'):
        div_class = div.get('class')
        if div_class and div_class[0] == 'col-md-6':
            results.append(div)

    d = 1
    for table in results:
        row = ''

        i = 0
        for div in table.find_all('div'):
            div_class = div.get('class')
            if div_class and div_class[0] == 'uncontested':
                print(f'{code}{str(d)},,')
                d += 1
        for td in table.find_all('td'):
            td_class = td.get('class') 
            if td_class and td_class[0] == 'party':
                row = f'{code}{str(d)},{td.text},'
            if td_class and td_class[0] == 'vote-count':
                count = td.text.replace(',','')
                row += f'{count}'
                print(row)
                i += 1
                if i % 2 == 0:
                    d += 1
                    break
