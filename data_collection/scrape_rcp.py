import requests as req
import subprocess
import sys

from bs4 import BeautifulSoup

from data_processing.definitions import *

try:
    url = sys.argv[1]
    output_dir = sys.argv[2]
except IndexError:
    print('Usage: python scrape_rcp.py <url> <output directory>')
    print('Suggestions:')
    print('\t- https://www.realclearpolitics.com/epolls/2018/house/2018_elections_house_map.html')
    print('\t- https://www.realclearpolitics.com/epolls/2018/senate/2018_elections_senate_map.html')
    sys.exit()

page = req.get(url)

soup = BeautifulSoup(page.text, features="html.parser")

status_dict = {
    'dem2': 'likely_dem',
    'dem3': 'leans_dem',
    'tu': 'toss_up',
    'gop3': 'leans_gop',
    'gop2': 'likely_gop'
}
statuses = {}

for div in soup.find_all('div'):
    div_class = div.get('class')
    if div_class:
        if ' '.join(div_class).startswith('states-in-play'):
            links = div.find_all('a')
            hrefs = {link.text: link.get('href')
                     for link in links[1:]
                     if link.text and not link.text.startswith('Safe')}
            codes = {k.strip(')').split(')')[-1].split(' (')[0].split(':')[0] for k in hrefs.keys()}
            statuses[status_dict[div_class[2]]] = codes

print(statuses)
os.chdir(f"{ROOT_DIR}/{output_dir}")
for code, href in hrefs.items(): 
    filename = code.replace(' ', '_')
    for char in ['(', ')', ':']:
        filename = filename.replace(char,'')
    filename += '.csv'
    if href.startswith('http'):
        link = href
    else:
        link = f'https://www.realclearpolitics.com{href}'

    try:
        subprocess.check_output(['rcp', link, "--output", f"{ROOT_DIR}/{output_dir}/{filename}"])
    except:
        page = req.get(url)

        soup = BeautifulSoup(page.text, features="html.parser")
        print(filename)
        continue

