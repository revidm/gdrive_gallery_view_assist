# Changelog

## 0.4.3

- Add image cache and prefetch options.
- Remove unused `size` option.

## 0.4.2

- Remove unused `size` option from config.

## 0.4.1

- Rename add-on to GoogleDrive Gallery for View Assist.
- Update slug to `gdrive_gallery_view_assist`.

## 0.4.0

- Remove Google Photos support.
- Keep Drive-only functionality.

## 0.4.5

- Add Drive recursion, exclude patterns, cache limits, and daily shuffle.

## 0.4.6

- Rename OAuth env vars to GOOGLE_*.

## 0.4.7

- Add /health endpoint with cache and index metrics.

## 0.4.8

- Return human-readable last refresh time in /health.

## 0.4.9

- Update GitHub URLs for new username.

## 0.5.1

- Add resize profiles with `/image/{profile}` endpoints.

## 0.5.2

- Fix add-on schema for resize profiles.

## 0.5.3

- Mark secrets as password fields and add friendly labels.

## 0.5.4

- Remove unused labels and descriptions from config.

## 0.5.5

- Add add-on icon.

## 0.5.6

- Fix resize profile caching and prefetch behavior.

## 0.5.7

- Report /data storage usage in /health.

## 0.5.8

- Log token refresh error responses from Google.
