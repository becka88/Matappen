# Matappen v24

Samlad version efter genomgång av tidigare prototyper.

- Barn/vuxen-status per dag, med torsdagsbyte och inställning för ankomst/avresa.
- Portionsmål: barn hemma = 4 middagar + 2 lunchlådor (6 port), vuxenkväll = 2 middagar + 2 lunchlådor (4 port).
- Veckoplanering väljer en hel varierad vecka. Samma huvudråvara får kraftigt repetitionsstraff; ICA-erbjudanden är bonus, inte styrning.
- Egna recept ingår i samma planering och erbjudandematchning.
- Stabilt recept-ID används för 👍/👎.
- Inköpsmängder skalas efter dagens portionsmål, slås ihop, vatten filtreras bort och "har hemma" återställs per vecka.
- Instruktionsrader filtreras; kända hemmagjorda delrecept kan expanderas till faktiska ingredienser.
- Budget: 12 000 kr/månad och 1 600 kr/vecka som standard, med registrering av faktisk matbutik/hämtmat.
- ICA-erbjudandepriser visas där de kan verifieras. Appen hittar inte på en totalprisprognos när ordinarie onlinepriser saknas.
- Receptsökning söker i namn, ingredienser och taggar.
- Daglig receptuppdaterare behåller katalogen och försöker komplettera saknade originalbilder från receptsidan.

Obs: exakt vanlig onlinepris-matchning för hela ICA-korgen kräver en stabil verifierad produktkälla. v24 visar därför endast verifierade kampanjpriser och faktisk registrerad kostnad tills sådan källa är bekräftad.

## v25 – UX/UI-genomgång
- Startsidan är renare: dagens middag, budgetläge, ICA-status och en kompakt länk till inköpslistan.
- Ingen snabb-inmatning på startsidan.
- Inköpslistan har nu "Lägg till vara" högst upp, följt av smarta snabbval.
- Snabbvalen lär sig vilka manuella varor som används oftast.
- Tydligare hierarki, större tryckytor, jämnare typografi, färre visuella element och mer konsekventa kort/knappar.
- Budgeten visas med tydlig progress och "kvar"-belopp.
- Receptbanken har renare sök- och filterlayout.
- Befintliga lokala inställningar och preferenser från v24 behålls.
