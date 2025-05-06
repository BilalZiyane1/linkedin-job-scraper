import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from datetime import datetime
import warnings
import os
import json
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

warnings.filterwarnings('ignore')

# Job config
JOB_CATEGORIES = [
    {
        "category": "frontend developement",
        "aliases": ["frontend developement", "frontend development"]
    }
]
LOCATIONS = ["USA"]
MAX_JOBS = 10
RESULTS_PER_PAGE = 25
MAX_THREADS = 3
DELAY_RANGE = (1, 2)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9"
    }

def scrape_job_listings(search_term, original_category, location, seen_job_ids):
    job_listings = []
    encoded_job = quote(search_term)
    encoded_location = quote(location)

    for start in range(0, 1000, RESULTS_PER_PAGE):
        if len(seen_job_ids) >= MAX_JOBS:
            break
        time.sleep(random.uniform(*DELAY_RANGE))
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/{encoded_job}-jobs?keywords={encoded_job}&location={encoded_location}&start={start}"

        try:
            response = requests.get(url, headers=get_random_headers())
            if response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, "html.parser")
            jobs = soup.find_all("li")
            if not jobs:
                break

            for job in jobs:
                base_card = job.find("div", {"class": "base-card"})
                if not base_card:
                    continue
                job_id = base_card.get("data-entity-urn", "").split(":")[-1]
                if job_id and job_id not in seen_job_ids:
                    seen_job_ids.add(job_id)
                    job_listings.append({
                        "job_id": job_id,
                        "original_category": original_category,
                        "search_location": location,
                        "search_term_used": search_term
                    })
                if len(seen_job_ids) >= MAX_JOBS:
                    break
        except Exception as e:
            print(f"Error scraping: {e}")
            continue

    return job_listings

def scrape_job_details(job):
    job_url = f"https://www.linkedin.com/jobs/view/{job['job_id']}"
    details = {
        **job,
        "job_title": None,
        "company_name": None,
        "company_url": None,
        "location": None,
        "time_posted": None,
        "num_applicants": None,
        "employment_type": None,
        "job_level": None,
        "job_description": None,
        "job_url": job_url
    }

    try:
        time.sleep(random.uniform(*DELAY_RANGE))
        response = requests.get(job_url, headers=get_random_headers())
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            details["job_title"] = soup.find("h1", {"class": "top-card-layout__title"}).get_text(strip=True) if soup.find("h1", {"class": "top-card-layout__title"}) else None
            company = soup.find("a", {"class": "topcard__org-name-link"})
            if company:
                details["company_name"] = company.get_text(strip=True)
                details["company_url"] = company.get("href", "")
            loc = soup.find("span", {"class": "topcard__flavor--bullet"})
            if loc:
                details["location"] = loc.get_text(strip=True)
            time_posted = soup.find("span", {"class": "posted-time-ago__text"})
            if time_posted:
                details["time_posted"] = time_posted.get_text(strip=True)
            applicants = soup.find("span", {"class": "num-applicants__caption"})
            if applicants:
                details["num_applicants"] = applicants.get_text(strip=True)
            criteria = soup.find_all("span", {"class": "description__job-criteria-text"})
            if criteria:
                details["employment_type"] = criteria[0].get_text(strip=True) if len(criteria) > 0 else None
                details["job_level"] = criteria[1].get_text(strip=True) if len(criteria) > 1 else None
            desc = soup.find("div", {"class": "show-more-less-html__markup"})
            if desc:
                details["job_description"] = desc.get_text(strip=True)
    except Exception as e:
        print(f"Error fetching job detail: {e}")
    return details

def upload_to_gdrive(file_path, folder_id):
    creds = json.loads(os.getenv("GDRIVE_CREDENTIALS"))
    with open("temp_creds.json", "w") as f:
        json.dump(creds, f)

    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("temp_creds.json")
    if not gauth.credentials:
        gauth.LocalWebserverAuth()
    gauth.ServiceAuth()
    drive = GoogleDrive(gauth)

    file_drive = drive.CreateFile({
        'title': os.path.basename(file_path),
        'parents': [{'id': folder_id}]
    })
    file_drive.SetContentFile(file_path)
    file_drive.Upload()
    print(f"Uploaded to Google Drive: {file_path}")

