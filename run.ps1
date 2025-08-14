# run.ps1 - PowerShell script to activate venv and run the app
& .\venv\Scripts\Activate.ps1
streamlit run app.py --server.port 8504
