# Arbeitsregeln für Claude (Trading-Bilanz)

Ziel: Runden laufen ohne Rückfragen zur Berechtigung durch.

## Befehle
- Erlaubt ist alles, was keine Rückfrage auslöst. Änderungen an `trading-bilanz.html` prüft der Diff nach jeder Phase.
- Lesen, Suchen, Ordner ansehen: lieber mit den Werkzeugen Read, Grep, Glob als mit Shell-Befehlen.

## Skripte statt `node -e`
- Textersetzungen in `trading-bilanz.html` und längere Prüfungen als Skriptdatei im Scratchpad schreiben (Write) und mit `node <datei>` ausführen. Kein `node -e '…'`.
- Grund: Die Shell verändert `\n`, Backticks und Anführungszeichen in `node -e`, und lange Einzeiler sind schwer zu prüfen.

## Testordner und Testbilder
- Testordner, Testkopien und Testbilder im Scratchpad anlegen und dort löschen, nicht im Projekt.
- Löschen im Scratchpad: ein einzelner Befehl `rm -rf "<absoluter Pfad unter …/scratchpad/>"`, ohne `*`, ohne `$`, ohne `..`. Nur diese Form läuft ohne Rückfrage (Prüfskript `.claude/hooks/rm-pruefen.js`).
- Löschen im Projekt fragt immer nach. Das ist gewollt.
- Bilder, die Florian sehen soll, kommen weiter nach `Bilder/RundeN-Tests/`.

## Prüfen (ab 0.56, ersetzt die bisherigen Regeln zum Schnelltest, wo sie sich widersprechen)
Ziel: Zeit und Token sparen, bei gleicher Qualität.
- **Pro Phase:** node-Tests (`tools/tests/runall.js`) und Byte-Vergleich in einem Lauf (ein Skript im Scratchpad). Ausgabe nur Fehler und eine Summenzeile.
- **Byte-Vergleich (ab 0.71 im Projekt):** `node tools/byte-vergleich.js "<Sicherung vor der Runde>.html" --ablage=<Scratchpad-Ordner>` (alle Prüfstände, AT und DE; Excel ohne das Datum „Erstellt am“). `--selbsttest` prüft den Vergleich selbst.
- **Browser einmal am Ende der Runde**: `tools/browser/pruefen.js`, dazu nur für das Geänderte, was dort fehlt. Höchstens 5 Bilder für die ganze Runde.
- **Parallele Runden** koordiniert Florian selbst. Keine Prüfung, ob andere Sitzungen an der Datei arbeiten.

## Tests nach Themen (ab 0.57 „Tests aufräumen“)
- **node:** `node tools/tests/runall.js` prüft alle Themen in einem Lauf (parallel, ca. 8 s), Ausgabe nur Fehler und Summenzeile. Ein Thema allein: `node tools/tests/runall.js adressbuch`. Andere Fassung des Tools: Umgebung `HTMLF`.
- **Themen** (je eine Datei in `tools/tests/`): reports, kurse, steuer, sicherung, tag-daten, boerse, wallet-dateien, adressbuch, noch-offen, vorgaenge (Alle Vorgänge, Einträge, Wallets), oberflaeche, anleitung. Gemeinsamer Lader und Hilfen in `tools/tests/lib.js`.
- **Neue Prüfungen kommen in das passende Thema** (neuer Teil mit `teil(…)` oder in einen bestehenden). Keine eigene Testdatei je Runde. Prüfe Verhalten (Tool laden, Funktion aufrufen); eine Suche im Quelltext nur, wo Verhalten nicht ohne großen Aufwand geht, dann mit `q(…)` statt `eq(…)`.
- **Ändert eine Runde ein Verhalten**, passt sie die betroffene Prüfung im Thema an (Kommentar „Ab 0.xx: …“), statt eine neue daneben zu stellen.
- **Browser:** `node tools/browser/pruefen.js` (Chromium, 1280 und 412 px, hell und dunkel: jeder Reiter, die wichtigsten Fenster, Konsole, seitliches Scrollen, × und Knöpfe unten, Kontrast). Eine Runde ergänzt dort nur, was sie braucht: weitere Fenster in `FENSTER`, eigene Prüfungen in `ZUSATZ`. `--bilder=Bilder/RundeN-Tests` speichert 4 Bilder.

## Prüfstände (ab 0.56)
- Alle Prüfstände liegen in `tools/pruefstaende/` (s2r, s16r, Beispiel, Sicherungen 20.10. und 22.10., eine aktuelle echte Sicherung von Florian, sobald er sie hineinlegt; in `dateien/` Wallet-, Börsen- und EZB-Dateien der Tests). Tests lesen sie nur dort über `tools/pruefstand.js`, nie aus ABLAGE. Fehlt ein Prüfstand, schlägt der Test fehl.
- Fehler-Sicherungen kommen nicht in die Prüfstände. Ist der Fehler behoben, wird daraus ein kleiner erfundener Fall im Test.
- **Die Prüfstände sind echte Daten: `tools/pruefstaende/` darf nie nach `GitHub/` (öffentlich).** Vor jedem Kopieren nach `GitHub/` prüfen, dass nichts daraus dort liegt. In `.gitignore` steht der Ordner.

## Bericht (ab 0.56)
Nach Inhalt, nicht nach Länge, in `BERICHTE/0.xx.md`.
- **Muss rein:** Kurzfassung; jede Abweichung vom Auftrag samt Grund; Funde (behoben und nicht behoben); Entscheidungen, die Claude selbst getroffen hat; offene Fragen; alles, was der Auftrag ausdrücklich verlangt (Listen, Tabellen); „Was du selbst prüfen solltest“.
- **Kurz halten:** Tests eine Zeile mit Zahl und Ergebnis, Einzelheiten nur bei Fehlern; Byte-Vergleich eine Zeile; Sicherungen und Bilder je eine Zeile mit Ordner; Funktionsnamen nur, wo sie für eine spätere Runde gebraucht werden; geänderte alte Tests nur Name und Grund in einem Satz.
- **Im Chat** höchstens 5 Zeilen.

## Wenn doch eine Rückfrage kommt
- Am Ende der Runde in `BERICHTE/0.xx.md` notieren: welcher Befehl (genau so, wie er aufgerufen wurde), welches Werkzeug, und warum er nicht zu den Regeln passte. Befehle stehen im Bericht nur, wenn eine Rückfrage kam.
