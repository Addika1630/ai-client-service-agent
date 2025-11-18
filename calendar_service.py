import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def _team_env_key(team: str, suffix: str) -> str:
    return f"CAL_{team.upper()}_{suffix}"


def _resolve_paths(team: str):
    # Determine base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Allow env overrides
    token_env = os.getenv(_team_env_key(team, "TOKEN_PATH"))
    creds_env = os.getenv(_team_env_key(team, "CREDENTIALS_PATH"))

    # Defaults
    token_default = os.path.join(base_dir, f"token_{team}.json")
    creds_default_specific = os.path.join(base_dir, f"credentials_{team}.json")
    creds_default = os.path.join(base_dir, "credentials.json")

    token_path = token_env if token_env else token_default
    # Prefer team-specific credentials if present
    if creds_env:
        creds_path = creds_env
    elif os.path.exists(creds_default_specific):
        creds_path = creds_default_specific
    else:
        creds_path = creds_default

    return token_path, creds_path


def get_calendar_service_for_team(team: str = "technical"):
    creds = None
    token_path, creds_path = _resolve_paths(team)

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Persist token to the team-specific path
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


# Backward compatibility: preserve original function name
def get_calendar_service():
    return get_calendar_service_for_team("technical")


