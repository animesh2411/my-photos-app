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
| Optional Access PIN | Stored locally on your computer | No |
| Favorites you mark | Stored locally on your computer | No |
| Thumbnail cache | Stored locally (`backend/.thumbcache/`), automatically purged on server shutdown/launch | No |

## How your phone is treated

When you connect a phone (or any other device) on your Wi-Fi network to PhotoBridge through a browser:
- Server responses are sent with `Cache-Control: private, no-store, must-revalidate` headers, which instruct the connecting browser not to write any media to that device's local storage.
- Access can optionally be restricted with a PIN that you set during first-time setup, stored only on the host computer.
- All access is limited to devices on the same local network as the host computer — PhotoBridge does not expose itself to the public internet.

## Children's privacy

PhotoBridge does not knowingly collect any personal data from anyone, including children, because it does not collect personal data from anyone at all.

## Changes to this policy

If PhotoBridge's functionality changes in a way that affects this policy (for example, if a future version adds an optional cloud-sync feature), this document will be updated and the "Last updated" date above will reflect the change.

## Contact

Questions about this policy or the application can be raised via the project's GitHub repository:
https://github.com/animesh2411/my-photos-app
