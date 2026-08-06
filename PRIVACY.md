# Privacy Policy for PhotoBridge

**Last updated:** August 6, 2026

PhotoBridge is a local network application. This policy explains exactly what data the application does — and does not — handle.

## Summary

PhotoBridge does not collect, transmit, or store any personal data on external servers. The application runs entirely as a local web server on your own Windows computer and is only accessible to devices on the same local Wi-Fi network as that computer.

## What PhotoBridge does NOT do

- It does not create user accounts or require sign-in.
- It does not use analytics, telemetry, crash reporting, or advertising SDKs of any kind.
- It does not upload your photos, videos, or any other file to the cloud or to any third-party service.
- It does not share data with the developer, Microsoft, or any other party.
- It does not require or use an internet connection to function — it operates entirely over your local Wi-Fi network.

## What data stays local, and where

| Data | Where it's stored | Leaves your network? |
|---|---|---|
| Photos & videos you browse | Read directly from the folder you configure on your own computer | No |
| Optional Access PIN | Stored locally as a salted PBKDF2-HMAC-SHA256 hash under `%LOCALAPPDATA%\PhotoBridge` — never in plain text | No |
| Favorites you mark | Stored locally under `%LOCALAPPDATA%\PhotoBridge` | No |
| App configuration (`config.json`) and logs (`app.log`) | Stored locally under `%LOCALAPPDATA%\PhotoBridge` | No |
| Thumbnail cache | Stored locally under `%LOCALAPPDATA%\PhotoBridge`, automatically cleared on server shutdown/launch | No |

PhotoBridge stores this data under your Windows user profile (`%LOCALAPPDATA%\PhotoBridge`) rather than inside the installation folder, so that it can write configuration, logs, and cache safely without needing elevated permissions to `Program Files`. This is a local filesystem location only — nothing in this folder is transmitted anywhere.

## Network access and firewall

To let other devices on your Wi-Fi network reach PhotoBridge, the app requests a one-time Windows Firewall exception (via a UAC prompt) for:
- **TCP port 8000** — the local web server that phones, tablets, TVs, and other laptops connect to.
- **UDP port 5353** — used for mDNS, so the app can be reached at a friendly `http://<device>.local:8000` address instead of a numeric IP.

Both exceptions are scoped to your **private network profile** only, are fully reversible from the Control Center, and are removed automatically on uninstall. These rules only allow inbound connections on your local network — they do not expose PhotoBridge to the public internet.

## Access PIN and rate limiting

If you choose to set an Access PIN from the Control Center sidebar:
- It is never stored or transmitted in plain text — only a salted PBKDF2-HMAC-SHA256 hash is kept, locally, on your computer.
- Repeated failed PIN attempts from the same device are automatically rate-limited, and that device is temporarily locked out after 5 failures.
- The PIN can only be configured or changed directly from the host computer's Control Center — it cannot be set or reset remotely.

## How connected devices are treated

When you connect a phone, tablet, TV, or other device on your Wi-Fi network to PhotoBridge through a browser:
- Server responses are sent with `Cache-Control: private, no-store, must-revalidate` headers, instructing the connecting browser not to write any media to that device's local storage.
- Access can optionally be restricted with the PIN described above.
- All access is limited to devices on the same local network as the host computer — PhotoBridge does not expose itself to the public internet.

## Children's privacy

PhotoBridge does not knowingly collect any personal data from anyone, including children, because it does not collect personal data from anyone at all.

## Changes to this policy

If PhotoBridge's functionality changes in a way that affects this policy (for example, if a future version adds an optional cloud-sync feature), this document will be updated and the "Last updated" date above will reflect the change.

## Contact

Questions about this policy or the application can be raised via the project's GitHub repository:
https://github.com/animesh2411/my-photos-app
