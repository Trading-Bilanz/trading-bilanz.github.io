# Erzeugt alle Icons, Logos und Vorschaubilder der Trading-Bilanz aus dem Original.
#
#   Befehl (im Hauptordner des Repos):  python icons/icons-erzeugen.py
#   Einmal vorher:                      pip install pillow
#   Übersichtsbild dazu:                python icons/icons-erzeugen.py --uebersicht <Pfad.png>
#
# Neues Motiv: icons/quelle/icon-trading-bilanz-original.png ersetzen und den Befehl starten. Das Original darf
# jedes Format haben, muss aber ein PNG mit durchsichtigem Hintergrund sein. Das Skript schneidet selbst auf das
# Motiv zu (alle Pixel ab SCHWELLE_DECKKRAFT). Alle Dateien in icons/ werden neu geschrieben, und das Skript setzt
# die eingebetteten Bilder im Tool neu ein (trading-bilanz.html bzw. index.html: Favicon 32, apple-touch-icon 180,
# Logo im Kopf, Logo in der Begrüßung, ab 0.139 der Schmetterling der Meilensteine in zwei Größen aus
# icons/quelle/schmetterling-freigestellt.png, dort als data:-Adresse, weil die Content-Security-Policy des Tools Bilder
# nur als data: erlaubt). Dabei passt es width und height der Logos an das Seitenverhältnis des Motivs an und
# setzt LOGO_VERSATZ ins CSS von Tool und Anleitung. Die Anleitung verweist auf die Dateien in icons/.
#
# Mit --uebersicht <Pfad> schreibt das Skript zusätzlich ein Blatt zum Ansehen: Kopf am PC und am Handy, Begrüßung,
# Favicon 16 und 32 px, iPhone-Symbol, je hell und dunkel, nachgebaut mit Pillow und Inter (doppelte Auflösung,
# wie ein hochauflösender Bildschirm). Ohne die Option schreibt es kein Übersichtsbild.
#
# Schrift der Vorschaubilder und der Übersicht: Inter (SIL Open Font License 1.1, icons/quelle/schrift/OFL.txt),
# auf westeuropäische Zeichen gekürzt. Sie liegt hier bei, damit jeder Rechner dieselben Bilder macht.
# OFL.txt ist byte-gleich die Datei LICENSE.txt aus github.com/rsms/inter, Tag v4.0 (Commit 2ce9119398be143fa289c3e180824db1b7ed803e,
# passend zu den Schriftdateien Version 4.000), nur umbenannt. SHA-256:
# 262481e844521b326f5ecd053e59b98c8b2da78c8ee1bdbb6e8174305e54935a

import base64
import io
import os
import re
import sys

from PIL import Image, ImageCms, ImageColor, ImageDraw, ImageFont

ORDNER = os.path.dirname(os.path.abspath(__file__))
ORIGINAL = os.path.join(ORDNER, 'quelle', 'icon-trading-bilanz-original.png')
SCHRIFT_TITEL = os.path.join(ORDNER, 'quelle', 'schrift', 'Inter-SemiBold.otf')
SCHRIFT_TEXT = os.path.join(ORDNER, 'quelle', 'schrift', 'Inter-Regular.otf')
TOOL = [os.path.join(ORDNER, '..', n) for n in ('trading-bilanz.html', 'index.html')]
ANLEITUNG = os.path.join(ORDNER, '..', 'anleitung.html')

# Zuschnitt: Pixel mit mindestens dieser Deckkraft (0 bis 255) gehören zum Motiv. 16 = etwa 6 %.
# Ganz zarte Reste am Rand (Kantenglättung, Staub) zählen so nicht mit.
SCHWELLE_DECKKRAFT = 16

# Quadratische Icons: Größe in Pixeln und Rand je Seite in Prozent der Kante. Datei: icon-trading-bilanz-<Größe>.png
#   32 Favicon (das ganze Motiv, kein Ausschnitt) · 180 Startbildschirm iPhone (iOS rundet die Ecken ab, daher mehr Rand)
#   192 Startbildschirm Android · 512 README, später Web-App
# Das Motiv steht mittig und passt mit dem Rand in das Quadrat (bei einem breiten Motiv bestimmt die Breite die Größe).
RAND = {32: 4, 180: 10, 192: 6, 512: 6}

