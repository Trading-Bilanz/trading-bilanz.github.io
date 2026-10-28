// Prüft die Regel aus GESTALTUNG.md Abschnitt 6 (ab 0.50 Nachtrag 13): „↗“ hängt mit geschütztem Leerzeichen am Wort davor (&nbsp;↗ oder das Zeichen
// U+00A0), damit es nie allein in die nächste Zeile rutscht. Gesucht wird im Quelltext von trading-bilanz.html und GitHub/anleitung.html: Jedes „↗“
// direkt nach einem normalen Leerzeichen, Tabulator oder Zeilenumbruch ist ein Fehler. Ausgenommen sind Kommentare (<!-- … -->, /* … */ und Zeilen,
// die mit // beginnen), dort sieht niemand das Zeichen. Ein „↗“ ohne Wort davor (z. B. eigener Link „↗“ hinter einer Explorer-Adresse) ist erlaubt.
// Aufruf im Projektordner:  node tools/test-pfeil.js
// Gegenprobe: HTMLF = andere Fassung des Tools, ANLF = andere Fassung der Anleitung (wie bei test-anleitung).
"use strict";
const fs=require('fs'),path=require('path');
const ROOT=path.join(__dirname,'..');
const FILES=[['trading-bilanz.html',process.env.HTMLF||path.join(ROOT,'trading-bilanz.html')],
             ['GitHub/anleitung.html',process.env.ANLF||path.join(ROOT,'GitHub','anleitung.html')]];
let fail=0,n=0;
function eq(name,got,exp){n++;const ok=JSON.stringify(got)===JSON.stringify(exp);if(!ok)fail++;
  console.log((ok?'  ok     ':'  FEHLER ')+name+(ok?'':`  →  ist ${JSON.stringify(got,null,1).slice(0,3000)}, soll ${JSON.stringify(exp)}`))}

// Kommentare durch gleich viele Leerzeilen ersetzen, damit die Zeilennummern stimmen
const blank=s=>s.replace(/[^\n]/g,'');
function noComments(t){
  return t.replace(/<!--[\s\S]*?-->/g,blank)
    .replace(/^[ \t]*\/\*[\s\S]*?\*\//gm,blank)
    .replace(/^[ \t]*\/\/.*$/gm,'')}

for(const [name,f] of FILES){
  const T=fs.readFileSync(f,'utf8'),C=noComments(T),L=C.split('\n');
  const bad=[];L.forEach((l,i)=>{for(const m of l.matchAll(/\s↗/g)){const a=Math.max(0,m.index-50);bad.push(`Zeile ${i+1}: …${l.slice(a,m.index+12).trim()}…`)}});
  const good=(C.match(/(&nbsp;| )↗/g)||[]).length;
  console.log(name);
  eq(`kein „↗“ mit normalem Leerzeichen davor`,bad,[]);
  eq(`es gibt Links mit „&nbsp;↗“ (Prüfung greift)`,good>0,true);
}
console.log(fail?`\n${fail} von ${n} Prüfungen fehlgeschlagen.`:`\nAlle ${n} Prüfungen bestanden.`);process.exit(fail?1:0);
