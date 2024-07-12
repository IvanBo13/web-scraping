import time
import random 
import datetime
import os
import pandas_csv as p_c 
import job_database as db

import jobs_scraping

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
accept_cookies_loc = (By.CSS_SELECTOR, 'button[data-test="button-submitCookie"]')
card_loc1 = (By.CSS_SELECTOR, 'div[data-test="default-offer"]')
card_loc2 = (By.CSS_SELECTOR, 'div[data-test="positioned-offer"]')
card_title_loc = (By.CSS_SELECTOR, 'h2[data-test="offer-title"]')
date_loc = (By.CSS_SELECTOR, 'p[data-test="text-added"]')
href_loc = (By.CSS_SELECTOR, 'a[class="tiles_c8yvgfl core_n194fgoq"]')
next_page_loc = (By.CSS_SELECTOR, 'button[data-test="bottom-pagination-button-next"]')

job_name_loc = (By.CSS_SELECTOR, 'h1[data-scroll-id="job-title"]')
company_name_loc = (By.CSS_SELECTOR, 'h2[data-test="text-employerName"]')
position_loc = (By.CSS_SELECTOR, 'li[data-scroll-id="position-levels"]')
location_loc = (By.CSS_SELECTOR, 'li[data-scroll-id="workplaces"]')
requrements_loc = (By.CSS_SELECTOR, 'div[data-scroll-id="requirements-expected-1"]')

def wait_presence(driver:webdriver, css_locator:Tuple[By, str], sec:int=5, all:Union[int, bool]=1):
    """Waits for the presence of elements located by css_locator within sec seconds."""
    if all:
        return WebDriverWait(driver, sec).until(EC.presence_of_all_elements_located(css_locator))
    return WebDriverWait(driver, sec).until(EC.presence_of_element_located(css_locator))
    
def accept_cookies(driver):
    """Clicks the accept cookies button if present."""
    try:
        button = wait_presence(driver, accept_cookies_loc, sec=10, all=False)
    except exceptions.TimeoutException:
        return None
    button.click()

def go_next_page(driver):
    """Navigates to the next page of job listings."""
    try:
        button = wait_presence(driver, next_page_loc, 10, all=False)
    except exceptions.TimeoutException:
        return None
    button.click()
    return True

def get_href(card):
    """Returns the href attribute of the job card."""
    try:
        return card.find_element(*href_loc).get_attribute('href')
    except exceptions.NoSuchElementException:
        return None
    
def get_job_id(card):
    """Returns the job ID from the job card."""
    return card.get_attribute("data-test-offerid")

def get_date(card):
    """Returns the job's published date from the job card."""
    calendar = {"sty": 1, "lut": 2, "mar": 3, "kwi": 4, "maj": 5, "cze": 6, "lip": 7, "sie": 8, "wrz": 9, "paź":10, "lis":11, "gru":12}
    date_str = card.find_element(*date_loc).text.split(": ")[-1] # returns string in format "<day_number> <month_NAME> <year_number>"
    day_num, month_name, year_num = date_str.split()
    #converting month name into month number
    for short_month_name in calendar:
        if short_month_name in month_name:
            month_num = calendar[short_month_name]
    return f'{year_num}-{month_num}-{day_num}'

def get_cards(driver):
    """Returns the list of job cards from the page."""
    default_cards = wait_presence(driver, card_loc1)
    try:
        promoted_cards = wait_presence(driver, card_loc2, sec=2)
    except exceptions.TimeoutException:
        promoted_cards = []
    return promoted_cards + default_cards

def get_card_title(card):
    """Returns the title of the job from the job card."""
    return card.find_element(*card_title_loc).text.strip()
    
def rand_sleep(start, end):
    """Sleeps for a random amount of time between start and end seconds."""
    time.sleep(random.uniform(start, end))

def get_cards_info(cards:list):    
    """Extracts information from the job cards."""

    d = {}
    for card in cards:

        card_title = get_card_title(card)
        # If the card title doesn't contain keywords that indicate Data Analyst job, skip it
        if not jobs_scraping.identify_analyst_job(card_title): 
            continue

        loc_text = card.find_element(By.CSS_SELECTOR, 'div[class="tiles_c1zyaun"').text # returns location text
        # Some job postings have several locations, and there is the ability to choose one of them
        # If there is a 'lokaliz' instead of a location name, then there are several locations offered.
        # and the job card must be clicked to view all of them.
        if 'lokaliz' in loc_text:
            # tries to click the job card 10 times and retrieve the job description link.
            for i in range(10):
                card.click()
                try:
                    href = card.find_element(By.CSS_SELECTOR, 'a[class="tiles_l84op4y core_btsqgu core_n194fgoq"]').get_attribute('href')
                except exceptions.NoSuchElementException:
                    continue
                else:
                    break
            d[get_job_id(card)] = [card_title, href, get_date(card)]
        else:
            d[get_job_id(card)] = [card_title, get_href(card), get_date(card)]
    return d

def identify_polish_description(desc_text):
    """Identifies if the job description contains Polish letters."""
    polish_letters = "żśćźóąęłń"
    for letter in polish_letters:
        if letter in desc_text.lower():
            return True
    else:
        return False

