# build.md – robot.exe készítése (Windows)

A `robot.exe` PyInstallerrel készül, egyetlen fájlként, konzolos módban.
A build csak Windowson fut: a PyInstaller nem tud keresztfordítani.

## 1. Követelmények

- Windows 10 vagy újabb.
- Python 3.12 vagy újabb (`python --version`).
- Internetkapcsolat a csomagok telepítéséhez.

## 2. Környezet előkészítése

A projekt gyökérkönyvtárában (ahol a `main.py` van), PowerShellben:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

A `requirements.txt` tartalmazza a PySide6, pytest, Ruff, mypy és PyInstaller csomagot.

Ha a PowerShell nem engedi a szkriptet, használd a `cmd`-et:
`.venv\Scripts\activate.bat`.

## 3. Ellenőrzés build előtt

```powershell
pytest
ruff check .
mypy src
```

Mindháromnak hibátlanul kell lefutnia. Hiba esetén ne építs.

## 4. Fordítás

```powershell
pyinstaller --onefile --console --name robot --paths src --hidden-import robot_ide.ui.app main.py
```

- `--onefile`: egyetlen `robot.exe`.
- `--console`: a `-q` mód `print` kimenete látszik a terminálban.
- `--paths src`: a `robot_ide` csomag a `src` mappában van.
- `--hidden-import robot_ide.ui.app`: a GUI modult a `-q` mód nem importálja, ezért kézzel kell megadni.

Eredmény: `dist\robot.exe`. A `build\` mappa és a `robot.spec` fájl köztes termék.

## 5. Kipróbálás

Csendes mód (nincs GUI):

```powershell
dist\robot.exe -q examples\collect_gold.txt out.txt
```

Várt eredmény:

- A konzolon a `2` jelenik meg.
- Az `out.txt` utolsó két sora: `13 print 2` és `EOR`.
- A kilépési kód 0 (`echo $LASTEXITCODE`).

Hibás bemenet esetén a kilépési kód 2, a hibaüzenet a stderr-re kerül.

Grafikus mód:

```powershell
dist\robot.exe
dist\robot.exe examples\collect_gold.txt out.txt
```

Az ablaknak meg kell nyílnia. A második parancs betölti a példát, és a futás végén kiírja a naplót az `out.txt` fájlba.

## 6. Takarítás

```powershell
Remove-Item -Recurse -Force build, dist, robot.spec
```

## 7. Gyakori hibák

- `No module named 'robot_ide'` futáskor: hiányzik a `--paths src`.
- `PySide6 is required for GUI mode`: a PySide6 nincs telepítve a build környezetben, vagy hiányzik a `--hidden-import`. Telepítsd, és fordítsd újra.
- A víruskereső karanténba teszi az exe-t: PyInstaller `--onefile` kimenetnél gyakori téves riasztás. Tedd a `dist` mappát a kivételek közé.