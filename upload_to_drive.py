# TEST
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load service account credentials from environment
service_account_info = json.loads(os.environ["GDRIVE_CREDENTIALS"])
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/drive"]  # ✅ broader scope
)

# Build Drive API service
service = build("drive", "v3", credentials=credentials)

def upload_to_drive(file_path, drive_folder_id=None):
    file_name = os.path.basename(file_path)

    file_metadata = {
        "name": file_name,
        "mimeType": "application/vnd.google-apps.spreadsheet"
    }

    if drive_folder_id:
        file_metadata["parents"] = [drive_folder_id]

    media = MediaFileUpload(file_path, mimetype="text/csv", resumable=True)

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, webViewLink"
    ).execute()

    print(f"✅ File '{uploaded_file['name']}' uploaded successfully!")
    print(f"🔗 View it at: {uploaded_file['webViewLink']}")

    # 🔥 Share the file with yourself explicitly
    YOUR_EMAIL = "bilal.ziyane-etu@etu.univh2c.ma"  # ⬅️ Replace with your real email
    permission = {
        "type": "user",
        "role": "writer",
        "emailAddress": YOUR_EMAIL
    }

    try:
        service.permissions().create(
            fileId=uploaded_file["id"],
            body=permission,
            fields="id",
            sendNotificationEmail=False
        ).execute()
        print(f"👤 Shared with: {YOUR_EMAIL}")
    except Exception as e:
        print(f"❌ Failed to share file: {e}")

    return uploaded_file["id"]

# Optional CLI use
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("❌ Please provide the CSV file path to upload.")
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
