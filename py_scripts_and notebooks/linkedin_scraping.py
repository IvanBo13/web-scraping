import time
import os
import random
from bs4 import BeautifulSoup
import datetime


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
        with open(get_prev_dir(os.getcwd()) + "scraping_dates\\" + 'linkedin_last_scraping_date.txt', 'r') as f:
            d = str(f.readline()).strip()
        return d
    except FileNotFoundError:
        return None
    
def choose_time_period():
    """Chooses the scraping time period based on the last scraping date."""
    last_date_str = load_last_scraping_date()
    if not last_date_str : # if there is no last scraping date, then scrape jobs for any time
        return 'any_time'
    
    cur_date_str = get_current_date()

    cur_date = datetime.date(*[int(s) for s in cur_date_str.split('-')])
    last_date = datetime.date(*[int(s) for s in last_date_str.split('-')])

    one_day = datetime.timedelta(days=1)
    one_week = datetime.timedelta(weeks=1)
    one_month = datetime.timedelta(days=30)

    delta = cur_date - last_date
    if delta <= one_day:
        return 'past_24_hours'
    elif delta <= one_week:
        return 'past_week'
    elif delta <= one_month: 
        return 'past_month'
    else:
        return 'any_time'



def get_next_list(time_period:str, num_lists:int):
    """Generates the URL for the next page of job listings and makes a request to retrieve it."""
    time_periods = {
        'past_month' : 'r2592000',
        'any_time' : '',
        'past_week' : 'r604800',
        'past_24_hours' : "r86400"
    }

    job_title, location = jobs_scraping.get_searching_parameters()
    splitted_job_title = job_title.split()
    splitted_location = location.split()
    if len(splitted_job_title) >= 2:
        job_title = '%20'.join(splitted_job_title)
    if len(splitted_location) >= 2:
        location = '%20'.join(splitted_location)

    for start in range(0, num_lists*10, 10):
        list_url = f'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={job_title}&f_TPR={time_periods[time_period]}&location={location}&start='
        current_url = list_url + str(start) # adding 10 to the "start" parameter of list url to get the next list of jobs
        response = jobs_scraping.make_request(current_url)
        # yield None if can't access a page, otherwise return text of the page
        yield None if response.status_code != 200 else response.text 

def get_job_id(job_url:str):
    """Extracts and returns the job ID from the job URL."""
    splitted = job_url.split('?')
    return splitted[0].split('-')[-1]

def get_job_description_request(job_id):
    """Generates the URL for the job description and makes a request to retrieve it."""
    descr_url = 'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/'
    return jobs_scraping.make_request(descr_url+job_id)

def scrape_description(descr_response):
    """Extracts the job description from the response."""
    descr_html = descr_response.text
    descr_soup = BeautifulSoup(descr_html, 'html.parser')
    description = descr_soup.find("div", {"class":"show-more-less-html__markup show-more-less-html__markup--clamp-after-5 relative overflow-hidden"}).text
    return description

def parse_location(location:str):
    """Parses the location string to get the voivodship."""
    splitted = location.split(',')
    if len(splitted) == 3:
        return splitted[1].strip()
    else:
        return location
    
    
def parse_jobs(list_soup : BeautifulSoup, scraped_ids:list, jobs_info:dict):
    """Parses job listings and extracts job details."""

    # jobs info's lists must have the same lengths because the DataFrame object will be created from it
    # so if some data can't be retrieved, None value is appended to a jobs_info's list
    job_cards = list_soup.find_all('div', {'class':"base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card"})
    cur_date = get_current_date()
    for card in job_cards:
        # get job_id
        card_url =  card.find('a', {'data-tracking-control-name' : 'public_jobs_jserp-result_search-card'})['href']
        job_id = get_job_id(card_url)
        if job_id in scraped_ids: # if this job_id is already in database, then skip it
            continue
        # get job_title
        try:
            job_title = card.find('span', {"class":"sr-only"}).get_text().strip()
        except AttributeError:
            job_title = None
        else:
            if not jobs_scraping.identify_analyst_job(job_title): # if this is not data job, skip it
                continue
        jobs_info['job_id'].append(job_id)
        
        position =  jobs_scraping.identify_position(job_title)
        jobs_info['position'].append(position)

        job_title = job_title[:99]
        jobs_info['job_title'].append(job_title)

        # get company_name
        try:
            company_name = card.find('a', {'data-tracking-control-name':"public_jobs_jserp-result_job-search-card-subtitle"}).get_text().strip()
        except AttributeError:
            company_name = None 
        company_name = company_name[:99]
        jobs_info['company_name'].append(company_name)

        # get location
        try:
            location = card.find('span', {'class':"job-search-card__location"}).get_text().strip()
        except AttributeError:
            location = None 
        parsed_location = parse_location(location)
        jobs_info['location'].append( parsed_location[:99])

        #get published_time
        try:
            published_date = card.find('time')['datetime'].strip()
        except AttributeError:
            published_date = None

        jobs_info['published_date'].append(published_date)
        jobs_info['scraped_date'].append(cur_date)

        # parse job descriptions

        # get description page
        time.sleep(random.uniform(0.5, 1.5))
        descr_response = get_job_description_request(job_id)
        if descr_response.status_code != 200: # if description can't be accessed, append None
            jobs_info['description'].append(None)
        else:
            jobs_info['is_polish_required'].append(jobs_scraping.identify_polish(descr_response.content))

            description = scrape_description(descr_response)
            jobs_info['description'].append(description.strip())
        
        jobs_info['source'].append('linkedin')
        scraped_ids.append(job_id)
        
        
def main():
    """Main function to run the scraping process and save the data."""
    
    conn, cur = db.connect_to_db()
    db.create_table_if_not_exists(conn, cur)
    # get ids of already scraped jobs from a database to avoid duplicating data
    scraped_ids = db.select_job_ids(conn, cur, 'linkedin')
    cur.close()
    conn.close()

    time_period = choose_time_period()
 
    lists_generator = get_next_list(time_period, 1) # creating  generator that yields lists of jobs
    print("linkedin scraping is started\n")
    for list_html in lists_generator:
        if not list_html:
            continue
        list_soup = BeautifulSoup(list_html, 'html.parser')
        parse_jobs(list_soup, scraped_ids, jobs_info)

    cur_date = get_current_date()
    # writing current date of scraping to a file
    with open(get_prev_dir(os.getcwd()) + "scraping_dates\\" + 'linkedin_last_scraping_date.txt', 'w') as f:
        f.write(cur_date)
    print("linkedin scraping is finished")
    # transforms jobs_info to a DataFrame object, then save it as csv file
    pandas_csv.save_data(jobs_info) 

main()
