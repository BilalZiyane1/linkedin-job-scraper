import os
import glob
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

FOLDER_ID = "1ySUMedn2pS7js3uq_RrZrVFYG16zDbqg"  # Replace this with your real folder ID

def upload_latest_csv():
    list_of_files = glob.glob('linkedin_jobs_*.csv')
    if not list_of_files:
        print("No CSV file found.")
        return

    latest_file = max(list_of_files, key=os.path.getctime)

    creds = service_account.Credentials.from_service_account_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/drive.file']
    )

    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': os.path.basename(latest_file),
        'parents': [FOLDER_ID]
    }

    media = MediaFileUpload(latest_file, mimetype='text/csv')
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    print(f"File '{latest_file}' uploaded with ID: {uploaded_file['id']}")

if __name__ == "__main__":
    upload_latest_csv()
