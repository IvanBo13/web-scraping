# web-scraping
This repository houses a Python-based web scraping project that extracts and analyzes job postings from LinkedIn, Indeed, and Pracuj, with the aim of identifying relevant requirements for a job applicant. The project uses various libraries to handle web requests and parse HTML content to gather job data. To analyze job descriptions, the ChatGPT 3.5 API is used. The scraped data is stored in a CSV file, then loaded into a Pandas DataFrame, cleaned and transformed, and then loaded into a PostgreSQL database.

## Project Structure
The repository is organized as follows:

### data/: 
Contains the CSV file with the scraped job data.
- uncleaned_jobs.csv
### promts/: 
Contains text files used for generating prompts.
- full_promt.txt
- promt_without_position.txt
### py_scripts_and_notebooks/: 
Contains the Python scripts, Jupyter notebooks, and some text files used for scraping and data analysis.
- description_analysis.py: Analyzes job descriptions using the GPT model.
- indeed_scraping.py: Scrapes job postings from Indeed using `requests` and `BeautifulSoup` (requires proxies).
- indeed_scraping_selenium.py: Scrapes job postings from Indeed using `Selenium` library (doesn't require proxies).
- job_database.py: Handles database operations.
- jobs_scraping.py: Contains helper functions used across different scraping scripts.
- linkedin_scraping.py: Scrapes job postings from LinkedIn.
- pandas_csv.py: Handles CSV file operations using Pandas.
- pracuj_scraping.py: Scrapes job postings from Pracuj.
- run_scrapers: run all 3 scraping scripts simultaneously.
- transformation.ipynb: Jupyter notebook for data cleaning and transformation.
- [db_credentials.txt](https://github.com/IvanBo13/web-scraping/blob/main/py_scripts_and%20notebooks/db_credentials.txt): Contains credentials for the PostgreSQL database.
- proxies.txt: Contains proxies that are used for requests.
- searching_parameters.txt: Contains job title and location, which will be searched in sites.
### scraping_dates/: 
Contains text files with the dates of the last scraping operations. They are used to filter out job postings that are already scraped.
- indeed_last_scraping_date.txt
- linkedin_last_scraping_date.txt
- pracuj_last_scraping_date.txt
### README.md: 
This file.
### requirements.txt: 
Contains the list of Python packages required to run the project.

## Prerequisites
- [Python 3.11 or higher](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/)
- 5-10 proxies
- chatGPT API key (you must buy it on the [official site](https://platform.openai.com/))

## Setup and Installation
1. Clone the repository on your local machine.
2. Install the required packages using pip: `pip install -r <full_path_to_requirements.txt>`
3. [Create a PostgreSQL database](https://www.geeksforgeeks.org/postgresql-create-database/)
4. Update `db_credentials.txt` with the credentials of the PostgreSQL database that you created. 
```
dbname=<yourdbname>
user=<yourusername>
password=<yourpassword>
host=<yourhost>
port=<yourport>
```
5. [Set up your API key](https://platform.openai.com/docs/quickstart/step-2-set-up-your-api-key)
6. Write your proxies to `proxies.txt`
7. Update the text in `full_promt.txt` and `promt_without_position.txt` to reflect your position.
8. Update the text in `searching_parameters.txt`
```
job_title=<your_job_title> 
location=<your_location>
```

## Usage
You can run `run_scrapers.py` to run `linkedin_scraping.py`, `indeed_scraping.py` and `pracuj_scraping.py` scraping scripts simultaneously. Alternately, you can run only one needed scraping script.
Then `uncleaned_jobs.csv` will be created in the `data` folder. You can clean it your way or run all cells from `transformation.ipynb` to clean and transform data using ChatGPT.
When `transformation.ipynb` is completed, cleaned data is loaded into a database with credentials specified in `db_credentials.txt`, and `uncleaned_jobs.csv` is deleted.
 
