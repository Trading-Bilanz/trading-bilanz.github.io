# Erzeugt alle Icons und Vorschaubilder der Trading-Bilanz aus dem Original.
#
#   Befehl (im Hauptordner des Repos):  python icons/icons-erzeugen.py
#   Einmal vorher:                      pip install pillow
#
# Neues Motiv: icons/quelle/icon-trading-bilanz-original.png ersetzen (quadratisch, PNG mit
# transparenten Ecken) und den Befehl starten. Alle Dateien in icons/ werden neu geschrieben.
# Danach die eingebetteten Bilder im Tool (trading-bilanz.html: Favicon 32, apple-touch-icon 180,
# Logo im Kopf 64, Logo in der Begrüßung 128) neu einsetzen, die stehen dort als data:-Adresse.
#
# Schrift der Vorschaubilder: Inter (SIL Open Font License 1.1, icons/quelle/schrift/OFL.txt),
# auf westeuropäische Zeichen gekürzt. Sie liegt hier bei, damit jeder Rechner dieselben Bilder macht.

import os
import sys

from PIL import Image, ImageDraw, ImageFont

ORDNER = os.path.dirname(os.path.abspath(__file__))
ORIGINAL = os.path.join(ORDNER, 'quelle', 'icon-trading-bilanz-original.png')
SCHRIFT_TITEL = os.path.join(ORDNER, 'quelle', 'schrift', 'Inter-SemiBold.otf')
SCHRIFT_TEXT = os.path.join(ORDNER, 'quelle', 'schrift', 'Inter-Regular.otf')

# Icon-Größen in Pixeln (quadratisch). Datei: icon-trading-bilanz-<Größe>.png
#   32 Favicon · 64 Logo im Kopf · 128 Logo in der Begrüßung · 180 Startbildschirm iPhone
#   192 Startbildschirm Android · 512 README, später Web-App
GROESSEN = [32, 64, 128, 180, 192, 512]

# Größen ohne Transparenz: Die Ecken werden mit der Farbe der Kachel gefüllt.
# iOS rundet das apple-touch-icon selbst ab und füllt Durchsichtiges schwarz.
# 'auto' = mittlere Farbe am Rand der Kachel im Original, sonst eine Farbe wie '#fbf8f5'.
OHNE_TRANSPARENZ = {180: 'auto'}

# Größen ohne Farbreduktion (Palette). Hier eintragen, wenn eine Größe Streifen in den Verläufen zeigt.
# Ab 128 px zeigten die Säulen mit Palette Streifen (Prüfung 0.89), 32 und 64 px nicht.
# Für die Vorschaubilder steht hier der Dateiname (auch dort leichte Streifen im Logo mit Palette).
VOLLFARBE = {128, 180, 192, 512, 'vorschau-trading-bilanz.png', 'vorschau-github.png'}

# Vorschaubilder (Datei, Breite, Höhe). Farben aus :root des Tools (helles Farbschema).
VORSCHAU = [
    ('vorschau-trading-bilanz.png', 1200, 630),  # Link-Vorschau (og:image)
    ('vorschau-github.png', 1280, 640),          # Social preview auf GitHub
]
TITEL = 'Trading-Bilanz'
UNTERTITEL = [  # je Eintrag eine Zeile
    'Statistik und Steuerzahlen aus deinen MetaTrader-5-Reports.',
    'Deine Daten bleiben in diesem Browser.',
]
FARBE_GRUND = '#f6f5f2'   # --bg
FARBE_TITEL = '#1a1a1a'   # --ink
FARBE_TEXT = '#373d43'    # --ink2
FARBE_LINIE = '#C49A55'   # --tab-line (Gold der Reiter)


