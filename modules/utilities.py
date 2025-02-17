import yaml
from pandas import read_parquet, DataFrame
from googleapiclient.discovery import build
from google.oauth2 import service_account

def load_configs(file_path: str = './configs.yaml') -> dict[str, any]:
    with open(file_path, 'r') as file:
        configs = yaml.safe_load(file)
    return configs

def load_parquet_file(file_path: str) -> DataFrame:
    try:
        return read_parquet(file_path)
    except Exception as e:
        raise ValueError(f"\033[91mError loading Parquet file\033[0m: {e}")

def get_progress_bar_text(progress: float, length: int = 50) -> str:
    progress = int(progress * length)
    return f"[\033[92m{'#' * progress}\033[0m{' ' * (length - progress)}] {progress * 2}%"

def get_refined_time_string(time_s: float) -> str:
    minutes, seconds = divmod(time_s, 60)
    hours, minutes = divmod(minutes, 60)

    if hours == 0 and minutes == 0:
        time_str: str = f"{seconds:.2f} s"
    else:
        time_str: str = f"{seconds:.0f} s"
        if minutes > 0:
            time_str = f"{minutes:.0f} m {time_str}"
        if hours > 0:
            time_str = f"{hours:.0f} h {time_str}"

    return time_str

def build_google_drive_service() -> any:
    """
    build the "service" object for the Google Drive API

    Returns:
        service: the service object for the Google Drive API

    Example:
        google_drive_service: any = build_google_drive_service()
    """
    SCOPES: list[str] = ['https://www.googleapis.com/auth/drive']
    GOOGLE_SERVICE_ACCOUNT_FILE_PATH: str = load_configs()['google_service_account_file_path']
    credentials = service_account.Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_FILE_PATH, scopes=SCOPES)

    google_drive_service = build('drive', 'v3', credentials=credentials)

    return google_drive_service