# Logos im echten Format: Höhe der Bilddaten fest (doppelt so viele Pixel wie angezeigt), die Breite folgt dem Motiv.
#   (Datei, Höhe der Bilddaten, angezeigte Höhe am PC)
LOGOS = [
    ('logo-trading-bilanz-kopf.png', 64, 32),          # Kopf von Tool und Anleitung (am Handy kleiner, CSS)
    ('logo-trading-bilanz-begruessung.png', 112, 56),  # Begrüßung im Tool (am Handy 48 px, CSS)
]

# Versatz des Logos nach oben (negativ) oder unten (positiv), in Prozent der Logohöhe. Das Skript schreibt ihn als
# transform:translateY(…%) ins CSS von Tool und Anleitung. Er gilt so für alle Größen gleich und ändert nichts am
# Platz, den das Logo einnimmt. Wofür: Das Lesezeichen hängt unten aus dem Buch, dadurch wirkt das Buch neben der
# Schrift etwas zu tief. 0 = Mitte des zugeschnittenen Motivs auf der Mitte der Zeile.
LOGO_VERSATZ = -3

# Eingebettete Bilder im Tool: Stelle (Anfang des Tags bis vor die Adresse) und Datei
EINGEBETTET = [
    ('<link rel="icon" type="image/png" sizes="32x32" href="', 'icon-trading-bilanz-32.png'),
    ('<link rel="apple-touch-icon" sizes="180x180" href="', 'icon-trading-bilanz-180.png'),
    ('<img class="hlogo" src="', 'logo-trading-bilanz-kopf.png'),
    ('<img class="ilogo" src="', 'logo-trading-bilanz-begruessung.png'),
    ('const BFLY_K="', 'schmetterling-klein.png'),   # ab 0.139: Schmetterling der Meilensteine, im Skript des Tools
    ('const BFLY_G="', 'schmetterling-gross.png'),
]

# Schmetterling der Meilensteine (ab 0.139): eigenes Original, zwei Größen nach Breite, die Höhe folgt dem Motiv.
#   groß  Feier-Fenster und geteiltes Bild · klein  Kachel, Zeile, Reiter und Titel (angezeigt ab 18 px Höhe)
# Beide mit Palette: SCHMETTERLING_FARBEN = (Farben für deckende Pixel, Farben für halb durchsichtige Randpixel).
# Die deckenden Farben wählt der Medianschnitt aus dem Motiv; mit der einfachen Palette der anderen Icons (FASTOCTREE)
# zeigte das Gold im großen Bild Streifen (Prüfung 0.139, vergrößert angesehen), so nicht.
SCHMETTERLING = os.path.join(ORDNER, 'quelle', 'schmetterling-freigestellt.png')
SCHMETTERLINGE = [('schmetterling-gross.png', 512), ('schmetterling-klein.png', 64)]
SCHMETTERLING_FARBEN = (128, 31)

# Größen ohne Transparenz: Alles Durchsichtige wird mit dieser Farbe gefüllt.
# iOS rundet das apple-touch-icon selbst ab und füllt Durchsichtiges schwarz.
# 'auto' = mittlere Farbe am Rand der Kachel im Motiv (nur für ein Motiv auf einer Kachel), sonst eine Farbe.
# Ab dem Buch ohne Kachel (0.94): '#f6f5f2' = --bg des Tools ('auto' gäbe das Petrol des Einbands).
OHNE_TRANSPARENZ = {180: '#f6f5f2'}

# Dateien ohne Farbreduktion (Palette). Hier eintragen, wenn eine Datei mit Palette Streifen in den Verläufen zeigt.
# Prüfung 0.96 (Buch im echten Format, vergrößert angesehen): mit Palette nur das Favicon 32 ohne sichtbare Streifen;
# die Logos zeigen mit Palette Stufen in den blauen Säulen und im Gold.
VOLLFARBE = {'icon-trading-bilanz-180.png', 'icon-trading-bilanz-192.png', 'icon-trading-bilanz-512.png',
             'logo-trading-bilanz-kopf.png', 'logo-trading-bilanz-begruessung.png',
             'vorschau-trading-bilanz.png', 'vorschau-github.png'}

