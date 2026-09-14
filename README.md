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

## v26 – torsdag–onsdag och erbjudanden i centrum
- Matveckan går nu torsdag till onsdag.
- Familjens varannan-vecka-cykel använder en riktig torsdags-ankardag i stället för jämn/udda ISO-vecka.
- Inställningar låter familjen välja en torsdag som de vet är ankomst- eller avresedag.
- Startsida och veckovy visar tydligt om det är barnvecka eller vuxenvecka.
- ICA-erbjudanden har fått betydligt högre vikt i veckoplaneringen.
- Samma huvudingrediens används högst två gånger per matvecka, även om den är billig.
- Falukorv och annan korv räknas som samma huvudgrupp.
- "Veckans fynd" visas tydligt på både startsidan och veckovyn.

## v27 – budget från den 25:e
- Hushållsbudgeten räknas nu per period 25:e–24:e i stället för kalendermånad.
- Den 25:e börjar automatiskt en ny budgetperiod med hela månadsbudgeten tillgänglig.
- Tidigare registrerade utgifter ligger kvar i historiken men räknas bara i den period de tillhör.
- Budgetkortet visar aktuell period och att nästa period börjar den 25:e.

## v28 – alla ICA-erbjudanden + korrekt planerad budget
- ICA-skriptet sparar nu alla erbjudanden det kan läsa, inte bara produkter klassade som middagsmat.
- Ny flik "Erbjudanden" med sökning och direktknapp till inköpslistan.
- Chips, bars, snacks, dryck och andra erbjudanden kan därför läggas till manuellt.
- Valda erbjudanden med tydligt styck- eller flerpackpris räknas som planerade köp i budgeten.
- Kg-priser visas men räknas inte automatiskt som ett exakt planerat belopp utan känd vikt.
- Den tidigare missvisande texten "ICA-pris verifierat för X av Y" är borttagen.
- Budgeten skiljer på faktiskt spenderat och planerade erbjudandeköp.
- Matveckan torsdag–onsdag och riktig torsdagsankare för barnveckan ingår.
- ICA-erbjudanden prioriteras starkt i receptplaneringen, men samma huvudingrediens används högst två gånger.

## v29 – ägg + inköpsbudget
- Äggulor slås nu ihop med ägg i inköpslistan.
- Exempel: 2 ägg + 2 äggulor blir 4 ägg att köpa.
- Inköpslistan räknar om planerad budget direkt när varor läggs till, tas bort eller bockas av.
- Kända ICA-erbjudandepriser används automatiskt där mängd/enhet går att tolka säkert.
- Varor utan säkert pris räknas inte som ett påhittat belopp; budgetkortet visar hur många kvarvarande varor som faktiskt har känt pris.

## v30 – köpbara förpackningar + budget för hela inköpslistan
- Inköpslistan räknar nu om receptmängder till sådant man faktiskt köper.
- Exempel: 3 msk vitlökspulver blir 1 burk/påse, 5 dl mjölk blir 1 liter, 350 g pasta blir 1 paket och 7 ägg blir en förpackning som täcker behovet.
- Budgeten räknar hela förpackningar, inte bara gram/dl som går åt i receptet.
- ICA-erbjudandepris används när det finns och går att tolka.
- När ett aktuellt ICA-pris saknas används ett tydligt märkt ca-pris som planeringsvärde i stället för att lämna varan som 0 kr.
- Budgeten uppdateras direkt när inköpslistan ändras eller en vara bockas av.

## v31 – riktiga Maxi ICA Växjö-priser
Schablonpriser är borttagna. GitHub Action hämtar butiksspecifika produktpriser från ICA Handla Online för butik 1003571. Budgeten använder bara matchade riktiga priser eller explicit valda erbjudanden.

## v32 – UI/UX, erbjudanden, priser och budget
- UI/UX behandlas som standardkrav och tekniska förklaringar har tagits bort från huvudvyerna.
- Erbjudandehämtaren räknar rätt total på ICA-sidan och har två oberoende korttolkningar.
- Prisuppdateraren hämtar fler receptvaror, sparar flera sökord per produkt och hanterar ICA:s prisobjekt/promotioner robustare.
- Produktmatchningen är tolerant mot vardagliga ingrediensnamn och multipack.
- Veckobudgeten räknas direkt på hela aktuella inköpslistan, även avbockade varor. Månadsbudgeten visar prognos efter veckans lista.

## v33 – endast riktiga källrecept
- Alla gamla Matappen-/fallback-recept är borttagna ur `recipes.json`.
- Den automatiska receptbanken accepterar endast Recipe-data från ICA, Arla och Köket.se.
- Recept måste ha käll-URL och riktig ingredienslista från källans Recipe JSON-LD för att få visas.
- Kryddor och övriga ingredienser sparas precis som de finns i källans ingredienslista; Matappen fyller inte i eller hittar på ingredienser.
- Egna recept finns endast om familjen själv lägger in dem i appen.
- Appen har tomläge och kraschar inte om en källuppdatering tillfälligt ger 0 recept.

## v35 – inkrementell receptuppdatering
- Behåller redan verifierade källrecept.
- Kontrollerar högst 30 receptsidor per körning.
- Receptsteget har 75 sekunders egen tidsgräns.
- Hela GitHub-jobbet har 5 minuters maxgräns.
- Endast ICA, Arla och Köket accepteras som automatisk receptkälla.
