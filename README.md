# Matappen v14 – levande receptkatalog

V14 ersätter det fasta receptbiblioteket med en dynamisk katalog.

- ICA, Arla och Köket används som levande upptäcktskällor.
- Katalogen lagras lokalt i SQLite och fylls på/uppdateras.
- Automatisk refresh när katalogen är äldre än 24 h.
- Manuell "Uppdatera" i appen.
- Sök går mot den lokala, växande katalogen.
- Externa recept visar metadata/ingredienser och länkar till originalet för full tillagning.
- De 44 egna Matappen-recepten ligger kvar som fallback.

## Drift
Miljövariabler:
- APP_PASSWORD
- SESSION_SECRET

Installera:
pip install -r requirements.txt

Starta:
uvicorn app:app --host 0.0.0.0 --port $PORT
