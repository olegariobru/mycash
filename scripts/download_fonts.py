from pathlib import Path
from urllib.request import urlopen

FONTS = {
    "Roboto.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/roboto/Roboto%5Bwdth%2Cwght%5D.ttf",
    "Montserrat.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf",
}

target = Path(__file__).parents[1] / "assets" / "fonts"
target.mkdir(parents=True, exist_ok=True)
for name, url in FONTS.items():
    destination = target / name
    if not destination.exists():
        print(f"Baixando {name}...")
        destination.write_bytes(urlopen(url, timeout=60).read())
print("Fontes prontas.")

