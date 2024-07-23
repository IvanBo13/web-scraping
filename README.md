# web-scraping
This repository contains a Python-based web scraping project designed to extract and analyze job postings from LinkedIn, Indeed, and Pracuj to identify relevant requirements for an applicant for a job. The project uses various libraries to handle web requests and parse HTML content to gather job data. To analyze job description ChatGPT 3.5 API is used. The scraped data is stored in CSV file, then loaded into pandas DataFrame, cleaned and transformed, then loaded in a PostgreSQL database.

## Project Structure
The repository is organized as follows:

### data/: Contains the CSV file with the scraped job data.
- uncleaned_jobs.csv
### promts/: Contains text files used for generating prompts.
- full_promt.txt
- promt_without_position.txt
### py_scripts_and_notebooks/: Contains the Python scripts and Jupyter notebooks used for scraping and data analysis.
- description_analysis.py: Analyzes job descriptions using the GPT model.
- indeed_scraping.py: Scrapes job postings from Indeed.
- job_database.py: Handles database operations.
- jobs_scraping.py: Contains helper functions used across different scraping scripts.
- linkedin_scraping.py: Scrapes job postings from LinkedIn.
- pandas_csv.py: Handles CSV file operations using pandas.
- pracuj_scraping.py: Scrapes job postings from Pracuj.
- transformation.ipynb: Jupyter notebook for data cleaning and transformation.
### scraping_dates/: Contains text files with the dates of the last scraping operations. They are used to filter out job postings that are already scraped
- indeed_last_scraping_date.txt
- linkedin_last_scraping_date.txt
- pracuj_last_scraping_date.txt
### README.md: This file.
### requirements.txt: Contains the list of Python packages required to run the project.

## Prerequisites
- [Python 3.11 or higher](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/)
- 5-10 proxies
- chatGPT API key (you must buy it in [official cite](https://platform.openai.com/))

## Setup and installation
1. Clone the repository on your local machine
2. Install the required packages
3. [Create PostgreSQL database](https://www.geeksforgeeks.org/postgresql-create-database/)
4. Update `db_credentials.txt` with credentials of PostgreSQL database that you created
5. [Set up your API key](https://platform.openai.com/docs/quickstart/step-2-set-up-your-api-key)
6. 
