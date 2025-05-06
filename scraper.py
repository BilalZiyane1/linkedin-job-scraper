import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from datetime import datetime
import warnings
from threading import Lock

warnings.filterwarnings('ignore')

JOB_CATEGORIES = [
    {"category": "commerce & teleconseille", "aliases": ["commerce & teleconseille", "sales and customer service", "téléconseiller", "customer support", "telemarketing"]},
    {"category": "maintenance informatique", "aliases": ["maintenance informatique", "IT maintenance", "computer maintenance", "IT support", "systèmes informatiques"]},
    {"category": "community management", "aliases": ["community management", "social media management", "gestion de communauté", "online community manager"]},
    {"category": "frontend developement", "aliases": ["frontend developement", "frontend development", "développement frontend", "web development"]},
    {"category": "Creation du jeu", "aliases": ["Creation du jeu", "game development", "développement de jeu", "video game design"]},
    {"category": "marketing digital", "aliases": ["marketing digital", "digital marketing", "e-marketing", "web marketing"]},
    {"category": "Creation du contenu", "aliases": ["Creation du contenu", "content creation", "création de contenu", "content marketing"]}
]

LOCATIONS = ["Morocco", "Europe", "Middle East", "USA", "Canada"]
MAX_RESULTS_PER_QUERY = 1000
RESULTS_PER_PAGE = 25
MAX_THREADS = 5
DELAY_RANGE = (1, 3)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/"
    }

