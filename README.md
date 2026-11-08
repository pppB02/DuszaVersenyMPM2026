# MineScript Robot IDE

Python és PySide6 alapú fejlesztőkörnyezet MineScript programok szerkesztéséhez és robotok szimulálásához.

## Funkciók

- **Labirintusszimulátor:** a robot pozíciójának, irányának, az érzékelőnek és a felfedezett mezőknek a megjelenítése.
- **Blokkszerkesztő:** MineScript programok vizuális összeállítása és szerkesztése.
- **Forráskódnézet:** a blokkokhoz tartozó szöveges kód automatikus generálása.
- **Programfuttatás:** automatikus futtatás, szüneteltetés, folytatás és újraindítás.
- **Debugger:** lépésenkénti végrehajtás és a változók értékeinek követése.
- **Manuális vezérlés:** a robot előre mozgatása, balra fordítása és bányászás a grafikus felületről.
- **Konzol és naplózás:** a program kimenetének, hibáinak és végrehajtási naplójának megjelenítése.
- **Témaváltás:** világos és sötét megjelenés.

## Követelmények

- Python 3.12 vagy újabb
- A függőségek a `requirements.txt` fájlban találhatók.

## Telepítés

A repository klónozása:

```bash
git clone https://github.com/pppB02/DuszaVersenyMPM2026.git
cd DuszaVersenyMPM2026
```

A függőségek telepítése:

```bash
python -m pip install -r requirements.txt
```

## Indítás

A grafikus felület elindítása a mintabemenettel:

```bash
python main.py input_video_program.txt output.txt
```

A program grafikus felület nélküli futtatása:

```bash
python main.py -q input_video_program.txt output.txt
```

A `-q` kapcsolóval a program konzolos módban fut, és az eredményt a megadott kimeneti fájlba naplózza.

## Technológiák

- Python 3.12+
- PySide6
- pytest
- Ruff
- mypy
- PyInstaller
