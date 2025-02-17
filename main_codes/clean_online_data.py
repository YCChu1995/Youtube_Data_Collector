from sys import path as sys_path
sys_path += ['modules']
from utilities import build_google_drive_service, load_configs

def __delete_file_from_google_drive(google_drive_service: any, file_id: str) -> bool:
    try:
        google_drive_service.files().delete(fileId=file_id).execute()
        return True
        # print(f"File with ID {file_id} has been deleted.")
    except Exception as e:
        print(f"\033[91mAn error occurred\033[0m: {e}")
        return False

def __clean_google_drive_folder(google_drive_service: any, folder_id: str, folder_name: str):
    try:
        results = google_drive_service.files().list(q=f"'{folder_id}' in parents", fields="files(id, name)").execute()
        files = results.get('files', [])
    except Exception as e:
        print(f"\033[91mAn error occurred\033[0m: {e}")

    cleaned_file_count: int = 0
    if files:
        for file in files:
            if __delete_file_from_google_drive(google_drive_service, file['id']):
                cleaned_file_count += 1

    if cleaned_file_count == 0:
        print(f"G-Drive folder \"\033[92m{folder_name}\033[0m\" was already empty.")
    else:
        print(f"G-Drive Folder \"\033[92m{folder_name}\033[0m\" has been cleaned, \033[92m{cleaned_file_count}\033[0m files has been deleted.")

def clean_online_data():
    configs: dict[str, any] = load_configs()
    google_drive_service: any = build_google_drive_service()

    FOLDER_IDS: dict[str, str] = configs['parent_folder_id_to_upload_data']

    for interested_category, folder_id in FOLDER_IDS.items():
        __clean_google_drive_folder(google_drive_service, folder_id, folder_name=interested_category)

if __name__ == '__main__':
    clean_online_data()