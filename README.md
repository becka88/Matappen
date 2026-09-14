# Matappen v6

Matappen v6 lägger till automatisk ICA-kontroll för **Maxi ICA Stormarknad Växjö**.

## Så fungerar ICA-delen
1. Kontrollerar ICA:s officiella erbjudandesida för butik `1003571`.
2. Kontrollerar även butikens publika onlineproduktdata med riktade sökningar efter bl.a. kyckling, färs, korv, fläsk och högrev.
3. Data cachelagras i högst 6 timmar för att inte belasta ICA i onödan.
4. Endast erbjudanden som faktiskt kan läsas markeras som verifierade.
5. Om ICA tillfälligt inte går att nå används en sparad reservkopia, tydligt märkt som sådan.
6. Veckoplanen premierar recept vars kött matchar ett aktuellt verifierat erbjudande.

## Viktigt
ICA:s publika sida kan visa ett större totalt antal erbjudanden än de produktkort som finns i server-renderad HTML. Matappen kombinerar därför två publika ICA-källor, men lovar inte 100 % täckning om ICA ändrar sina gränssnitt.

## Kör
```bash
pip install -r requirements.txt
streamlit run app.py
```

För nästa produktionssteg behövs publicering + permanent delad datalagring för Snabblistan/familjesynk.
