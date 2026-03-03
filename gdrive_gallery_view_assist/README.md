# GoogleDrive Gallery for View Assist

Home Assistant add-on that exposes a simple `/image` endpoint which serves a random (or sequential) image from a Google Drive folder. Intended for View Assist background images.

## Installation (Add-on Repository)

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**.
2. Open the menu (top right) → **Repositories**.
3. Add your GitHub repository URL.
4. Find **GoogleDrive Gallery for View Assist** in the list and install.

## Usage

1. Create a Google Cloud project and enable **Google Drive API**.
2. Create OAuth credentials (Desktop app) and get `client_id` and `client_secret`.
3. Obtain a refresh token for your account (see Notes).
4. Get the Drive folder ID for the folder you want.
5. Install the add-on, set options, and start it.
6. In View Assist, set background URL to `http://<homeassistant>:8099/image`.

## Add-on Options

- `client_id`, `client_secret`, `refresh_token`: required.
- `drive_folder_id`: required.
- `drive_include_shared`: include Shared Drives.
- `drive_recursive`: include subfolders.
- `exclude_patterns`: comma-separated glob patterns to skip (example: `*_thumb.jpg,*.tmp`).
- `cache_images`: keep downloaded images in memory.
- `cache_max_items`: max cached images (0 = unlimited).
- `cache_max_mb`: max cache size in MB (0 = unlimited).
- `prefetch_next`: download the next image in advance.
- `daily_shuffle`: shuffle images in a stable daily order.
- `mode`: `random` or `sequential`.
- `refresh_interval_minutes`: refresh album list on this interval.
- `max_items`: max images to keep in memory.

## Endpoints

- `GET /`: health/status JSON
- `GET /image`: returns a Google Drive image
No additional endpoints.

## Notes

Getting a refresh token requires a one-time OAuth flow. Use a helper script that requests `https://www.googleapis.com/auth/photoslibrary`, `https://www.googleapis.com/auth/photoslibrary.readonly`, and `https://www.googleapis.com/auth/photoslibrary.sharing` (needed for share links) and prints the refresh token. Once set, the add-on only uses the refresh token.

### OAuth helper (optional)

This repo includes a helper script you can run on your desktop to generate a refresh token:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r tools/requirements.txt
export GPHOTOS_CLIENT_ID="..."
export GPHOTOS_CLIENT_SECRET="..."
export OAUTH_SCOPE="https://www.googleapis.com/auth/drive.readonly"
python tools/google_oauth_helper.py
```

## Drive Folder ID

Open the folder in Google Drive; the ID is the string after `/folders/` in the URL.
