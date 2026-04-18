# Deployment Instructions - Cloud To-Do List

This project is a full-stack FastAPI application that serves its own frontend as a Single Page Application (SPA).

## 1. MongoDB Atlas Setup (Cloud Database)

1.  Log in to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2.  Create a new Cluster (Shared/Free tier).
3.  Go to **Database Access** and create a user (keep the username and password).
4.  Go to **Network Access** and add your IP address (or `0.0.0.0/0` for testing).
5.  Go to **Clusters** > **Connect** > **Connect your application**.
6.  Copy the connection string (it looks like `mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0`).

## 2. Local Setup & Testing

1.  Open your terminal in the project directory.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Create a `.env` file and add your MongoDB URL:
    ```env
    MONGODB_URL=your_mongodb_connection_string_here
    ```
4.  Run the application:
    ```bash
    python main.py
    ```
5.  Open your browser at `http://localhost:8000`.

## 3. Deployment on Render (Backend + Frontend)

Setting it up on Render is the simplest way to deploy both the API and the UI at once.

1.  Create a new **Web Service** on [Render](https://render.com/).
2.  Connect your GitHub/GitLab repository.
3.  Set the following configuration:
    - **Runtime**: `Python`
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4.  Go to **Environment Variables** and add:
    - `MONGODB_URL`: (Your MongoDB Atlas connection string)
5.  Click **Deploy Web Service**.

## 4. Deployment on Vercel (Frontend Only - Optional)

If you strictly want the frontend on Vercel (connected to the Render API):

1.  Edit `index.html` and change `const API_BASE_URL = window.location.origin;` to `const API_BASE_URL = 'https://your-render-app-url.onrender.com';`.
2.  Push to GitHub.
3.  Import the repo into [Vercel](https://vercel.com/dashboard).
4.  Set the Framework Preset to **Other**.
5.  Deploy.

> [!IMPORTANT]
> Ensure CORS in `main.py` allows your Vercel domain if you choose separate deployment. Currently, it is set to `["*"]` which allows all, but in production, you might want to specify your Vercel URL.
