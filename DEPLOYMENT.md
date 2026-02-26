# Talk to Krishna - Deployment Guide

This document lists the step-by-step process for deploying the application into a production environment using a highly decoupled architecture:
- **Backend (API Server):** Deployed to **Render** 
- **Frontend (React Web App):** Deployed to **Vercel**

---

## 🏗️ 1. Prepare and Push Your Code

1. Before deploying, ensure all of your recent changes are pushed to a remote **GitHub** repository.
2. If your repository is currently private, this ensures your credentials and databases stay secure while Vercel and Render are granted access.

---

## 🔙 2. Deploy Backend on Render (Free Tier Friendly)

The API server runs entirely on Python using `Flask`, `Gunicorn`, and `Edge-TTS` for real-time speech synthesis.

1. **Log in to [Render](https://render.com).**
2. In the Render Dashboard, click **New +** and select **Blueprint**.
3. Connect your GitHub repository containing the Codebase.
4. Render will automatically detect the `render.yaml` file located in the root directory.
    - *The `render.yaml` magically configures the entire API Server, sets up Gunicorn, provisions a Persistent Disk for your SQLite `users.db`, and queues up the startup scripts.*
5. Render will ask you to provide **Environment Variables** securely via its dashboard. Ensure you click **Advanced** under the web service and provide the following strictly:
    - `GROQ_API_KEY`: Enter your Groq API secret (`gsk_...`).
    - `FRONTEND_URL`: Leave it blank for now. We will return to update this *after* the Frontend is deployed! (This restricts cross-origin request abuse).
6. Click **Apply**.
7. Wait ~2-5 minutes as Render installs dependencies, generates embeddings (`create_embeddings.py`), and binds the server to port `5000`.
8. Once the status shows **Live**, copy your API URL. It will look like: `https://talk-to-krishna-api-xxxx.onrender.com`.

---

## 🌅 3. Deploy Frontend on Vercel

The frontend is a beautifully designed React App using modern browser APIs for voice processing.

1. **Log in to [Vercel](https://vercel.com/new).**
2. Click **Add New** $\rightarrow$ **Project**.
3. Re-select the identical GitHub repository.
4. In the **Framework Preset** dropdown, Vercel should auto-detect **Create React App**.
5. In the **Root Directory** field, click Edit and select the `website/krishna-react` folder.
6. Expand the **Environment Variables** tab and vividly importantly add:
    - **Key:** `REACT_APP_API_URL`
    - **Value:** `https://talk-to-krishna-api-xxxx.onrender.com` *(Paste the Render URL from Step 2. Do NOT include a trailing slash.)*
7. Click **Deploy**.
8. Wait ~1 minute as Vercel compiles the React optimized build.
9. Upon success, you will receive a production Domain URL (e.g. `https://talk-to-krishna.vercel.app`).

**Note:** The `/vercel.json` file inside the frontend folder takes care of SPA (Single Page App) routing ensuring page refreshes do not result in `404 Not Found` errors!

---

## 🔗 4. Final Security Check (CORS)

If we do not explicitly link both platforms back to each other, the browser will angrily block the connections due to "CORS errors". Let's finalize the handshake:

1. Copy your new Vercel App Domain (e.g., `https://talk-to-krishna.vercel.app`).
2. Head back to your **Render Dashboard**.
3. Open the `talk-to-krishna-api` backend Web Service.
4. Navigate to **Environment $\rightarrow$ Environment Variables**.
5. Edit the variable named `FRONTEND_URL` and enter the copied Vercel App Domain.
6. Click **Save Changes**. This gracefully reloads the API server safely validating your Vercel web application exactly.

You now have a fully scalable, enterprise-grade deployed application seamlessly serving production Neural Audio!
