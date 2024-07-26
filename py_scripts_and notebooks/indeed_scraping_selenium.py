import time
import random 
import datetime
import pandas_csv as p_c 
import job_database as db
import jobs_scraping
import os
import traceback

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions

from typing import Tuple, Union

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
# Locators for various elements on the job listing pages
reject_cookies_loc = (By.CSS_SELECTOR, 'button[id="onetrust-reject-all-handler"]')
job_card_loc = (By.CSS_SELECTOR, 'div[data-testid="slider_item"]')
next_page_loc = (By.CSS_SELECTOR, 'a[data-testid="pagination-page-next"]')
close_pop_up_loc = (By.CSS_SELECTOR, 'button[aria-label="zamknij"]')

company_name_loc = (By.CSS_SELECTOR, 'span[data-testid="company-name"]')
location_loc = (By.CSS_SELECTOR, 'div[data-testid="text-location"]')
date_loc = (By.CSS_SELECTOR, 'span[data-testid="myJobsStateDate"]')

description_loc = (By.CSS_SELECTOR, 'div[id="jobDescriptionText"]')

def wait_presence(driver:webdriver, css_locator:Tuple[By, str], sec:int=5, all:Union[int, bool]=1):
    """Waits for the presence of elements located by css_locator within sec seconds."""
    if all:
        return WebDriverWait(driver, sec).until(EC.presence_of_all_elements_located(css_locator))
    return WebDriverWait(driver, sec).until(EC.presence_of_element_located(css_locator))

def reject_cookies(driver:webdriver):
    """Clicks the reject cookies button if present."""
    button = wait_presence(driver, reject_cookies_loc, sec=10, all=False)
    button.click()
    
def close_pop_up(driver:webdriver):
    """Clicks close window button if pop-up window is present"""
    try:
        button = wait_presence(driver, close_pop_up_loc, 2, all=False)
    except exceptions.TimeoutException:
        return None
    button.click()

def get_job_cards(driver:webdriver):
    """Returns all job card elements presented in a page"""
    return wait_presence(driver, job_card_loc)

def go_next_page(driver:webdriver):
    """Clicks the next page button"""
    button = wait_presence(driver, next_page_loc, all=False)
    button.click()

def rand_sleep(start:int, end:int):
    time.sleep(random.uniform(start, end))

def get_job_title(card):
    return card.find_element(By.CSS_SELECTOR, "span[title]").text

def get_company_name(card):
    return card.find_element(*company_name_loc).text

def get_location(card):
    return card.find_element(*location_loc).text

def parse_interval(interval:str):
    if interval in ('Dzisiaj', 'Dodano przed chwilą'):
        return datetime.timedelta(days=0)
    elif interval == 'wczoraj':
        return datetime.timedelta(days=1)
    else:
        #getting number from interval string
        number_from_interval = int(''.join(list(filter(str.isdigit, interval))))
        return datetime.timedelta(days=number_from_interval)
    
def get_current_date():
    return datetime.date.today()

def get_date(card):
    interval = card.find_element(*date_loc).text.split('\n')[-1]
    return get_current_date() - parse_interval(interval)

def get_job_id(card):
    return card.find_element(By.CSS_SELECTOR, "a[id]").get_attribute('id')

def get_description(driver, card):
    card.click()
    try:
        description_elem = wait_presence(driver, description_loc, sec=5, all=False)
    except exceptions.TimeoutException:
        return None
    else:
        return description_elem

def get_description_link(card):
    return card.find_element(By.CSS_SELECTOR, 'a[id]').get_attribute('href')

def identify_position(job_title:str):
    '''
    if position name is mentioned in job_title, return position, None otherwise
    '''
    d = dict(
        junior = ['junior', 'entry'],
        intern = ['intern', 'staż', 'train'],
        middle = ['assosiate', 'mid', 'intermediate'],
        senior = ['senior', 'executive', 'starszy']
    )
    for key in d:
        for position in d[key]:
            if position in job_title.lower():
                return key
    else:
        return None
    
def identify_prior_experience(position:str):

    if not position or position in ("junior", "intern"):
        return None
    return True 