# Vorschaubilder (Datei, Breite, Höhe). Farben aus :root des Tools (helles Farbschema).
VORSCHAU = [
    ('vorschau-trading-bilanz.png', 1200, 630),  # Link-Vorschau (og:image)
    ('vorschau-github.png', 1280, 640),          # Social preview auf GitHub
]
VORSCHAU_LOGO = 200  # Höhe des Buchs in px bei 630 px Bildhöhe, die Breite folgt dem Motiv
TITEL = 'Trading-Bilanz'
UNTERTITEL = [  # je Eintrag eine Zeile
    'Statistik und Steuerzahlen aus deinen MT5-Reports.',
    'Deine Daten bleiben bei dir.',
]
FARBE_GRUND = '#f6f5f2'   # --bg
FARBE_TITEL = '#1a1a1a'   # --ink
FARBE_TEXT = '#373d43'    # --ink2
FARBE_LINIE = '#C49A55'   # --tab-line (Gold der Reiter)


def motiv_zuschneiden(orig):
    """Schneidet das Original auf das Motiv zu. Bricht ab, wenn der Hintergrund nicht durchsichtig ist."""
    if 'A' not in orig.getbands() and 'transparency' not in orig.info:
        sys.exit('Das Original hat keinen durchsichtigen Hintergrund (kein Alphakanal). Bitte ein PNG mit '
                 'durchsichtigem Hintergrund als icons/quelle/icon-trading-bilanz-original.png ablegen.')
    bild = orig.convert('RGBA')
    alpha = bild.getchannel('A')
    w, h = bild.size
    # Der Hintergrund gilt als durchsichtig, wenn der äußere Rahmen (1 px) überwiegend durchsichtig ist.
    rahmen = [alpha.getpixel((x, y)) for x in range(w) for y in (0, h - 1)] + \
             [alpha.getpixel((x, y)) for y in range(1, h - 1) for x in (0, w - 1)]
    if sum(a >= SCHWELLE_DECKKRAFT for a in rahmen) > len(rahmen) // 2:
        sys.exit('Das Original hat keinen durchsichtigen Hintergrund (der Rand des Bildes ist deckend). Bitte den '
                 'Hintergrund entfernen und als PNG mit Durchsichtigkeit speichern.')
    box = alpha.point(lambda a: 255 if a >= SCHWELLE_DECKKRAFT else 0).getbbox()
    if not box:
        sys.exit('Das Original ist ganz durchsichtig, es gibt kein Motiv zum Zuschneiden.')
    return bild.crop(box)


def kachel_farbe(im):
    """Typische Farbe (Median je Kanal) der ganz deckenden Pixel im äußeren Rand der Kachel."""
    w, h = im.size
    rand = max(2, round(min(w, h) * 0.04))
    kanaele = ([], [], [])
    px = im.load()
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


def speichern(bild, pfad, palette, profil=None):
    if profil:  # Farbprofil nur behalten, wenn es nicht sRGB ist (sRGB nimmt jeder Browser ohnehin an)
        bild.info['icc_profile'] = profil
    else:
        bild.info.pop('icc_profile', None)
    if palette:
        bild = bild.quantize(256, method=Image.Quantize.FASTOCTREE)
    bild.save(pfad, 'PNG', optimize=True)


