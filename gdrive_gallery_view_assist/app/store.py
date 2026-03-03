import asyncio
import random
import time
from dataclasses import dataclass
import fnmatch
from datetime import date

from .google_drive import GoogleDriveClient, DriveItem


@dataclass
class CachedDriveItems:
    items: list[DriveItem]
    fetched_at: float


@dataclass
class CachedImage:
    content: bytes
    content_type: str
    fetched_at: float


class ItemStore:
    def __init__(
        self,
        drive_client: GoogleDriveClient,
        drive_folder_id: str,
        drive_include_shared: bool,
        drive_recursive: bool,
        exclude_patterns: str,
        cache_images: bool,
        cache_max_items: int,
        cache_max_mb: int,
        prefetch_next: bool,
        daily_shuffle: bool,
        refresh_interval_minutes: int,
        max_items: int,
        mode: str,
    ):
        self._drive_client = drive_client
        self._drive_folder_id = drive_folder_id
        self._drive_include_shared = drive_include_shared
        self._drive_recursive = drive_recursive
        self._exclude_patterns = [
            pattern.strip()
            for pattern in exclude_patterns.split(",")
            if pattern.strip()
        ]
        self._cache_images = cache_images
        self._cache_max_items = cache_max_items
        self._cache_max_mb = cache_max_mb
        self._prefetch_next = prefetch_next
        self._daily_shuffle = daily_shuffle
        self._refresh_interval = refresh_interval_minutes * 60
        self._max_items = max_items
        self._mode = mode
        self._drive_cache: CachedDriveItems | None = None
        self._image_cache: dict[str, CachedImage] = {}
        self._cache_bytes = 0
        self._prefetch_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._index = 0

    async def _refresh(self) -> CachedDriveItems:
        if not self._drive_folder_id:
            raise RuntimeError("Missing drive_folder_id")
        items = await self._drive_client.list_folder_images(
            folder_id=self._drive_folder_id,
            page_size=min(self._max_items, 1000),
            max_items=self._max_items,
            include_shared=self._drive_include_shared,
            recursive=self._drive_recursive,
        )
        filtered = self._filter_items(items)
        cache = CachedDriveItems(items=filtered, fetched_at=time.time())
        self._drive_cache = cache
        self._index = 0
        return cache

    async def next_item(self) -> DriveItem | None:
        items = await self._get_drive_items()
        if not items:
            return None
        if self._daily_shuffle:
            items = self._daily_shuffle_items(items)
        if self._mode == "sequential":
            item = items[self._index % len(items)]
            self._index += 1
            if self._prefetch_next:
                self._schedule_prefetch(items)
            return item
        item = random.choice(items)
        if self._prefetch_next:
            self._schedule_prefetch(items)
        return item

    async def get_image(self, item: DriveItem) -> CachedImage:
        if self._cache_images:
            cached = self._image_cache.get(item.id)
            if cached:
                return cached
        content, content_type = await self._drive_client.download_file(item.id)
        cached = CachedImage(
            content=content, content_type=content_type, fetched_at=time.time()
        )
        if self._cache_images:
            self._add_to_cache(item.id, cached)
        return cached

    async def _get_drive_items(self) -> list[DriveItem]:
        async with self._lock:
            if not self._drive_cache:
                await self._refresh()
            if not self._drive_cache:
                return []
            if time.time() - self._drive_cache.fetched_at > self._refresh_interval:
                await self._refresh()
            if not self._drive_cache:
                return []
            return self._drive_cache.items

    async def get_status(self) -> dict:
        async with self._lock:
            item_count = len(self._drive_cache.items) if self._drive_cache else 0
            fetched_at = self._drive_cache.fetched_at if self._drive_cache else None
            cache_items = len(self._image_cache)
            cache_bytes = self._cache_bytes
        return {
            "item_count": item_count,
            "last_refresh": fetched_at,
            "last_refresh_iso": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(fetched_at)
            )
            if fetched_at
            else None,
            "cache_items": cache_items,
            "cache_bytes": cache_bytes,
        }

    async def _prefetch(self, items: list[DriveItem]) -> None:
        if not items:
            return
        if self._mode == "sequential":
            next_item = items[self._index % len(items)]
        else:
            next_item = random.choice(items)
        if self._cache_images and next_item.id in self._image_cache:
            return
        try:
            await self.get_image(next_item)
        except Exception:
            return

    def _schedule_prefetch(self, items: list[DriveItem]) -> None:
        if self._prefetch_task and not self._prefetch_task.done():
            return
        self._prefetch_task = asyncio.create_task(self._prefetch(items))

    def _filter_items(self, items: list[DriveItem]) -> list[DriveItem]:
        if not self._exclude_patterns:
            return items
        filtered: list[DriveItem] = []
        for item in items:
            name = item.name or ""
            if any(
                fnmatch.fnmatch(name, pattern) for pattern in self._exclude_patterns
            ):
                continue
            filtered.append(item)
        return filtered

    def _daily_shuffle_items(self, items: list[DriveItem]) -> list[DriveItem]:
        seed = date.today().isoformat()
        seeded = list(items)
        random.Random(seed).shuffle(seeded)
        return seeded

    def _add_to_cache(self, item_id: str, cached: CachedImage) -> None:
        size_bytes = len(cached.content)
        if self._cache_max_mb > 0:
            max_bytes = self._cache_max_mb * 1024 * 1024
            while self._cache_bytes + size_bytes > max_bytes and self._image_cache:
                self._evict_one()
        if self._cache_max_items > 0:
            while len(self._image_cache) >= self._cache_max_items and self._image_cache:
                self._evict_one()
        self._image_cache[item_id] = cached
        self._cache_bytes += size_bytes

    def _evict_one(self) -> None:
        item_id, cached = self._image_cache.popitem()
        self._cache_bytes = max(self._cache_bytes - len(cached.content), 0)
