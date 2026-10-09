# Namit PDF Locker — Complete Web App

## Run locally
1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Run `pip install -r requirements.txt`
4. Run `python app.py`
5. Visit http://127.0.0.1:7860

## Features
- Six-question quiz with correct answers stored internally.
- Quiz answer key and binary code are not printed on screen.
- After the quiz, asks for the hidden binary unlock code.
- Lets you upload a PDF or paste a direct public PDF URL.
- Encrypts the PDF with the password you choose and downloads a locked copy.

## Public hosting
Upload these files to a Python/Flask host and set the start command to:
`gunicorn app:app`
The hosting service should provide a public HTTPS URL to share.

## Notes
- Direct links must point to the actual PDF file, not a preview page.
- PDFs are processed in memory, but a hosted server receives the file. Avoid confidential files on a third-party host unless you trust it.
- Set a strong random `SECRET_KEY` environment variable before public deployment.
- This is a quiz/puzzle gate, not strong authentication; source-code access reveals the internal answers/code.