def main():
    seen_job_ids = set()
    all_jobs = []

    for category in JOB_CATEGORIES:
        for alias in category["aliases"]:
            for location in LOCATIONS:
                listings = scrape_job_listings(alias, category["category"], location, seen_job_ids)
                all_jobs.extend(listings)
                if len(seen_job_ids) >= MAX_JOBS:
                    break
            if len(seen_job_ids) >= MAX_JOBS:
                break
        if len(seen_job_ids) >= MAX_JOBS:
            break

    print(f"Total jobs collected: {len(all_jobs)}")

    job_details = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(scrape_job_details, job) for job in all_jobs]
        for future in futures:
            job_details.append(future.result())

    df = pd.DataFrame(job_details)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"linkedin_jobs_test_{date_str}.csv"
    df.to_csv(filename, index=False)
    print(f"Saved to: {filename}")

    # Replace with your actual GDrive folder ID
    upload_to_gdrive(filename, folder_id="1ySUMedn2pS7js3uq_RrZrVFYG16zDbqg")

    return filename

if __name__ == "__main__":
    print(main())

















# import requests
# from bs4 import BeautifulSoup
# import pandas as pd
# import time
# import random
# from concurrent.futures import ThreadPoolExecutor
# from urllib.parse import quote
# from datetime import datetime
# import warnings

# # Suppress warnings
# warnings.filterwarnings('ignore')

# # Enhanced job configuration with aliases
# JOB_CATEGORIES = [
#     {
#         "category": "commerce & teleconseille",
#         "aliases": [
#             "commerce & teleconseille",
#             "sales and customer service",
#             "téléconseiller",
#             "customer support",
#             "telemarketing"
#         ]
#     },
#     {
#         "category": "maintenance informatique",
#         "aliases": [
#             "maintenance informatique",
#             "IT maintenance",
#             "computer maintenance",
#             "IT support",
#             "systèmes informatiques"
#         ]
#     },
#     {
#         "category": "community management",
#         "aliases": [
#             "community management",
#             "social media management",
#             "gestion de communauté",
#             "online community manager"
#         ]
#     },
#     {
#         "category": "frontend developement",
#         "aliases": [
#             "frontend developement",
#             "frontend development",
#             "développement frontend",
#             "web development"
#         ]
#     },
#     {
#         "category": "Creation du jeu",
#         "aliases": [
#             "Creation du jeu",
#             "game development",
#             "développement de jeu",
#             "video game design"
#         ]
#     },
#     {
#         "category": "marketing digital",
#         "aliases": [
#             "marketing digital",
#             "digital marketing",
#             "e-marketing",
#             "web marketing"
#         ]
#     },
#     {
#         "category": "Creation du contenu",
#         "aliases": [
#             "Creation du contenu",
#             "content creation",
#             "création de contenu",
#             "content marketing"
#         ]
#     }
# ]

# LOCATIONS = [
#     "Morocco",
#     "Europe",
#     "Middle East",
#     "USA",
#     "Canada"
# ]

# MAX_RESULTS_PER_QUERY = 1000
# RESULTS_PER_PAGE = 25
# MAX_THREADS = 5
# DELAY_RANGE = (1, 3)
# USER_AGENTS = [
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
# ]

# def get_random_headers():
#     return {
#         "User-Agent": random.choice(USER_AGENTS),
#         "Accept-Language": "en-US,en;q=0.9",
#         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
#         "Referer": "https://www.google.com/"
#     }

# def scrape_job_listings(search_term, original_category, location, seen_job_ids):
#     job_listings = []
#     encoded_job = quote(search_term)
#     encoded_location = quote(location)

#     for start in range(0, MAX_RESULTS_PER_QUERY, RESULTS_PER_PAGE):
#         time.sleep(random.uniform(*DELAY_RANGE))
#         list_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/{encoded_job}-jobs?keywords={encoded_job}&location={encoded_location}&start={start}"

#         try:
#             response = requests.get(list_url, headers=get_random_headers())

#             if response.status_code != 200:
#                 print(f"Failed to fetch {search_term} in {location} at start={start}")
#                 break

#             soup = BeautifulSoup(response.text, "html.parser")
#             jobs = soup.find_all("li")

#             if not jobs:
#                 break

#             for job in jobs:
#                 base_card_div = job.find("div", {"class": "base-card"})
#                 if not base_card_div:
#                     continue