def identify_polish(desc_text):
    """Identifies if the job requires Polish language"""
    is_polish_description = identify_polish_description(desc_text)
    is_english_required = False
    
    if 'Polish' in desc_text  \
        or 'język polski' in desc_text.lower() or 'polskiego' in desc_text.lower():
        return True
    
    if "English" in desc_text or "angielski" in desc_text.lower():
        is_english_required = True
    # If the description is written in Polish and English is not mentioned, it implies that Polish is required.
    if is_polish_description and not is_english_required:
            return True
    return False

def formate_position(position_str):
    """Formats the position string to standardize it."""
    position_str = position_str.lower()
    if "praktykant" in position_str or "stażysta" in position_str or "trainee" in position_str:
        return "intern"
    elif "junior" in position_str or "asystent" in position_str:
        return "junior"
    elif 'mid' in position_str:
        return 'middle'
    elif "senior" in position_str or "expert" in position_str or 'ekspert' in position_str or "kierownik" in position_str\
        or "koordynator" in position_str or "menedżer" in position_str or 'manager' in position_str\
        or "dyrektor" in position_str or 'director' in position_str:
        return "senior"
    else:
        return position_str


def get_from_description(driver, locator):
    """Returns the text content of an element located by locator when description page is opened"""
    sec=5
    if locator == requrements_loc:
        sec=10
    element = wait_presence(driver, locator, sec=sec, all=False)
    return element.text.strip()

def get_all_cards_info(driver):
    """Returns information from all job cards on all pages."""
    cards_info = {}
    next_exists = True
    while next_exists:
        cards = get_cards(driver)
        cards_info.update(get_cards_info(cards))
        rand_sleep(1, 10)
        next_exists = go_next_page(driver)
    return cards_info

def make_lists_same_length():
    """Ensures all lists in jobs_info have the same length by truncating longer lists."""
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
    """Loads the date of the last scraping from a file."""
    try:
        with open(get_prev_dir(os.getcwd()) + r'\scraping_dates\pracuj_last_scraping_date.txt', 'r') as f:
            d = str(f.readline()).strip()
        return d
    except FileNotFoundError:
        return None
    
def choose_time_period():
    """Chooses the scraping time period based on the last scraping date."""
    last_date_str = load_last_scraping_date()
    if not last_date_str : # if there is no last scraping date, then scrape jobs for any time
        return ''
    
    cur_date = datetime.date.today()
    last_date = datetime.date(*[int(s) for s in last_date_str.split('-')])

    one_day = datetime.timedelta(days=1)
    three_days = datetime.timedelta(days=3)
    one_week = datetime.timedelta(weeks=1)
    two_weeks = datetime.timedelta(weeks=2)
    one_month = datetime.timedelta(days=30)
    
    delta = cur_date - last_date
    if delta <= one_day:
        return "ostatnich%2024h;p,1"
    elif delta <= three_days:
        return "ostatnich%203%20dni;p,3"
    elif delta <= one_week:
        return "ostatnich%207%20dni;p,7"
    elif delta <= two_weeks:
        return "ostatnich%2014%20dni;p,14"
    elif delta <= one_month: 
        return 'ostatnich%2030%20dni;p,30'
    else:
        return ''
    
def main():
    """Main function to run the scraping process and save the data."""
    base_url = "https://it.pracuj.pl/praca/data%20analyst;kw/" + choose_time_period()
    with open(get_prev_dir(os.getcwd()) + 'scraping_dates\\pracuj_last_scraping_date.txt', 'w') as f:
        f.write(str(datetime.date.today()))
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(base_url)

    accept_cookies(driver)

    cards_info = get_all_cards_info(driver)
    # get ids of already scraped jobs from a database to avoid duplicating data
    conn, cur = db.connect_to_db()
    scraped_ids = db.select_job_ids(conn, cur, 'pracuj')

    print("pracuj scraping is started")
    for job_id in cards_info:

        if job_id in scraped_ids:
            continue

        try:
            driver.get(cards_info[job_id][1])
            jobs_info['job_id'].append(job_id)
            jobs_info['published_date'].append(cards_info[job_id][2])
            jobs_info['scraped_date']= datetime.date.today()

            jobs_info['job_title'].append(get_from_description(driver, job_name_loc))
            jobs_info['company_name'].append(get_from_description(driver, company_name_loc))
            jobs_info['location'].append(get_from_description(driver, location_loc))
            position = formate_position(get_from_description(driver, position_loc))
            jobs_info['position'].append(position)

            description = get_from_description(driver, requrements_loc)
            jobs_info['description'].append(description.strip())
            jobs_info['is_polish_required'].append(identify_polish(description))
            jobs_info['source'].append('pracuj')
            rand_sleep(1, 7)
        except:
            print(f"An error occured... Saving {len(jobs_info['job_id'])} jobs to csv")
            make_lists_same_length()
    print("pracuj scraping is finished")
    # writing current date of scraping to a file
    with open(get_prev_dir(os.getcwd()) + "scraping_dates\\" + 'pracuj_last_scraping_date.txt', 'w') as f:
        f.write(str(datetime.date.today()))
    # transforms jobs_info to a DataFrame object, then save it as csv file
    p_c.save_data(jobs_info)
    
main()