def scrape_job_listings(search_term, original_category, location, seen_job_ids_local):
    job_listings = []
    encoded_job = quote(search_term)
    encoded_location = quote(location)

    for start in range(0, MAX_RESULTS_PER_QUERY, RESULTS_PER_PAGE):
        time.sleep(random.uniform(*DELAY_RANGE))
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_job}&location={encoded_location}&start={start}"

        try:
            response = requests.get(url, headers=get_random_headers())
            if response.status_code != 200:
                print(f"Failed to fetch {search_term} in {location} at start={start}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            jobs = soup.find_all("li")

            if not jobs:
                break

            for job in jobs:
                base_card = job.find("div", class_="base-card")
                if not base_card:
                    continue

                job_id = base_card.get("data-entity-urn", "").split(":")[-1]
                if not job_id or job_id in seen_job_ids_local:
                    continue

                seen_job_ids_local.add(job_id)
                job_listings.append({
                    "job_id": job_id,
                    "original_category": original_category,
                    "search_location": location,
                    "search_term_used": search_term
                })

        except Exception as e:
            print(f"Error scraping {search_term} in {location}: {e}")
            continue

    return job_listings

def scrape_job_details(job):
    job_url = f"https://www.linkedin.com/jobs/view/{job['job_id']}"
    job_post = {
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
        if response.status_code != 200:
            return job_post

        soup = BeautifulSoup(response.text, "html.parser")

        job_post["job_title"] = soup.find("h1", {"class": "top-card-layout__title"}).get_text(strip=True) if soup.find("h1", {"class": "top-card-layout__title"}) else None
        company_tag = soup.find("a", {"class": "topcard__org-name-link"})
        if company_tag:
            job_post["company_name"] = company_tag.get_text(strip=True)
            job_post["company_url"] = company_tag.get("href", "")
        job_post["location"] = soup.find("span", {"class": "topcard__flavor--bullet"}).get_text(strip=True) if soup.find("span", {"class": "topcard__flavor--bullet"}) else None
        job_post["time_posted"] = soup.find("span", {"class": "posted-time-ago__text"}).get_text(strip=True) if soup.find("span", {"class": "posted-time-ago__text"}) else None
        job_post["num_applicants"] = soup.find("span", {"class": "num-applicants__caption"}).get_text(strip=True) if soup.find("span", {"class": "num-applicants__caption"}) else None

        criteria = soup.find_all("span", {"class": "description__job-criteria-text"})
        if criteria:
            if len(criteria) > 0:
                job_post["employment_type"] = criteria[0].get_text(strip=True)
            if len(criteria) > 1:
                job_post["job_level"] = criteria[1].get_text(strip=True)

        desc = soup.find("div", {"class": "show-more-less-html__markup"})
        if desc:
            job_post["job_description"] = desc.get_text(strip=True)

    except Exception as e:
        print(f"Error scraping job {job['job_id']}: {e}")

    return job_post

def fetch_and_collect_jobs(alias, original_category, location, seen_job_ids_lock, seen_job_ids):
    local_seen = set()
    listings = scrape_job_listings(alias, original_category, location, local_seen)
    new_jobs = []

    with seen_job_ids_lock:
        for job in listings:
            if job['job_id'] not in seen_job_ids:
                seen_job_ids.add(job['job_id'])
                new_jobs.append(job)

    print(f"Found {len(new_jobs)} new jobs using alias '{alias}' in {location}")
    return new_jobs

def main():
    seen_job_ids = set()
    seen_job_ids_lock = Lock()
    all_jobs = []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_params = []

        for job_category in JOB_CATEGORIES:
            original_category = job_category["category"]
            print(f"\nProcessing category: {original_category}")

            for alias in job_category["aliases"]:
                for location in LOCATIONS:
                    future = executor.submit(
                        fetch_and_collect_jobs,
                        alias, original_category, location,
                        seen_job_ids_lock, seen_job_ids
                    )
                    future_to_params.append(future)

        for i, future in enumerate(future_to_params):
            try:
                listings = future.result()
                all_jobs.extend(listings)
                if (i + 1) % 10 == 0:
                    print(f"Fetched listings: {i + 1}/{len(future_to_params)}")
            except Exception as e:
                print(f"Error fetching listings: {e}")

    print(f"\nTotal unique jobs collected: {len(all_jobs)}")

    job_details = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(scrape_job_details, job) for job in all_jobs]
        for i, future in enumerate(futures):
            try:
                result = future.result()
                job_details.append(result)
                if (i + 1) % 10 == 0:
                    print(f"Processed job details: {i + 1}/{len(all_jobs)}")
            except Exception as e:
                print(f"Error processing job details: {e}")

    df = pd.DataFrame(job_details)
    filename = f"linkedin_jobs_{datetime.now().strftime('%Y-%m-%d')}.csv"
    df.to_csv(filename, index=False)
    print(f"\nScraping complete. Data saved to: {filename}")
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
# from upload_to_drive import upload_to_drive  # 👈 import working upload function

# # ----------------- CONFIG -----------------
# JOB_CATEGORIES = [
#     {
#         "category": "frontend developement",
#         "aliases": [
#             "frontend developement",
#             "frontend development",
#             "développement frontend",
#             "web development"
#         ]
#     }
# ]

# LOCATIONS = ["Morocco"]

# MAX_RESULTS_PER_QUERY = 1000
# RESULTS_PER_PAGE = 25
# MAX_THREADS = 5
# DELAY_RANGE = (1, 2)
# MAX_JOBS_TOTAL = 10  # 👈 limit to 10 jobs
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
#         if len(seen_job_ids) >= MAX_JOBS_TOTAL:
#             break

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
#                 if len(seen_job_ids) >= MAX_JOBS_TOTAL:
#                     break

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
#         print(f"\n🔍 Processing category: {original_category}")

#         for alias in job_category["aliases"]:
#             for location in LOCATIONS:
#                 print(f"  ➤ Searching: '{alias}' in {location}")
#                 listings = scrape_job_listings(alias, original_category, location, seen_job_ids)
#                 all_jobs.extend(listings)
#                 print(f"  ➤ Found {len(listings)} new listings using '{alias}'")
#                 if len(seen_job_ids) >= MAX_JOBS_TOTAL:
#                     break
#             if len(seen_job_ids) >= MAX_JOBS_TOTAL:
#                 break
#         if len(seen_job_ids) >= MAX_JOBS_TOTAL:
#             break

#     print(f"\n✅ Total unique jobs found: {len(all_jobs)}")

#     job_details = []
#     with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
#         futures = [executor.submit(scrape_job_details, job) for job in all_jobs]
#         for i, future in enumerate(futures):
#             try:
#                 result = future.result()
#                 job_details.append(result)
#                 print(f"Processed {i+1}/{len(all_jobs)} jobs")
#             except Exception as e:
#                 print(f"Error processing job: {str(e)}")

#     df = pd.DataFrame(job_details)
#     date_str = datetime.now().strftime("%Y-%m-%d")
#     filename = f"linkedin_jobs_test_{date_str}.csv"
#     df.to_csv(filename, index=False)
#     print(f"\n📁 Saved to: {filename}")
#     return filename

# if __name__ == "__main__":
#     filename = main()
#     print(filename)  # Only output the filename, clean for GitHub Actions

















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
