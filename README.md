# Survey Insight Assistant

Upload survey results as a CSV file and get:

- quick charts for multiple-choice and rating questions
- AI-grouped themes from open-ended answers, with real quotes for each theme
- a short summary and recommendations you can download as a report

Built with Python, Streamlit, pandas and Google Gemini.

## Why I built it

On my NTUC Starter Awards project, our team surveyed young workers and sorted the open-ended answers into themes by hand. It took hours. This app does the same first pass in under a minute, so the team can spend its time on the insights instead of the sorting.

## Run it on your computer

1. Install Python 3.10 or newer from python.org (tick "Add Python to PATH" on Windows).
2. Open a terminal in this folder and install the packages:
   ```
   pip install -r requirements.txt
   ```
3. Get a free Gemini API key at https://aistudio.google.com (click "Get API key").
4. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and paste your key in it.
   (You can also skip this and paste the key into the sidebar when the app is running.)
5. Start the app:
   ```
   streamlit run app.py
   ```
6. Your browser opens the app. Click **Try sample data**, then **Analyse with AI**.

## Put it online for free

1. Create a new public repository on GitHub and upload these files.
   Do **not** upload `.streamlit/secrets.toml`. The `.gitignore` file already keeps it out.
2. Go to https://share.streamlit.io, sign in with GitHub and click **Create app**.
3. Pick your repository, set the main file to `app.py`, and click **Deploy**.
4. In the app's **Settings > Secrets**, add:
   ```
   GEMINI_API_KEY = "your-key-here"
   ```
5. Copy your app's link (it ends in `.streamlit.app`) into your portfolio.

## Notes

- `sample_survey.csv` is made-up data for testing. It is not the real NTUC survey.
- Up to 300 answers per question are sent to Gemini, which keeps it within the free tier.
- If you see a "model not found" error, change the model name in the sidebar (for example to `gemini-2.5-flash`).