#                 job_id = base_card_div.get("data-entity-urn", "").split(":")[-1]
#                 if not job_id or job_id in seen_job_ids:
#                     continue

#                 seen_job_ids.add(job_id)
#                 job_listings.append({
#                     "job_id": job_id,
#                     "original_category": original_category,
#                     "search_location": location,
#                     "search_term_used": search_term
#                 })

#         except Exception as e:
#             print(f"Error scraping {search_term} in {location}: {str(e)}")
#             continue

#     return job_listings

# def scrape_job_details(job):
#     job_url = f"https://www.linkedin.com/jobs/view/{job['job_id']}"
#     job_post = {
#         "job_id": job["job_id"],
#         "original_category": job["original_category"],
#         "search_location": job["search_location"],
#         "search_term_used": job["search_term_used"],
#         "job_title": None,
#         "company_name": None,
#         "company_url": None,
#         "location": None,
#         "time_posted": None,
#         "num_applicants": None,
#         "employment_type": None,
#         "job_level": None,
#         "job_description": None,
#         "job_url": job_url
#     }

#     try:
#         time.sleep(random.uniform(*DELAY_RANGE))
#         response = requests.get(job_url, headers=get_random_headers())

#         if response.status_code == 200:
#             soup = BeautifulSoup(response.text, "html.parser")

#             title_element = soup.find("h1", {"class": "top-card-layout__title"})
#             if title_element:
#                 job_post["job_title"] = title_element.get_text(strip=True)

#             company_element = soup.find("a", {"class": "topcard__org-name-link"})
#             if company_element:
#                 job_post["company_name"] = company_element.get_text(strip=True)
#                 job_post["company_url"] = company_element.get("href", "")

#             location_element = soup.find("span", {"class": "topcard__flavor--bullet"})
#             if location_element:
#                 job_post["location"] = location_element.get_text(strip=True)

#             time_element = soup.find("span", {"class": "posted-time-ago__text"})
#             if time_element:
#                 job_post["time_posted"] = time_element.get_text(strip=True)

#             applicants_element = soup.find("span", {"class": "num-applicants__caption"})
#             if applicants_element:
#                 job_post["num_applicants"] = applicants_element.get_text(strip=True)

#             criteria_elements = soup.find_all("span", {"class": "description__job-criteria-text"})
#             if criteria_elements:
#                 job_post["employment_type"] = criteria_elements[0].get_text(strip=True) if len(criteria_elements) > 0 else None
#                 job_post["job_level"] = criteria_elements[1].get_text(strip=True) if len(criteria_elements) > 1 else None

#             description_element = soup.find("div", {"class": "show-more-less-html__markup"})
#             if description_element:
#                 job_post["job_description"] = description_element.get_text(strip=True)

#     except Exception as e:
#         print(f"Error scraping job {job['job_id']}: {str(e)}")

#     return job_post

# def main():
#     seen_job_ids = set()
#     all_jobs = []

#     for job_category in JOB_CATEGORIES:
#         original_category = job_category["category"]
#         print(f"\nProcessing category: {original_category}")

#         for alias in job_category["aliases"]:
#             for location in LOCATIONS:
#                 print(f"Searching: '{alias}' in {location}")
#                 listings = scrape_job_listings(alias, original_category, location, seen_job_ids)
#                 all_jobs.extend(listings)
#                 print(f"Found {len(listings)} new listings using '{alias}'")

#     print(f"\nTotal unique jobs found: {len(all_jobs)}")

#     job_details = []
#     with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
#         futures = [executor.submit(scrape_job_details, job) for job in all_jobs]
#         for i, future in enumerate(futures):
#             try:
#                 result = future.result()
#                 job_details.append(result)
#                 if (i + 1) % 10 == 0:
#                     print(f"Processed {i+1}/{len(all_jobs)} jobs")
#             except Exception as e:
#                 print(f"Error processing job: {str(e)}")

#     df = pd.DataFrame(job_details)

#     # Generate unique filename with timestamp
#     date_str = datetime.now().strftime("%Y-%m-%d")
#     filename = f"linkedin_jobs_{date_str}.csv"
#     df.to_csv(filename, index=False)
#     print(f"\nScraping complete. Data saved to {filename}")

#     return filename

# if __name__ == "__main__":
#     print(main())
