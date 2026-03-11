import asyncio
import logging
import time
from dataclasses import dataclass
import httpx


TOKEN_URL = "https://oauth2.googleapis.com/token"
FILES_URL = "https://www.googleapis.com/drive/v3/files"

LOGGER = logging.getLogger(__name__)


@dataclass
class DriveItem:
    id: str
    name: str
    mime_type: str


class GoogleDriveClient:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._access_token: str | None = None
        self._access_token_expires_at: float = 0
        self._lock = asyncio.Lock()

    async def _refresh_access_token(self) -> str:
        async with self._lock:
            if self._access_token and time.time() < self._access_token_expires_at - 30:
                return self._access_token
            async with httpx.AsyncClient(timeout=20) as client:
                payload = {
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "refresh_token": self._refresh_token,
                    "grant_type": "refresh_token",
                }
                response = await client.post(TOKEN_URL, data=payload)
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError:
                    LOGGER.error("Token refresh failed: %s", response.text.strip())
                    raise
                data = response.json()
                self._access_token = data["access_token"]
                expires_in = int(data.get("expires_in", 3600))
                self._access_token_expires_at = time.time() + expires_in
                if self._access_token is None:
                    raise RuntimeError("Failed to obtain access token")
                return self._access_token

    async def list_folder_images(
        self,
        folder_id: str,
        page_size: int,
        max_items: int,
        include_shared: bool,
        recursive: bool,
    ) -> list[DriveItem]:
        access_token = await self._refresh_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        items: list[DriveItem] = []
        folder_ids = [folder_id]
        async with httpx.AsyncClient(timeout=30) as client:
            while folder_ids:
                current_folder = folder_ids.pop(0)
                next_page_token: str | None = None
                while True:
                    params: dict[str, str] = {
                        "pageSize": str(min(page_size, 1000)),
                        "q": f"'{current_folder}' in parents and trashed=false",
                        "fields": "nextPageToken,files(id,name,mimeType)",
                    }
                    if include_shared:
                        params["includeItemsFromAllDrives"] = "true"
                        params["supportsAllDrives"] = "true"
                    if next_page_token:
                        params["pageToken"] = next_page_token
                    response = await client.get(
                        FILES_URL, headers=headers, params=params
                    )
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as exc:
                        error_body = response.text
                        raise httpx.HTTPStatusError(
                            f"Drive list failed: {error_body}",
                            request=exc.request,
                            response=exc.response,
                        )
                    data = response.json()
                    for item in data.get("files", []):
                        mime_type = item.get("mimeType", "")
                        if mime_type == "application/vnd.google-apps.folder":
                            if recursive:
                                folder_ids.append(item["id"])
                            continue
                        if not mime_type.startswith("image/"):
                            continue
                        items.append(
                            DriveItem(
                                id=item["id"],
                                name=item.get("name", ""),
                                mime_type=mime_type,
                            )
                        )
                        if len(items) >= max_items:
                            return items
                    next_page_token = data.get("nextPageToken")
                    if not next_page_token:
                        break
        return items

    async def download_file(self, file_id: str) -> tuple[bytes, str]:
        access_token = await self._refresh_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"alt": "media"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                f"{FILES_URL}/{file_id}", headers=headers, params=params
            )
            response.raise_for_status()
            content_type = response.headers.get(
                "content-type", "application/octet-stream"
            )
            return response.content, content_type
