from fastapi import FastAPI, Response
import uvicorn

from .config import load_settings
from .google_drive import GoogleDriveClient, DriveItem
from .store import ItemStore


settings = load_settings()
drive_client = GoogleDriveClient(
    client_id=settings.client_id,
    client_secret=settings.client_secret,
    refresh_token=settings.refresh_token,
)
store = ItemStore(
    drive_client=drive_client,
    drive_folder_id=settings.drive_folder_id,
    drive_include_shared=settings.drive_include_shared,
    drive_recursive=settings.drive_recursive,
    exclude_patterns=settings.exclude_patterns,
    cache_images=settings.cache_images,
    cache_max_items=settings.cache_max_items,
    cache_max_mb=settings.cache_max_mb,
    prefetch_next=settings.prefetch_next,
    daily_shuffle=settings.daily_shuffle,
    refresh_interval_minutes=settings.refresh_interval_minutes,
    max_items=settings.max_items,
    mode=settings.mode,
)

app = FastAPI()


@app.get("/")
async def root() -> dict:
    return {
        "status": "ok",
        "mode": settings.mode,
        "drive_folder_id": settings.drive_folder_id,
        "max_items": settings.max_items,
    }


@app.get("/health")
async def health() -> dict:
    status = await store.get_status()
    return {
        "status": "ok",
        "drive_folder_id": settings.drive_folder_id,
        "refresh_interval_minutes": settings.refresh_interval_minutes,
        "item_count": status["item_count"],
        "last_refresh": status["last_refresh_iso"],
        "cache_items": status["cache_items"],
        "cache_bytes": status["cache_bytes"],
    }


@app.get("/image")
async def image() -> Response:
    item = await store.next_item()
    if not item:
        return Response(content="No images found", status_code=404)
    if not isinstance(item, DriveItem):
        return Response(content="Invalid drive item", status_code=500)
    cached = await store.get_image(item)
    return Response(content=cached.content, media_type=cached.content_type)


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=settings.port)


if __name__ == "__main__":
    main()
