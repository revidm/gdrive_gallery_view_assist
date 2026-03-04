# Configuration

## Required

- `client_id`
- `client_secret`
- `refresh_token`
- `drive_folder_id`

## Optional

- `drive_include_shared`: include Shared Drives
- `drive_recursive`: include subfolders
- `exclude_patterns`: comma-separated glob patterns
- `cache_images`: keep downloaded images in memory
- `cache_max_items`: max cached images (0 = unlimited)
- `cache_max_mb`: max cache size in MB (0 = unlimited)
- `prefetch_next`: download the next image in advance
- `daily_shuffle`: shuffle images in a stable daily order
- `resize_profiles`: list of resize profiles used via `/image/{profile}`

Drive folder ID tip: open the folder in Google Drive and copy the ID from the URL after `/folders/`.

Resize profile example:

```yaml
resize_profiles:
  - name: echo5
    width: 960
    height: 480
    mode: cover
```

- `mode`: `random` or `sequential`
- `refresh_interval_minutes`: default `30`
- `max_items`: default `500`
- `port`: default `8099`
