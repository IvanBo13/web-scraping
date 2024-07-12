import os
import time
import random
from bs4 import BeautifulSoup
import datetime

import requests
import jobs_scraping
import job_database as db
import pandas_csv


# Configure socket options for HTTP connections to keep them alive longer
import socket
from urllib3.connection import HTTPConnection

HTTPConnection.default_socket_options = (
    HTTPConnection.default_socket_options + [
        (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
        (socket.SOL_TCP, socket.TCP_KEEPIDLE, 45),
        (socket.SOL_TCP, socket.TCP_KEEPINTVL, 10),
        (socket.SOL_TCP, socket.TCP_KEEPCNT, 6)
    ]
)

# Dictionary to store job information
# from jobs_info dictionary DataFrame will be created
jobs_info = {
        'job_id': [],
        'job_title': [],
        'company_name': [],
        'location': [],
        'published_date': [],
        'scraped_date': [],
        'is_polish_required':  [],
        'position': [],
        'source' : [],
        'description': []
    }



def get_current_date():
    """Returns the current date as a string."""
    return str(datetime.date.today())

def make_request(url:str):
    """Makes an HTTP GET request to the specified URL using random proxies and user agents.
    Retries up to 10 times if the request fails."""
    # headers are important here to avoid getting blocked
    for i in range(10):
        response = requests.get(url=url, 
                                proxies={'http':jobs_scraping.get_random_proxy()},
                                headers={
                                    'User-Agent': jobs_scraping.get_random_user_agent(),
                                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                                    'Accept-Language': 'pl-PL,pl;q=0.9',
                                    'Referer': 'https://www.google.com/',
                                    'Connection': 'keep-alive',
                                    'Upgrade-Insecure-Requests': '1',
                                    'DNT': '1',
                                    #'Host': 'www.indeed.com',
                                    'Cache-Control': 'max-age=0',
                                    'Pragma': 'no-cache'})
        if response.status_code == 200:
            break
    else:
        print(f"status code {response.status_code}: {response.url}")
    return response

def parse_interval(interval:str):
    """Parses the interval string to calculate the job's published date."""
    if interval in ('Dzisiaj', 'Dodano przed chwilą'):
        return datetime.timedelta(days=0)
    elif interval == 'wczoraj':
        return datetime.timedelta(days=1)
    else:
        #getting number from interval string
        number_from_interval = int(''.join(list(filter(str.isdigit, interval))))
        return datetime.timedelta(days=number_from_interval)
    
def get_prev_dir(dir:str):
    '''Returns previous directory path relatively to dir path'''
    prev_dir = dir[:dir.rfind("\\")+1]
    return prev_dir

def load_last_scraping_date():
    """
    Loads the date of the last scraping from a file.
    If file doesn't exist, return None
    """
    try:
        with open(get_prev_dir(os.getcwd()) + "scraping_dates\\" + 'indeed_last_scraping_date.txt', 'r') as f:
            d = str(f.readline()).strip()
        return d
    except FileNotFoundError:
        return None


time_periods = {
    'past_week' : '7',
    'past_two_weeks' : '14',
    'past_three_days' : '3',
    'past_24_hours' : '1'
}

def choose_time_period():
    """Chooses the scraping time period based on the last scraping date."""
    last_date_str = load_last_scraping_date()
    if not last_date_str : # if there is no last scraping date, then scrape jobs for any time
        return None
    cur_date_str = get_current_date()

    cur_date = datetime.date(*[int(s) for s in cur_date_str.split('-')])
    last_date = datetime.date(*[int(s) for s in last_date_str.split('-')])

    one_day = datetime.timedelta(days=1)
    three_days = datetime.timedelta(days=3)
    one_week = datetime.timedelta(days=7)
    two_weeks = datetime.timedelta(days=14)

    delta = cur_date - last_date
    if delta <= one_day:
        return 'past_24_hours'
    elif delta <= three_days:
        return 'past_three_days'
    elif delta <= one_week:
        return 'past_week'
    elif delta <= two_weeks: 
        return 'past_two_weeks'
    else:
        return None
    

start = 0
def get_next_list(time_period):
    """Generates the URL for the next page of job listings and makes a request to retrieve it."""
    global time_periods
    global start
    if not time_period: # If time_period is None or an empty string, jobs in the list will be from any time.
        list_url = f"https://pl.indeed.com/jobs?q=data+analyst&l=Polska&start={str(start)}"
    else: # jobs in the list will be filtered by the passed time_period.
        list_url = f"https://pl.indeed.com/jobs?q=data+analyst&l=Polska&start={str(start)}&fromage={time_periods[time_period]}"
    response = make_request(list_url)
    start += 10
    return None if response.status_code != 200 else response.text

def get_job_description_request(job_id):
    """Generates the URL for the job description and makes a request to retrieve it."""
    descr_url = f"https://pl.indeed.com/viewjob?jk={job_id}&from=vjs&viewtype=embedded&spa=1&hidecmpheader=0"
    return make_request(descr_url)
    

    
    
def parse_json_description(descr_response):
    """Parses the job description JSON data and updates the jobs_info dictionary."""
    descr_json = descr_response.json()

    dict1 = descr_json['body']['hostQueryExecutionResult']['data']['jobData']['results'][0]['job']
        
    string_interval  = descr_json['body']['hiringInsightsModel']['age']
    delta = parse_interval(string_interval)
    cur_date_str = get_current_date()
    cur_date = datetime.date(*[int(s) for s in cur_date_str.split('-')])
    published_date = cur_date - delta

    description_html = dict1['description']['html']
    is_polish_required = jobs_scraping.identify_polish(description_html)
    position = jobs_scraping.identify_position(dict1['title'])

    # jobs info's lists must have the same lengths because the DataFrame object will be created from it
    # so if some data can't be retrieved, None value is appended to a jobs_info's list
    jobs_info['job_title'].append(dict1['title'][:100] if dict1['title'] else None)
    jobs_info['job_id'].append(dict1['key'])
    jobs_info['company_name'].append(dict1['sourceEmployerName'][:100] if dict1['sourceEmployerName'] else None)
    jobs_info['location'].append(dict1['location']['city'][:100] if dict1['location']['city'] else None)
    jobs_info['published_date'].append(published_date)
    jobs_info['scraped_date'].append(cur_date)
    jobs_info['position'].append(position[:30] if position else position)
    jobs_info['is_polish_required'].append(is_polish_required)
    jobs_info['description'].append(dict1['description']['text'].strip())
    jobs_info['source'].append('indeed')


def parse_jobs(list_soup : BeautifulSoup, scraped_ids:list):
    """Parses job listings and extracts job IDs."""
    jobs_ids = list(map(lambda tag: tag['data-jk'], list_soup.find_all('a', {'class': "jcs-JobTitle css-jspxzf eu4oa1w0"})))

    for job_id in jobs_ids:
        if job_id in scraped_ids: # if job_id is already in database, then skip it
            continue
        # get description json
        time.sleep(random.uniform(2, 7))
        descr_response = get_job_description_request(job_id)
        if descr_response.status_code != 200 or descr_response.json() == None:
            continue
        parse_json_description(descr_response)
        scraped_ids.append(job_id)
        
            


def main():
    """Main function to run the scraping process and save the data."""

    conn, cur = db.connect_to_db()
    db.create_table_if_not_exists(conn, cur)
    # get ids of already scraped jobs from a database to avoid duplicating data
    scraped_ids = db.select_job_ids(conn, cur, "indeed")
    cur.close()
    conn.close()

    time_period = choose_time_period()
        
    print("indeed scraping is started\n")
    for i in range(100):
        list_html = get_next_list(time_period)
        time.sleep(2)
        if not list_html:
            continue
        list_soup = BeautifulSoup(list_html, 'html.parser')
        parse_jobs(list_soup, scraped_ids)

    cur_date = get_current_date()
    # writing current date of scraping to a file
    with open(get_prev_dir(os.getcwd()) + r'\scraping_dates\indeed_last_scraping_date.txt', 'w') as f:
        f.write(cur_date) 
    print("indeed scraping is finished\n")
    pandas_csv.save_data(jobs_info) # transforms jobs_info to a DataFrame object, then save it as csv file


main()