def palette_ohne_streifen(rgba, n_innen, n_rand):
    """Palette-Bild mit Transparenz: deckende Pixel mit Medianschnitt, halb durchsichtige Randpixel mit eigener kleiner Palette."""
    alpha = rgba.getchannel('A')
    innen = alpha.point(lambda v: 255 if v == 255 else 0)
    rand = alpha.point(lambda v: 255 if 0 < v < 255 else 0)
    rgb = rgba.convert('RGB')
    mittel = rgb.resize((1, 1), Image.BOX).getpixel((0, 0))  # füllt das Durchsichtige, damit es keine Farbe der Palette kostet
    pal = Image.composite(rgb, Image.new('RGB', rgb.size, mittel), innen).quantize(
        n_innen, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    p1 = rgb.quantize(palette=pal, dither=Image.Dither.NONE)
    p2 = Image.composite(rgba, Image.new('RGBA', rgba.size, (0, 0, 0, 0)), rand).quantize(
        n_rand + 1, method=Image.Quantize.FASTOCTREE)
    pal2 = p2.getpalette('RGBA')
    idx1 = Image.frombytes('L', p1.size, p1.tobytes())
    idx2 = Image.frombytes('L', p2.size, p2.tobytes()).point(lambda v: min(255, v + n_innen))
    idx = Image.composite(idx1, Image.composite(idx2, Image.new('L', rgba.size, 255), rand), innen)
    bild = Image.frombytes('P', rgba.size, idx.tobytes())
    farben = (pal.getpalette()[:n_innen * 3] + [0] * (n_innen * 3))[:n_innen * 3]
    deckkraft = [255] * n_innen
    for i in range(n_rand + 1):
        q = pal2[i * 4:i * 4 + 4]
        if len(q) == 4 and n_innen + i < 256:
            farben += list(q[:3])
            deckkraft.append(q[3])
    deckkraft = (deckkraft + [0] * 256)[:256]
    deckkraft[255] = 0  # Index 255 = ganz durchsichtig
    bild.putpalette((farben + [0] * 768)[:768])
    bild.info['transparency'] = bytes(deckkraft)
    return bild


def schmetterlinge():
    """Schreibt die zwei Größen des Schmetterlings und gibt ihre Namen zurück (leer, wenn das Original fehlt)."""
    if not os.path.exists(SCHMETTERLING):
        return []
    motiv = motiv_zuschneiden(Image.open(SCHMETTERLING))
    namen = []
    for name, breite in SCHMETTERLINGE:
        klein = motiv.resize((breite, max(1, round(motiv.height * breite / motiv.width))), Image.LANCZOS)
        palette_ohne_streifen(klein, *SCHMETTERLING_FARBEN).save(os.path.join(ORDNER, name), 'PNG', optimize=True)
        namen.append(name)
    return namen


def nach_hoehe(motiv, hoehe):
    """Motiv auf diese Höhe, Breite im Seitenverhältnis (Pillow rechnet RGBA dabei vormultipliziert)."""
    breite = max(1, round(motiv.width * hoehe / motiv.height))
    return motiv.resize((breite, hoehe), Image.LANCZOS)


def icon(motiv, groesse, rand, fuellung):
    """Quadrat mit dem Motiv in der Mitte und rand Prozent Abstand je Seite."""
    platz = groesse * (1 - 2 * rand / 100)
    s = min(platz / motiv.width, platz / motiv.height)
    klein = motiv.resize((max(1, round(motiv.width * s)), max(1, round(motiv.height * s))), Image.LANCZOS)
    bild = Image.new('RGBA', (groesse, groesse), (0, 0, 0, 0))
    bild.paste(klein, ((groesse - klein.width) // 2, (groesse - klein.height) // 2))
    if fuellung:
        grund = Image.new('RGBA', bild.size, fuellung + (255,))
        bild = Image.alpha_composite(grund, bild).convert('RGB')
    return bild


def vorschau(motiv, breite, hoehe):
    s = hoehe / 630  # alle Maße bezogen auf 630 px Höhe
    bild = Image.new('RGB', (breite, hoehe), FARBE_GRUND)
    zeichnen = ImageDraw.Draw(bild)
    rand = round(80 * s)

    logo = nach_hoehe(motiv, round(VORSCHAU_LOGO * s))
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
    gesamt = logo.height + abst_logo + a_t + d_t + abst_linie + linie + abst_text + zeile * len(UNTERTITEL)
    y = (hoehe - gesamt) // 2
    mitte = breite // 2

    bild.paste(logo, (mitte - logo.width // 2, y), logo)
    y += logo.height + abst_logo
    zeichnen.text((mitte, y + a_t), TITEL, font=f_titel, fill=FARBE_TITEL, anchor='ms')
    y += a_t + d_t + abst_linie
    lb = round(96 * s)
    zeichnen.rectangle([mitte - lb // 2, y, mitte + lb // 2 - 1, y + linie - 1], fill=FARBE_LINIE)
    y += linie + abst_text
    for z in UNTERTITEL:
        zeichnen.text((mitte, y + (zeile - a_x - d_x) // 2 + a_x), z, font=f_text, fill=FARBE_TEXT, anchor='ms')
        y += zeile
    return bild


def farbprofil(orig):
    """Farbprofil des Originals, außer es ist sRGB (dann None, spart Bytes in jeder Datei)."""
    icc = orig.info.get('icc_profile')
    if not icc:
        return None
    try:
        if 'srgb' in ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))).lower():
            return None
    except Exception:
        pass
    return icc


def logo_attribute():
    """width und height je Logo (angezeigte Größe am PC), aus den erzeugten Dateien."""
    werte = {}
    for name, h_daten, h_anzeige in LOGOS:
        with Image.open(os.path.join(ORDNER, name)) as im:
            werte[name] = (int(im.width * h_anzeige / im.height + 0.5), h_anzeige)  # kaufmännisch gerundet (44,5 → 45)
    return werte


def versatz_text():
    return ('%.2f' % LOGO_VERSATZ).rstrip('0').rstrip('.')


def ersetzen_genau_einmal(text, muster, ersatz, datei, was):
    neu, n = re.subn(muster, ersatz, text)
    if n != 1:
        sys.exit('%s: %s gibt es %d-mal statt einmal.' % (datei, was, n))
    return neu


def css_versatz(text, datei, selektor):
    """Setzt LOGO_VERSATZ in die Regel selektor{transform:translateY(…%)}."""
    muster = re.escape(selektor) + r'\{transform:translateY\(-?\d+(?:\.\d+)?%\)\}'
    return ersetzen_genau_einmal(text, muster, lambda m: selektor + '{transform:translateY(%s%%)}' % versatz_text(),
                                 datei, 'Die CSS-Regel %s{transform:translateY(…%%)}' % selektor)


def datei_schreiben(pfad, text, neu, was):
    name = os.path.basename(pfad)
    if neu != text:
        with open(pfad, 'w', encoding='utf-8', newline='') as f:
            f.write(neu)
        print('%s: %s erneuert (%+d Bytes)' % (name, was, len(neu.encode()) - len(text.encode())))
    else:
        print('%s: %s unverändert' % (name, was))


def tool_einsetzen():
    """Setzt die Bilder als data:-Adresse in die Fassungen des Tools ein, die es gibt, dazu width, height und Versatz."""
    attr = logo_attribute()
    for pfad in TOOL:
        if not os.path.exists(pfad):
            continue
        datei = os.path.basename(pfad)
        with open(pfad, encoding='utf-8', newline='') as f:
            text = f.read()
        neu = text
        for anfang, name in EINGEBETTET:
            with open(os.path.join(ORDNER, name), 'rb') as f:
                daten = 'data:image/png;base64,' + base64.b64encode(f.read()).decode('ascii')
            muster = re.escape(anfang) + r'data:image/png;base64,[A-Za-z0-9+/=]*"'
            if name in attr:  # Logo: width und height gleich mit
                muster += r' alt="" width="\d+" height="\d+">'
                ersatz = anfang + daten + '" alt="" width="%d" height="%d">' % attr[name]
            else:
                ersatz = anfang + daten + '"'
            neu = ersetzen_genau_einmal(neu, muster, lambda m: ersatz, datei, 'Die Stelle ' + anfang)
        with Image.open(os.path.join(ORDNER, SCHMETTERLINGE[0][0])) as im:  # Seitenverhältnis des Schmetterlings
            wh = 'const BFLY_WH=[%d,%d];' % im.size
        neu = ersetzen_genau_einmal(neu, r'const BFLY_WH=\[\d+,\d+\];', lambda m: wh, datei, 'Die Stelle const BFLY_WH')
        neu = css_versatz(neu, datei, '.hlogo,.ilogo')
        datei_schreiben(pfad, text, neu, 'eingebettete Bilder und Versatz')


def anleitung_einsetzen():
    """Anleitung: width und height des Logos im Kopf und den Versatz."""
    if not os.path.exists(ANLEITUNG):
        return
    datei = os.path.basename(ANLEITUNG)
    with open(ANLEITUNG, encoding='utf-8', newline='') as f:
        text = f.read()
    name = LOGOS[0][0]
    w, h = logo_attribute()[name]
    anfang = '<img class="hlogo" src="icons/%s" alt=""' % name
    neu = ersetzen_genau_einmal(text, re.escape(anfang) + r' width="\d+" height="\d+">',
                                lambda m: anfang + ' width="%d" height="%d">' % (w, h), datei, 'Die Stelle ' + anfang)
    neu = css_versatz(neu, datei, '.hlogo')
    datei_schreiben(ANLEITUNG, text, neu, 'Maße des Logos und Versatz')


# ---- Übersichtsbild (nur mit --uebersicht) ----

# Farben aus :root des Tools, hell und dunkel
THEMEN = [
    ('hell', {'bg': '#f6f5f2', 'card': '#ffffff', 'ink': '#1a1a1a', 'muted': '#454b51', 'line': '#e2e0da',
              'pos': '#1f7a4d', 'btn': '#2a63a6', 'wand': '#8796a5'}),
    ('dunkel', {'bg': '#15181b', 'card': '#1e2226', 'ink': '#f2f4f6', 'muted': '#bec5cc', 'line': '#30363c',
                'pos': '#5cc08d', 'btn': '#2f6db5', 'wand': '#2b3440'}),
]


def uebersicht(pfad):
    """Blatt zum Ansehen in doppelter Auflösung (1 CSS-Pixel = 2 Pixel, wie ein hochauflösender Bildschirm)."""
    S = 2
    kopf = Image.open(os.path.join(ORDNER, LOGOS[0][0])).convert('RGBA')
    begr = Image.open(os.path.join(ORDNER, LOGOS[1][0])).convert('RGBA')
    fav = Image.open(os.path.join(ORDNER, 'icon-trading-bilanz-32.png')).convert('RGBA')
    ios = Image.open(os.path.join(ORDNER, 'icon-trading-bilanz-180.png')).convert('RGBA')
    f_klein = ImageFont.truetype(SCHRIFT_TEXT, 12 * S)
    spalte, rand = 560 * S, 20 * S

    def logo_zeile(zeichnen, bild, x, y, logo, h_logo, gap, zeilen, groesse, farbe, knopf=None, zeilenhoehe=1.5):
        """Logo (Höhe h_logo) links neben Textzeilen, senkrecht mittig wie display:flex;align-items:center,
        Logo um LOGO_VERSATZ verschoben. Gibt die Höhe der Zeile zurück."""
        f = ImageFont.truetype(SCHRIFT_TITEL, groesse * S)
        a, d = f.getmetrics()
        lh = round(groesse * zeilenhoehe * S)
        text_h = lh * len(zeilen)
        lg = logo if logo.height == h_logo * S else nach_hoehe(logo, h_logo * S)
        hoehe = max(text_h, lg.height)
        mitte = y + hoehe / 2
        ly = round(mitte - lg.height / 2 + lg.height * LOGO_VERSATZ / 100)
        bild.alpha_composite(lg, (x, ly))
        tx = x + lg.width + gap * S
        ty = mitte - text_h / 2
        breite = 0
        for i, z in enumerate(zeilen):  # Grundlinie wie im Browser: Inhalt (a + d) mittig in der Zeilenhöhe
            zeichnen.text((tx, round(ty + i * lh + (lh - a - d) / 2 + a)), z, font=f, fill=farbe, anchor='ls')
            breite = max(breite, zeichnen.textlength(z, font=f))
        if knopf:
            fk = ImageFont.truetype(SCHRIFT_TEXT, 14 * S)
            kx = round(tx + breite + knopf[1] * S)
            kw, kh = round(zeichnen.textlength(knopf[0], font=fk) + 20 * S), round(14 * 1.5 * S + 8 * S + 2 * S)
            ky = round(mitte - kh / 2)
            zeichnen.rounded_rectangle([kx, ky, kx + kw, ky + kh], radius=8 * S, fill=knopf[2])
            zeichnen.text((kx + kw / 2, ky + kh / 2), knopf[0], font=fk, fill='#ffffff', anchor='mm')
        return hoehe

    teile = []
    for thema, c in THEMEN:
        bild = Image.new('RGBA', (spalte, 640 * S), c['bg'])
        z = ImageDraw.Draw(bild)
        y = rand

        def titel(text):
            nonlocal y
            z.text((rand, y + 12 * S), text, font=f_klein, fill=c['muted'], anchor='ls')
            y += 20 * S

        titel('Kopf am PC (Logo 32 px, Titel 26 px), %s' % thema)
        y += logo_zeile(z, bild, rand, y, kopf, 32, 10, ['Trading-Bilanz'], 26, c['ink'], ('Erste Schritte', 14, c['btn'])) + 18 * S
        titel('Kopf am Handy (Logo 24 px, Titel 24 px)')
        y += logo_zeile(z, bild, rand, y, kopf, 24, 6, ['Trading-Bilanz'], 24, c['ink'], ('Erste Schritte', 8, c['btn'])) + 18 * S
        titel('Begrüßung am PC (Logo 56 px, Titel 20 px)')
        z.rounded_rectangle([rand, y, spalte - rand, y + 88 * S], radius=12 * S, fill=c['card'], outline=c['line'], width=S)
        logo_zeile(z, bild, rand + 16 * S, y + 16 * S, begr, 56, 14, ['Willkommen bei der Trading-Bilanz'], 20, c['pos'])
        y += 88 * S
        y += 18 * S
        titel('Begrüßung am Handy (Logo 48 px, zwei Zeilen)')
        z.rounded_rectangle([rand, y, rand + 300 * S, y + 92 * S], radius=12 * S, fill=c['card'], outline=c['line'], width=S)
        logo_zeile(z, bild, rand + 16 * S, y + 16 * S, begr, 48, 12, ['Willkommen bei der', 'Trading-Bilanz'], 20, c['pos'])
        y += 92 * S
        y += 18 * S
        titel('Favicon 16 px und 32 px · iPhone-Symbol (60 px, Ecken wie iOS)')
        f16 = fav.resize((16, 16), Image.LANCZOS)
        x = rand
        for kl in (f16, fav):
            gross = kl.resize((kl.width * S, kl.height * S), Image.NEAREST)  # 1 Pixel = 2 x 2
            bild.alpha_composite(gross, (x, y))
            x += gross.width + 24 * S
        sym = ios.resize((60 * S, 60 * S), Image.LANCZOS)
        maske = Image.new('L', sym.size, 0)
        ImageDraw.Draw(maske).rounded_rectangle([0, 0, sym.width - 1, sym.height - 1], radius=round(sym.width * 0.2237), fill=255)
        sym.putalpha(maske)
        z.rectangle([x, y, x + 100 * S - 1, y + 100 * S - 1], fill=c['wand'])  # Hintergrund des Startbildschirms
        bild.alpha_composite(sym, (x + 20 * S, y + 20 * S))
        y += 100 * S + rand
        teile.append(bild.crop((0, 0, spalte, y)))

    blatt = Image.new('RGB', (sum(t.width for t in teile), max(t.height for t in teile)), THEMEN[0][1]['bg'])
    x = 0
    for t in teile:
        blatt.paste(t.convert('RGB'), (x, 0))
        x += t.width
    blatt.save(pfad, 'PNG', optimize=True)
    print('Übersicht: %s (%d x %d px)' % (pfad, blatt.width, blatt.height))


def main():
    argumente = sys.argv[1:]
    ziel_uebersicht = None
    if argumente[:1] == ['--uebersicht']:
        if len(argumente) != 2:
            sys.exit('Aufruf: python icons/icons-erzeugen.py --uebersicht <Pfad.png>')
        ziel_uebersicht = argumente[1]
    elif argumente:
        sys.exit('Unbekannte Angabe: %s. Erlaubt ist nur --uebersicht <Pfad.png>.' % ' '.join(argumente))
    if not os.path.exists(ORIGINAL):
        sys.exit('Original fehlt: ' + ORIGINAL)
    roh = Image.open(ORIGINAL)
    profil = farbprofil(roh)
    motiv = motiv_zuschneiden(roh)
    print('Motiv: %d x %d px (zugeschnitten aus %d x %d px)' % (motiv.size + roh.size))
    kachel = None
    erzeugt = []
    for g, rand in sorted(RAND.items()):
        f = OHNE_TRANSPARENZ.get(g)
        if f == 'auto':
            kachel = kachel or kachel_farbe(motiv)
            f = kachel
        elif f:
            f = ImageColor.getrgb(f)[:3]
        name = 'icon-trading-bilanz-%d.png' % g
        speichern(icon(motiv, g, rand, f), os.path.join(ORDNER, name), name not in VOLLFARBE, profil)
        erzeugt.append(name)
    for name, h_daten, _ in LOGOS:
        speichern(nach_hoehe(motiv, h_daten), os.path.join(ORDNER, name), name not in VOLLFARBE, profil)
        erzeugt.append(name)
    for name, b, h in VORSCHAU:
        speichern(vorschau(motiv, b, h), os.path.join(ORDNER, name), name not in VOLLFARBE, profil)
        erzeugt.append(name)
    erzeugt += schmetterlinge()
    for name in erzeugt:
        with Image.open(os.path.join(ORDNER, name)) as im:
            print('%-38s %4d x %-4d %7d Bytes' % (name, im.width, im.height, os.path.getsize(os.path.join(ORDNER, name))))
    if kachel:
        print('Farbe der Kachel für die Ecken: #%02x%02x%02x' % kachel)
    tool_einsetzen()
    anleitung_einsetzen()
    if ziel_uebersicht:
        uebersicht(ziel_uebersicht)


if __name__ == '__main__':
    main()
