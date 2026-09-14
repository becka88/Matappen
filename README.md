# Matappen v15 – bara GitHub

Ingen Render, ingen Streamlit-server och inget du behöver installera lokalt.

## Så fungerar det
- GitHub Pages visar själva mobilappen.
- GitHub Actions kör `scripts/update_recipes.py` varje dygn.
- Scriptet letar efter recept hos ICA, Arla och Köket.
- Receptmetadata läggs i `recipes.json`.
- Externa recept länkar till originalkällan för full tillagning.
- De egna Matappen-recepten ligger kvar som reserv.

## Starta sidan
I GitHub:
1. Settings
2. Pages
3. Under Build and deployment: välj `Deploy from a branch`
4. Branch: `main`
5. Folder: `/ (root)`
6. Save

OBS: GitHub Pages är en publik webbplats. Lägg inte känsliga uppgifter i appen.
På GitHub Free kräver Pages normalt ett publikt repo. Privata repo stöds på vissa betalda GitHub-planer.

## Testa receptuppdateringen
Actions → Uppdatera recept → Run workflow.
