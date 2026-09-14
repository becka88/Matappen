# Matappen v17

Mobilversion för GitHub Pages.

Nytt i v17:
- mycket högre kontrast på klocka, matlåda och frys i den gröna rutan
- 👍/👎 finns inne i själva receptet och sparas lokalt på mobilen
- receptbilder visas där källan tillhandahåller bild
- veckoplanen prioriterar verifierade aktuella ICA-erbjudanden från Maxi ICA Stormarknad Växjö
- en rätt visar varför den valts när den matchar ett erbjudande
- inköpslistan försöker slå ihop mängder från veckans recept
- ”Lägg till snabbt” lär sig av vilka varor som läggs till oftast
- receptkatalog + ICA-erbjudanden uppdateras automatiskt via GitHub Actions

Viktigt: Om ICA inte kan verifieras vid en körning får statusen `unavailable`. Då används inte gamla erbjudanden för att styra veckoplanen.
