# GenVoice Care

GenVoice Care is an AI-assisted voice check-in system designed to help older adults share how they are doing and keep caregivers informed. It combines a senior-facing Android app, a caregiver dashboard, and a Python API.

## What it does

- Guides a senior through a multi-question wellness conversation.
- Adapts follow-up questions to responses such as loneliness, discomfort, or a request for help.
- Detects configured urgent-symptom phrases and routes them through an urgent workflow.
- Offers voice interaction in the senior app and saves conversation messages for later review.
- Produces a conversation summary, including an optional final note from the senior, for the caregiver dashboard.
- Refreshes recent dashboard conversations periodically to show new check-ins.

GenVoice Care is an MVP wellness support tool. It does not diagnose or replace professional medical care or local emergency services. In an emergency, contact local emergency services.

## Project structure

```text
Code-coding part/
├── backend/               Python API, conversation flow, summaries, and emergency routes
├── caregiver-dashboard/   React and Vite caregiver dashboard
├── caregiver-app/         Android caregiver app
└── senior-app/            Android senior voice check-in app
```

## Requirements

- Python 3.10 or later
- Node.js and npm
- Android Studio with an Android SDK for building the Android apps
- A Groq API key only if you want to enable the optional Groq-powered responses

## Run the backend

From the repository root in PowerShell:

```powershell
cd "Code-coding part\backend"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python api_blueprint.py
```

Set the required environment values in your local `.env` file before enabling external AI features. Never commit `.env`, API keys, local databases, or real care records.

The API starts on port `8000`. Its health endpoint is `/api/v1/health`.

## Run the caregiver dashboard

Open a second PowerShell window:

```powershell
cd "Code-coding part\caregiver-dashboard"
npm install
npm run dev
```

Configure the dashboard API base URL in its local environment file to point to the backend, then open the local URL printed by Vite.

## Build the Android apps

Open `Code-coding part\senior-app` or `Code-coding part\caregiver-app` in Android Studio and allow Gradle sync to finish. To build a debug APK from PowerShell:

```powershell
cd "Code-coding part\senior-app"
.\gradlew.bat assembleDebug
```

The debug APK is created under `app\build\outputs\apk\debug\`. Repeat from the caregiver app folder to build that app.

## Data and privacy

The backend uses SQLite for local persistence. Keep production data and credentials out of source control. Use a protected deployment environment for API keys and restrict access to conversation transcripts and caregiver summaries.
