# Tervezési megjegyzések és a nyitott kérdésekre vonatkozó döntések

- A naplóban szereplő sorszámok az első programutasítástól számítandók. Ez a térképet követő első sor, amelynek sorszáma 1.
- Egy naplóbejegyzés elemei: sorszám, valamint opcionálisan az API neve, a kiértékelt argumentum, a visszatérési érték és a hibakód. Az API-nevek: `isThere`, `step forward`, `turn by`, `mine here`, `print`.
- A nem API-hívásból származó hibák naplóformátuma: `<sorszám> <ERROR_CODE>`. Hiba esetén a napló `EOR` bejegyzés nélkül zárul.
- A kifejezések egyszerűek, nem ágyazhatók egymásba: operandus, `not operandus`, `isThere operandus`, illetve `operandus operátor operandus`.
- Az operandusok kiértékelése balról jobbra történik, az operátor pedig ezt követően ellenőrzi a típusokat. Nincs rövidzáras kiértékelés.
- A `step forward n` utasítás mezőről mezőre mozgatja a robotot. Fal esetén a robot az utolsó szabad mezőn marad.
- Hibás típusú vagy megengedett tartományon kívüli API-argumentum esetén (például logikai érték, negatív szám, vagy az `isThere` esetén 0 és 2 közötti tartományon kívüli érték) a hibakód: `E_BAD_ARG`.
- Az aritmetikai műveletek eredményeire nem történik tartományellenőrzés. A 0 és 100 közötti tartományon kívüli literálok szintaktikai hibát okoznak.
- Szintaktikai hiba esetén a naplófájl üres marad, `-q` módban pedig a program 2-es kilépési kóddal áll le.
- A végrehajtott sorok számlálója az `else` utasításokat és a `while` minden egyes feltételvizsgálatát is tartalmazza. A korlátot központilag, a `MAX_EXECUTED_LINES` konstans határozza meg.
- A fejlesztői környezetben nem futottak le a valódi pytest-, Ruff- és mypy-eszközök (nem volt hálózati hozzáférés). A tesztelés egy minimális helyettesítő futtatóval történt; a valódi eszközöket helyben is futtatni kell.

## Döntések a 6–8. fejlesztési fázishoz

- A blokkok fája (`BlockProgram`) az egyetlen szerkeszthető állapot. A forráskódnézet ebből generálódik, és csak olvasható.
- Az operandusok egyetlen tokenből állnak (szám, `true`/`false` vagy változónév). Egy olyan feltételt, mint az `a = 1`, először változóba kell menteni. Ha egy betöltött fájlban az `if` vagy `while` feltétele kifejezés, a betöltés figyelmeztető üzenettel elutasításra kerül, mert a blokkszerkesztő nem tudja ezt a formát ábrázolni.
- Szerkesztés közben megengedett az üres vezérlőblokk. Futtatásakor azonban szintaktikai hiba keletkezik.
- A beágyazási korlát (3 szint) csak a vezérlőblokkokra vonatkozik. Az `else` az azt tartalmazó `if` blokkal azonos szintű.
- A futásvezérlést a grafikus felület szálában működő Qt-időzítő végzi (`RunController`). Egy futás legfeljebb 1000 sort dolgozhat fel, így külön munkaszál nélkül is válaszkész marad a grafikus felület. A sebességcsúszka értéke 1 és 10 közötti.
- A hibakereső (`DebugSession`) minden programsor előtt megállítja a végrehajtást. Az aktuális sor kiemelve jelenik meg a forráskódnézetben és a blokkfában. A blokkok és a változók szerkeszthetősége, illetve olvashatósága ennek megfelelően korlátozott.
- A grafikus felülethez tartozó naplófájl a futás befejezésekor íródik ki, amennyiben a parancssorban megadtak kimeneti útvonalat.
- Nem ellenőrzött: a PySide6 nem volt telepítve a fejlesztői környezetben. A felületi fájlok szintaktikailag lefordulnak, de az alkalmazást nem indították el. Az első grafikus indításkor hibák merülhetnek fel. A manuális robotvezérlés ekkor még nem készült el (9. fázis).

## 9. fázis: manuális vezérlés

- A `ManualControlService` Qt-függőség nélkül, a meglévő `Robot` objektumot használja a mozgatáshoz, a forduláshoz és a bányászáshoz. Minden művelet először meghívja a `DebugSession.stop()` metódust: az aktív futás befejeződik, a szimuláció NEM áll vissza alaphelyzetbe, a napló változatlan marad.
- A manuális előrelépés közvetlenül a térképet ellenőrzi (`world.cell_at`), és nem hívja meg az `isThere` függvényt, így nem jár a mező felfedezetté jelölésével. Fal vagy a térkép széle esetén nincs mozgás és nincs hibakód; a megjelenített üzenet: „Fal előtt – a robot megállt.” Automatikus módban továbbra is az `E_BEDROCK_HIT` hibakód érvényes (ezt teszt is ellenőrzi).
- Az érzékelő megjelenítése (`Sensor.peek`, a térképen szaggatott vonallal jelölt előtte lévő mező) önmagában nem teszi felfedezetté a mezőt.
- Ha a manuális vezérlés állítja le a futást, akkor is lefut a normál „futás befejeződött” kezelő. Ha a grafikus felülethez megadtak kimeneti útvonalat, ekkor a program részleges naplója íródik ki (`EOR` nélkül). A manuális műveletek nem adnak hozzá bejegyzéseket a naplóhoz.
- A következő futtatás vagy az újraindítás a korábbiaknak megfelelően alaphelyzetbe állítja a szimulációt.
