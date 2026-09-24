# Hotel Booking

A responsive React Native/Expo hotel discovery and booking-request application built with Expo SDK 57.

## Features

- Create an account and log in with validated credentials.
- Persist users in an on-device SQLite database.
- Restore the authenticated session after restarting the app.
- Log out from the Home screen.
- Search hotels by name or location.
- Sort by recommended order, price, or guest rating.
- Display filtered hotels on an interactive map.
- Send a validated booking request for a selected hotel.
- Review the complete request on a confirmation screen.
- Adapt layouts for narrow phones, larger phones, tablets, and orientation changes.

## Authentication and local database

The demo uses SQLite because it runs directly in Expo Go and does not require a separately hosted API or PostgreSQL server.

The `users` table stores:

- First and last name
- A case-insensitive unique email address
- A random password salt
- A PBKDF2-derived password hash
- The account creation timestamp

Passwords are never stored as plain text. SQL values are passed as query parameters rather than interpolated into statements. The active user ID is persisted with Expo SecureStore on Android and iOS.

This is device-local authentication intended for a portfolio demo. Accounts do not synchronize between devices. A production version should move user records and password verification to a server-side authentication API backed by PostgreSQL or a managed identity provider.

## Test the authentication flow

1. Launch the app and select **Create an account**.
2. Enter a name, a valid email address, and a password containing at least eight characters, one letter, and one number.
3. Submit the form. The app creates the SQLite record and opens the authenticated Home screen.
4. Select **Log out** in the Home header.
5. Log in again with the same email and password.
6. Close and reopen the app to verify that the secure session is restored.

## Launch with Expo Go

### 1. Install Expo Go

Install the current **Expo Go** app from Google Play on Android or the App Store on iPhone. This project uses Expo SDK 57.

### 2. Open the project directory

```bash
cd /home/olti/Desktop/Projects/Personal_Projects/hotel-booking-app
```

The old `ReactNative_PR/reactnative_pr` path no longer exists. If the editor still shows tabs from that location, close them and open the `hotel-booking-app` directory instead.

### 3. Install dependencies

```bash
npm install
```

You normally need to do this only the first time or after `package.json` changes.

### 4. Put both devices on the same network

Connect the phone and computer to the same Wi-Fi network. Temporarily disable a VPN if it prevents the phone from reaching the computer.

### 5. Start Expo

```bash
npm start
```

Keep the terminal open. Wait until it says `Metro waiting on` and displays a QR code.

### 6. Open the app

- **Android:** Open Expo Go, choose **Scan QR Code**, and scan the terminal QR code.
- **iPhone:** Scan the QR code with the Camera app, then tap the Expo Go notification.

If Expo Go asks you to sign in, use the same Expo account in Expo Go and the terminal:

```bash
npx expo login
```

Press `r` in the Metro terminal to reload or `m` to open the developer menu.

### 7. Stop Expo

Press `Ctrl+C` in the Metro terminal.

For later launches:

```bash
cd /home/olti/Desktop/Projects/Personal_Projects/hotel-booking-app
npm start
```

### Troubleshooting

If the phone cannot connect to Metro, use tunnel mode:

```bash
npx expo start --tunnel
```

If Metro has stale cached data:

```bash
npx expo start --clear
```

## Booking payload

A valid request is assembled in this form:

```json
{
  "hotelId": 3,
  "checkIn": "2026-10-01",
  "checkOut": "2026-10-07",
  "adults": 2,
  "children": 0
}
```

Booking requests are currently stored in memory for the app session. `submitBooking` in `src/context/BookingContext.js` is the integration point for a production reservation API.
