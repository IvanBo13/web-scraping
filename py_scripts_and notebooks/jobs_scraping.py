from fake_useragent import UserAgent
import requests
import random
from bs4 import BeautifulSoup

def get_proxies():
    """Reads proxy addresses from proxies.txt and returns them as a list."""
    with open('proxies.txt', 'r') as f:
        proxies = list(map(str.strip, f.readlines()))
    if len(proxies) == 0:
        print('There is no proxies in proxies.txt')
        return None 
    return proxies

proxies_list = get_proxies()


def get_random_proxy():
    """Returns a random proxy from the proxies list."""
    return random.choice(proxies_list)

def get_random_user_agent():
    """Returns a random user agent string."""
    ua = UserAgent()
    return ua.random

def make_request(url:str):
    """Makes an HTTP GET request to the specified URL using random proxies and user agents.
    Retries up to 10 times if the request fails."""
    for i in range(10):
        response = requests.get(url=url,
                                proxies={
                                    'http':get_random_proxy(),
                                    'https':get_random_proxy()
                                },
                                headers={'User-Agent': get_random_user_agent()})
        if response.status_code == 200:
            break
    else:
        print(f"status code {response.status_code}: {response.url}")
    return response

def identify_analyst_job(job_title:str):
    """Identifies if the job title corresponds to a data analyst position."""
    sub_strings = ['anal', 'sql', 'bi', "excel" ]
    # if there are some words from sub_strings in job_title, then it's Data Analyst job
    for sub in sub_strings:
        if sub in job_title.lower():
            return True
    else:
        return False
    
def identify_position(job_title:str):
    """Identifies the job position (e.g., Junior, Senior) from the job title."""
    d = dict(
        junior = ['junior', 'entry'],
        intern = ['intern', 'staż', 'train'],
        middle = ['assosiate', 'mid', 'intermediate'],
        senior = ['senior', 'executive', 'starszy', 'lead']
    )
    for key in d:
        for position in d[key]:
            if position in job_title.lower():
                return key
    else:
        return None
    

def identify_polish_description(desc_text:str):
    """Identifies if the job description contains Polish letters."""
    polish_letters = "żśćźóąęłń"
    for letter in polish_letters: # if there are some polish letters, then description is written in Polish
        if letter in desc_text.lower():
            return True
    else:
        return False
    

def identify_polish(desc_html:str):
    """Identifies if the job requires Polish language skills."""
    # bullet points in job postings are often represented as either <li> or <p> tags
    soup = BeautifulSoup(desc_html, 'html.parser')
    bullet_points = soup.find_all('li') # find all <li> tags 
    is_english_required = False
    is_polish_description = identify_polish_description(soup.text)
    if len(bullet_points) == 0: # if there are no <li> tags, then find all <p> tags
        bullet_points = soup.find_all('p')
        if len(bullet_points) == 0: # if there are no <p> tags (hence no bullet points at all) then return None
            return None
    for bullet in bullet_points:
        bullet = bullet.text
        if 'Polish' in bullet  \
            or 'język polski' in bullet.lower() or 'polskiego' in bullet.lower():
            return True
        if "English" in bullet or "angielski" in bullet.lower():
            is_english_required = True
    else:
        # If the description is written in Polish and English is not mentioned, it implies that Polish is required.
        if is_polish_description and not is_english_required:
            return True
        else:
            return False