def identify_polish(desc_element):
    li_bullet_points = desc_element.find_elements(By.TAG_NAME, 'li')
    p_bullet_points = desc_element.find_elements(By.TAG_NAME, 'p')
    bullet_points = li_bullet_points if len(li_bullet_points) != 0 else p_bullet_points
    if len(bullet_points) == 0:
        return False
    for bullet in bullet_points:
        bullet = bullet.text
        if 'Polish' in bullet  \
            or 'język polski' in bullet.lower() or 'polskiego' in bullet.lower():
            return True
    else:
        return False
    
def parse_job(driver:webdriver, card, scraped_ids:list):
    global jobs_info
    job_id = get_job_id(card)
    jobs_info["job_id"].append(job_id)
    job_title = get_job_title(card)
    position = identify_position(job_title)
    jobs_info["job_title"].append(job_title)
    jobs_info['position'].append(position)
    jobs_info['company_name'].append(get_company_name(card))
    jobs_info['location'].append(get_location(card))
    jobs_info['published_date'].append(get_date(card))
    jobs_info['scraped_date'].append(get_current_date())
    desc_element = get_description(driver, card)
    is_polish_required = identify_polish(desc_element) if desc_element else None
    jobs_info['description'].append(desc_element.text if desc_element else None)
    jobs_info['is_polish_required'].append(is_polish_required)
    jobs_info['source'].append('indeed')

    scraped_ids.append(job_id)

def make_lists_same_length():
    global jobs_info
    lens = []
    for key in jobs_info:
        lens.append(len(jobs_info[key]))
    min_len = min(lens)
    for key in jobs_info:
        jobs_info[key] = jobs_info[key][:min_len]
    
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
    
def choose_time_period(last_date_str):
    if not last_date_str : # if there is no last scraping date, then scrape jobs for any time
        return None
    cur_date = get_current_date()
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
    
def choose_base_url(job_title:str, location:str, time_period:str):
    time_periods = {
        'past_week' : '7',
        'past_two_weeks' : '14',
        'past_three_days' : '3',
        'past_24_hours' : '1'
    }  
    return f'https://pl.indeed.com/jobs?q={job_title}&l={location}&fromage={time_periods[time_period]}' if time_period else 'https://pl.indeed.com/jobs?q=data+analyst&l=Polska'


def main():
    with open('indeed_last_scraping_date.txt', 'w') as f:
        f.write(str(get_current_date()))

    conn, cur = db.connect_to_db()
    db.create_table_if_not_exists(conn, cur)
    scraped_ids = db.select_job_ids(conn, cur, "indeed")
    
    last_date_str = load_last_scraping_date()
    time_period = choose_time_period(last_date_str)
    
    job_title, location = jobs_scraping.get_searching_parameters()
    # transforming_searching_parameters
    splitted_job_title = job_title.split()
    splitted_location = location.split()
    if len(splitted_job_title) >= 2:
        job_title = '+'.join(splitted_job_title).lower()
    if len(splitted_location) >= 2:
        location = '+'.join(splitted_location)

    base_url = choose_base_url(job_title, location, time_period)

    driver = webdriver.Edge()
    driver.maximize_window()
    driver.get(base_url)

    reject_cookies(driver)
    print("indeed scraping is started\n")
    try:
        while True:
            while close_pop_up(driver):
                pass
            job_cards = get_job_cards(driver)
            for card in job_cards:
                id = get_job_id(card)
                if id in scraped_ids:
                    continue
                rand_sleep(2, 7)
                card.click()
                parse_job(driver, card, scraped_ids)
            try:
                go_next_page(driver)
            except exceptions.TimeoutException:
                break
    except:
        make_lists_same_length()
        print("Indeed scraping was ended because of error\n")
        print(traceback.format_exc())
    finally:
        with open(get_prev_dir(os.getcwd()) + r'\scraping_dates\indeed_last_scraping_date.txt', 'w') as f:
            f.write(str(datetime.date.today())) 
        print('indeed scraping is finished\n')
        p_c.save_data(jobs_info)


main()