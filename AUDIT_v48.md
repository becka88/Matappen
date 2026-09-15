# v48
- Fixar ICA-prisparsern för `decoratedProducts` när ICA returnerar en dictionary/map i stället för en lista.
- Parsern går nu rekursivt igenom listor, wrappers och id-mappar och plockar endast produktliknande objekt med identitet + pris.
- Behåller v47:s dublett-/varumärkesfixar och alla tidigare ändringar.
