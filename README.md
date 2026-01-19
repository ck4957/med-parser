# med-parser

Parse unstructured medication text into structured entities using a Django API and a React UI.

## Project layout

- Django backend: `med_parser/` + `med_app/`
- React frontend: `med_ui/`
- SQLite DB: `db.sqlite3`

## Backend setup (Django)

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirement.txt
   ```

3. Download the spaCy medical model (required):

   ```bash
   python -m spacy download en_core_web_sm
   ```

4. Run migrations:

   ```bash
   python manage.py migrate
   ```

5. Start the dev server:
   ```bash
   python manage.py runserver
   ```

The API is served at `http://127.0.0.1:8000/api/`.

## API endpoints

- `GET /api/` — health check.
- `POST /api/parse_medical_text` — extracts entities from medical text.

Request body:

```
{
  "medical_text": "Metformin 500mg twice daily"
}
```

Response example:

```
{
  "entities": [
     ["Metformin", "DRUG"],
     ["500mg", "DOSAGE"],
     ["twice daily", "FREQUENCY"]
  ]
}
```

## Frontend setup (React)

From the `med_ui` folder:

1. Install dependencies:

   ```bash
   npm install
   ```

2. Configure the API URL (optional):
   - Copy `.env.example` to `.env` if needed
   - Default API URL is `http://127.0.0.1:8000`
   - To change it, edit the `.env` file:
     ```
     REACT_APP_API_URL=http://127.0.0.1:8000
     ```

3. Run the dev server:
   ```bash
   npm start
   ```

The UI runs at `http://localhost:3000` and connects to the Django API.

## Features

- **Medical Text Input**: Enter unstructured medical text in a user-friendly interface
- **Entity Extraction**: Automatically extracts and categorizes medical entities:
  - Drugs/Medications
  - Dosages
  - Frequencies
  - Durations
  - Conditions
  - Procedures
- **Visual Results**: Color-coded entity cards for easy identification
- **API Health Check**: Test connection to the backend API
- **Responsive Design**: Works on desktop and mobile devices

## Notes

- CORS is enabled for local development in [med_parser/settings.py](med_parser/settings.py).
- The Django backend uses medspaCy for medical NLP processing.
- The frontend is built with React and uses Axios for API calls.
- All dependencies are listed in [requirement.txt](requirement.txt) (backend) and [med_ui/package.json](med_ui/package.json) (frontend).

## Quick Start

1. **Start Backend**:

   ```bash
   python manage.py runserver
   ```

2. **Start Frontend** (in a new terminal):

   ```bash
   cd med_ui
   npm start
   ```

3. **Access the app**: Open `http://localhost:3000` in your browser

4. **Test it**: Try parsing "Metformin 500mg twice daily for diabetes"