def kachel_farbe(im):
    """Typische Farbe (Median je Kanal) der ganz deckenden Pixel im äußeren Rand der Kachel."""
    box = im.getchannel('A').getbbox()
    ab = im.crop(box)
    w, h = ab.size
    rand = max(2, round(min(w, h) * 0.04))
    kanaele = ([], [], [])
    px = ab.load()
    for y in range(h):
        for x in range(w):
            if rand <= x < w - rand and rand <= y < h - rand:
                continue
            r, g, b, a = px[x, y]
            if a == 255:
                kanaele[0].append(r); kanaele[1].append(g); kanaele[2].append(b)
    if not kanaele[0]:
        return (255, 255, 255)
    return tuple(sorted(k)[len(k) // 2] for k in kanaele)


def speichern(bild, pfad, palette):
    if palette:
        bild = bild.quantize(256, method=Image.Quantize.FASTOCTREE)
    bild.save(pfad, 'PNG', optimize=True)


def icon(orig, groesse, fuellung):
    bild = orig.resize((groesse, groesse), Image.LANCZOS)  # Pillow rechnet RGBA dabei vormultipliziert
    if fuellung:
        grund = Image.new('RGBA', bild.size, fuellung + (255,))
        bild = Image.alpha_composite(grund, bild).convert('RGB')
    return bild


def vorschau(orig, breite, hoehe):
    s = hoehe / 630  # alle Maße bezogen auf 630 px Höhe
    bild = Image.new('RGB', (breite, hoehe), FARBE_GRUND)
    zeichnen = ImageDraw.Draw(bild)
    rand = round(80 * s)

    ic = round(230 * s)
    logo = orig.resize((ic, ic), Image.LANCZOS)
    f_titel = ImageFont.truetype(SCHRIFT_TITEL, round(92 * s))
    groesse_text = round(34 * s)
    while True:  # Untertitel so groß wie möglich, aber jede Zeile innerhalb des Rands
        f_text = ImageFont.truetype(SCHRIFT_TEXT, groesse_text)
        if max(zeichnen.textlength(z, font=f_text) for z in UNTERTITEL) <= breite - 2 * rand or groesse_text <= 12:
            break
        groesse_text -= 1

    a_t, d_t = f_titel.getmetrics()
    a_x, d_x = f_text.getmetrics()
    zeile = round(groesse_text * 1.35)
    abst_logo, abst_linie, linie, abst_text = round(26 * s), round(18 * s), max(3, round(4 * s)), round(26 * s)
    gesamt = ic + abst_logo + a_t + d_t + abst_linie + linie + abst_text + zeile * len(UNTERTITEL)
    y = (hoehe - gesamt) // 2
    mitte = breite // 2

    bild.paste(logo, (mitte - ic // 2, y), logo)
    y += ic + abst_logo
    zeichnen.text((mitte, y + a_t), TITEL, font=f_titel, fill=FARBE_TITEL, anchor='ms')
    y += a_t + d_t + abst_linie
    lb = round(96 * s)
    zeichnen.rectangle([mitte - lb // 2, y, mitte + lb // 2 - 1, y + linie - 1], fill=FARBE_LINIE)
    y += linie + abst_text
    for z in UNTERTITEL:
        zeichnen.text((mitte, y + (zeile - a_x - d_x) // 2 + a_x), z, font=f_text, fill=FARBE_TEXT, anchor='ms')
        y += zeile
    return bild


def main():
    if not os.path.exists(ORIGINAL):
        sys.exit('Original fehlt: ' + ORIGINAL)
    orig = Image.open(ORIGINAL).convert('RGBA')
    if orig.width != orig.height:
        sys.exit('Das Original muss quadratisch sein, ist aber %d x %d px.' % orig.size)
    kachel = None
    erzeugt = []
    for g in GROESSEN:
        f = OHNE_TRANSPARENZ.get(g)
        if f == 'auto':
            kachel = kachel or kachel_farbe(orig)
            f = kachel
        elif f:
            f = ImageColorRGB(f)
        name = 'icon-trading-bilanz-%d.png' % g
        speichern(icon(orig, g, f), os.path.join(ORDNER, name), g not in VOLLFARBE)
        erzeugt.append(name)
    for name, b, h in VORSCHAU:
        speichern(vorschau(orig, b, h), os.path.join(ORDNER, name), name not in VOLLFARBE)
        erzeugt.append(name)
    for name in erzeugt:
        print('%-30s %7d Bytes' % (name, os.path.getsize(os.path.join(ORDNER, name))))
    if kachel:
        print('Farbe der Kachel für die Ecken: #%02x%02x%02x' % kachel)


def ImageColorRGB(farbe):
    from PIL import ImageColor
    return ImageColor.getrgb(farbe)[:3]


if __name__ == '__main__':
    main()
