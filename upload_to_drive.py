#TEST
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load service account credentials from environment variable
try:
    service_account_info = json.loads(os.environ["GDRIVE_CREDENTIALS"])
except KeyError:
    raise RuntimeError("❌ GDRIVE_CREDENTIALS environment variable not found.")

# Authenticate with Google Drive
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/drive.file"]
)

# Build the Drive API service
service = build("drive", "v3", credentials=credentials)


def upload_to_drive(file_path, drive_folder_id=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ File not found: {file_path}")

    file_name = os.path.basename(file_path)

    # Optional: Validate folder access
    if drive_folder_id:
        try:
            folder = service.files().get(fileId=drive_folder_id, fields="id, name").execute()
            print(f"📁 Uploading to folder: {folder['name']} (ID: {drive_folder_id})")
        except Exception as e:
            print(f"❌ Error: Could not access folder with ID '{drive_folder_id}'.")
            print("👉 Make sure the folder exists and is shared with your service account.")
            print(f"🔍 Exception details: {e}")
            return None

    file_metadata = {
        "name": file_name,
        "mimeType": "application/vnd.google-apps.spreadsheet"
    }

    if drive_folder_id:
        file_metadata["parents"] = [drive_folder_id]

    media = MediaFileUpload(file_path, mimetype="text/csv", resumable=True)

    try:
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink"
        ).execute()

        print(f"✅ File '{uploaded_file['name']}' uploaded successfully!")
        print(f"🔗 View it at: {uploaded_file['webViewLink']}")
        return uploaded_file["id"]

    except Exception as e:
        print(f"❌ Failed to upload file: {file_name}")
        print(f"🔍 Exception details: {e}")
        return None


# Optional CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("❌ Please provide the path to the file you want to upload.")
    else:
        upload_to_drive(sys.argv[1])





# import os
# import json
# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaFileUpload

# # Load service account credentials from environment
# service_account_info = json.loads(os.environ["GDRIVE_CREDENTIALS"])
# credentials = service_account.Credentials.from_service_account_info(
#     service_account_info,
#     scopes=["https://www.googleapis.com/auth/drive.file"]
# )

# # Build Drive API service
# service = build("drive", "v3", credentials=credentials)

# def upload_to_drive(file_path, drive_folder_id=None):
#     file_name = os.path.basename(file_path)

#     file_metadata = {
#         "name": file_name,
#         "mimeType": "application/vnd.google-apps.spreadsheet"
#     }

#     if drive_folder_id:
#         file_metadata["parents"] = [drive_folder_id]

#     media = MediaFileUpload(file_path, mimetype="text/csv", resumable=True)

#     uploaded_file = service.files().create(
#         body=file_metadata,
#         media_body=media,
#         fields="id, name, webViewLink"
#     ).execute()

#     print(f"✅ File '{uploaded_file['name']}' uploaded successfully!")
#     print(f"🔗 View it at: {uploaded_file['webViewLink']}")
#     return uploaded_file["id"]

# # Optional CLI use
# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) < 2:
#         print("❌ Please provide the CSV file path to upload.")
#     else:
#         upload_to_drive(sys.argv[1])











# import os
# import io
# import json
# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaFileUpload

# # Get credentials from the GITHUB secret
# service_account_info = json.loads(os.environ["GDRIVE_CREDENTIALS"])
# credentials = service_account.Credentials.from_service_account_info(
#     service_account_info,
#     scopes=["https://www.googleapis.com/auth/drive.file"]
# )

# # Build the Drive service
# service = build("drive", "v3", credentials=credentials)

# def upload_to_drive(file_path, drive_folder_id=None):
#     file_name = os.path.basename(file_path)

#     file_metadata = {
#         "name": file_name,
#         "mimeType": "application/vnd.google-apps.spreadsheet"
#     }

#     if drive_folder_id:
#         file_metadata["parents"] = [drive_folder_id]

#     media = MediaFileUpload(file_path, mimetype="text/csv", resumable=True)

#     uploaded_file = service.files().create(
#         body=file_metadata,
#         media_body=media,
#         fields="id, name, webViewLink"
#     ).execute()

#     print(f"✅ File '{uploaded_file['name']}' uploaded successfully!")
#     print(f"🔗 View it at: {uploaded_file['webViewLink']}")
#     return uploaded_file["id"]

# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) < 2:
#         print("❌ Please provide the CSV file path to upload.")
#     else:
#         upload_to_drive(sys.argv[1])
