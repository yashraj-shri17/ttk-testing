# Render Deployment Guide (Azure TTS Update)

This guide outlines the necessary environment variables and configuration changes required to deploy the updated "Talk to Krishna" app with Azure Hindi TTS support on Render.

## 1. Environment Variables
You must add the following variables in the **Render Dashboard -> Environment** section of your Web Service.

| Variable | Value | Description |
| :--- | :--- | :--- |
| `AZURE_SPEECH_KEY` | `9W7IkVXD78...` | Your Azure Speech Service primary key. |
| `AZURE_SPEECH_REGION` | `centralindia` | The region of your Azure Speech resource. |
| `FRONTEND_URL` | `https://your-app.onrender.com` | Base URL of your deployed frontend (to allow CORS). |
| `DATABASE_URL` | *(your connection string)* | Ensure your PostgreSQL database is linked correctly. |
| `GROQ_API_KEY` | *(your groq key)* | Used for LLM answers and Whisper transcription. |

> [!IMPORTANT]
> Ensure the `AZURE_SPEECH_KEY` does not have any typos (e.g., lowercase 'l' vs capital 'I'). The key we fixed today starts with `9W7I...`.

## 2. Infrastructure Requirements (Linux)
The Azure Speech SDK runs on Linux on Render but requires certain shared system libraries. 

### A. System Dependencies (If using native environment)
If your Python build fails or the server crashes with a "Shared library not found" (e.g., `libasound2`, `libssl`), you may need to specify system dependencies. On Render, you can use a **Custom Build Command** or a `Dockerfile`.

**If using a custom build command:**
```bash
# Example Build Command in Render Dashboard
apt-get update && apt-get install -y libasound2 libssl3 && pip install -r requirements.txt
```
*(Note: Most standard Render Python environments already satisfy these).*

### B. Python Version
The `azure-cognitiveservices-speech` library is compatible with Python 3.8 through 3.12. Ensure your Render environment is set to `PYTHON_VERSION=3.10` or higher.

## 3. Frontend Deployment
The frontend (`krishna-react`) must be rebuilt to include the updated `VoiceChat.js` logic.

1. **Rebuild Command**: `npm run build`
2. **Environment**: Ensure `REACT_APP_API_BASE_URL` in your frontend environment variables points to your backend URL (no trailing slash).

## 4. Troubleshooting
- **Silence on iPhone**: Ensure the physical "Silent Mode" switch on the phone is OFF.
- **Madhur Voice Fallback**: If you hear the Madhur voice on Render, check the backend logs. It usually means `AZURE_SPEECH_KEY` is incorrect or missing.
- **Audio Lag**: Azure synthesis is generally faster than Edge TTS. If there is a lag, it's usually network latency between Render and the Azure `centralindia` region.
