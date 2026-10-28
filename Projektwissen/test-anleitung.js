// Prüft die Anleitung mit Bildern (GitHub/anleitung.html) gegen das Tool (ohne Browser, mit dem Loader aus test-050n1):
// Jeder Text zwischen <!--Q:quelle--> und <!--/Q--> muss wortgleich im Tool stehen. Ab 0.50 Nachtrag 9 sind das nur noch die Schritt-Listen (SCHRITTE),
// jede andere Quelle ist ein Fehler, und in diesen Blöcken darf „hier“ nicht stehen (außer im Namen des Felds „Hier einfügen“), weil es auf der Seite
// nicht stimmt. Quellen: „js:Ausdruck“ (im geladenen Hauptskript ausgewertet,
// Listen mit Leerzeichen verbunden) und „html:#id“ bzw. „html:tag[attr=wert]“ (Element direkt aus trading-bilanz.html). Verglichen wird der Text ohne Tags
// und mit zusammengefasstem Leerraum. In der Anleitung fallen vorher weg: Zusätze <!--Z-->…<!--/Z--> und Bilder (<figure>). Im Tool fällt der Knopf
// „Wozu?“ weg (in der Anleitung steht der Text offen). Dazu: Pflicht-Quellen vorhanden, Bilder vorhanden und benutzt, jedes mit alt, Sprungmarken
// der Links im Tool vorhanden, kein Skript. Platzhalter für Florians Bilder sind nur ein Hinweis („Bild fehlt noch“), kein Fehler.
// Aufruf im Projektordner:  node tools/test-anleitung.js
"use strict";
const fs=require('fs'),path=require('path');
const {load,run,strip}=require('./test-050n1.js');
const ROOT=path.join(__dirname,'..'),GH=path.join(ROOT,'GitHub'),IMG=path.join(GH,'anleitung');
// HTMLF = andere Fassung des Tools (Gegenprobe), wie bei test-050n1
const H=fs.readFileSync(process.env.HTMLF||path.join(ROOT,'trading-bilanz.html'),'utf8');
// ANLF = andere Fassung der Anleitung (Gegenprobe, z. B. mit „hier“ in einer Schritt-Liste)
const A=fs.readFileSync(process.env.ANLF||path.join(GH,'anleitung.html'),'utf8');
let fail=0,n=0;const notes=[];
function eq(name,got,exp,more){n++;const ok=JSON.stringify(got)===JSON.stringify(exp);if(!ok)fail++;
  console.log((ok?'  ok     ':'  FEHLER ')+name+(ok?'':more?'\n'+more:`  →  ist ${JSON.stringify(got).slice(0,800)}, soll ${JSON.stringify(exp)}`))}
const end=()=>{for(const x of notes)console.log('  Hinweis '+x);console.log(fail?`\n${fail} von ${n} Prüfungen fehlgeschlagen.`:`\nAlle ${n} Prüfungen bestanden.`);process.exit(fail?1:0)};

// Die Schritt-Listen: nur diese stehen wortgleich in der Anleitung, alle Pflicht
const JM=String.raw`js:stepsHTML(false).match(/<div class="chkm">[\s\S]*?(<ol[\s\S]*?<\/ol>)/)[1]`;
const MUST=["js:MT5_CONNECT.win","js:MT5_SAVE.win","js:tagGuide('win')","js:STEPS.slice(0,5)",JM];
// Block-Grenzen (Listenpunkt, Absatz) zählen als Leerraum, sonst klebt „neu.</li><li>Ziehe“ zusammen
const norm=h=>strip(String(h).replace(/<!--Z-->[\s\S]*?<!--\/Z-->/g,'').replace(/<figure>[\s\S]*?<\/figure>/g,'').replace(/<\/?(li|p|div|ol|ul|br|h\d)\b[^>]*>/g,' ')).replace(/\s+/g,' ').trim();
const ctx=load({});
function src(q){
  if(q.startsWith('js:')){const v=run(ctx,q.slice(3));return Array.isArray(v)?v.join(' '):v}
  const m=q.match(/^html:(?:#([\w-]+)|(\w+)\[([\w-]+)=([^\]]+)\])$/);if(!m)throw new Error('unbekannte Quelle');
  const re=m[1]?new RegExp(`<(\\w+)[^>]*\\bid="${m[1]}"[^>]*>([\\s\\S]*?)</\\1>`):new RegExp(`<(${m[2]})[^>]*\\b${m[3]}="${m[4]}"[^>]*>([\\s\\S]*?)</\\1>`);
  const r=H.match(re);if(!r)throw new Error('nicht im Tool gefunden');return r[2]}
// Erste Stelle, an der sich zwei Texte unterscheiden, mit etwas Umgebung
function diff(a,b){let i=0;while(i<a.length&&a[i]===b[i])i++;const cut=s=>(i>40?'…':'')+s.slice(Math.max(0,i-40),i+60)+'…';
  return `           ab Zeichen ${i}:\n           Anleitung: ${cut(a)}\n           Tool:      ${cut(b)}`}

console.log('Texte wortgleich mit dem Tool');
const Q=[...A.matchAll(/<!--Q:([\s\S]*?)-->([\s\S]*?)<!--\/Q-->/g)];
for(const [,q,body] of Q){let s;try{s=src(q)}catch(e){eq(`${q}: Quelle im Tool`,e.message,'vorhanden');continue}
  const a=norm(body),b=norm(String(s).replace(/<button[^>]*data-gtwhy[^>]*>[\s\S]*?<\/button>/g,''));
  eq(`${q} (${a.length} Zeichen)`,a===b,true,a===b?'':diff(a,b));
  eq(`${q}: kein „hier“ (außer „Hier einfügen“)`,(a.replace(/Hier einfügen/g,'').match(/[^.!?„]*\bhier\b[^.!?“]*/gi)||[]).map(s=>s.trim()),[])}
const have=new Set(Q.map(m=>m[1]));
eq('Pflicht-Quellen (Schritt-Listen) in der Anleitung',MUST.filter(q=>!have.has(q)),[]);
eq('nur Schritt-Listen wortgleich, keine anderen Quellen',[...have].filter(q=>!MUST.includes(q)),[]);

console.log('Bilder');
const used=[...A.matchAll(/<img\b[^>]*>/g)].map(m=>m[0]);
const files=fs.existsSync(IMG)?fs.readdirSync(IMG):[];
const srcOf=t=>(t.match(/\bsrc="anleitung\/([^"]+)"/)||[])[1];
eq('jedes Bild liegt in GitHub/anleitung/',used.map(srcOf).filter(f=>!f||!files.includes(f)),[]);
eq('jedes Bild hat alt, width und height',used.filter(t=>!/\balt="[^"]+"/.test(t)||!/\bwidth="\d+"/.test(t)||!/\bheight="\d+"/.test(t)).map(srcOf),[]);
eq('jedes Bild ist ein Link auf sich selbst (Vergrößern)',[...A.matchAll(/<a href="([^"]*)"><img src="([^"]*)"/g)].filter(m=>m[1]!==m[2]).map(m=>m[2]).concat(used.length-(A.match(/<a href="anleitung\/[^"]+"><img /g)||[]).length?['ohne Link']:[]),[]);
const ph=[...A.matchAll(/<div class="ph" data-bild="([\w-]+)"/g)].map(m=>m[1]);
eq('jede Datei in GitHub/anleitung/ wird verwendet',files.filter(f=>!used.some(t=>srcOf(t)===f)&&!ph.includes(f.replace(/\.webp$/,''))),[]);
const FR=Object.keys(JSON.parse(fs.readFileSync(path.join(__dirname,'anleitung-fremd.json'),'utf8'))).filter(k=>k[0]!=='_');
eq('jedes Bild aus anleitung-fremd.json steht in der Anleitung (Bild oder Platzhalter)',FR.filter(k=>!ph.includes(k)&&!used.some(t=>srcOf(t)===k+'.webp')),[]);
for(const k of [...new Set(ph)])notes.push(files.includes(k+'.webp')?`Bild ${k}.webp ist da, steht aber noch als Platzhalter: node tools/anleitung-fremd.js ${k}`:`Bild fehlt noch: ${k}`);

console.log('Seite');
eq('kein Skript in der Anleitung',/<script\b/i.test(A),false);
eq('Content-Security-Policy: nur eigene Bilder, kein Skript',/<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">/.test(A),true);
const ids=new Set([...A.matchAll(/\bid="([\w-]+)"/g)].map(m=>m[1]));
const anch=[...H.matchAll(/https:\/\/trading-bilanz\.github\.io\/anleitung\.html(?:#([\w-]+))?"/g)];
eq('Links im Tool zur Anleitung (mindestens 4)',anch.length>=4,true);
eq('Sprungmarken der Links im Tool gibt es in der Anleitung',anch.map(m=>m[1]).filter(x=>x&&!ids.has(x)),[]);
eq('Inhaltsverzeichnis zeigt nur auf vorhandene Abschnitte',[...A.matchAll(/href="#([\w-]+)"/g)].map(m=>m[1]).filter(x=>!ids.has(x)),[]);
// Ab 0.53: Gliederung nach den Reitern, „↑ Inhalt“ in jedem Abschnitt, Links aus dem Tool in den Teil Wallet
const toc=(A.match(/<nav class="toc" id="inhalt"[\s\S]*?<\/nav>/)||[''])[0];
eq('Inhalt (#inhalt) mit den Reitern als Gruppen',[...toc.matchAll(/<a class="grp" href="#(reiter-[\w-]+)">/g)].map(m=>m[1]),['reiter-reports','reiter-kurse','reiter-wallet']);
eq('Reiter-Überschriften mit eigener Sprungmarke',[...A.matchAll(/<h2 class="reiter" id="([\w-]+)">/g)].map(m=>m[1]),['reiter-reports','reiter-kurse','reiter-wallet']);
const secs=[...A.matchAll(/<section id="([\w-]+)">([\s\S]*?)<\/section>/g)];
eq('Abschnitte 1 bis 12 in dieser Reihenfolge',secs.map(m=>m[1]),['start','mt5-verbinden','report-speichern','reports-laden','trading-benefit','kurse','tag-daten','noch-offen','boerse-datei','von-hand','abarbeiten','weiter']);
eq('jeder Abschnitt endet mit „↑ Inhalt“',secs.filter(m=>!/<p class="up"><a href="#inhalt">↑ Inhalt<\/a><\/p>\s*$/.test(m[2])).map(m=>m[1]),[]);
eq('Links aus dem Tool in den Teil Wallet',['reiter-wallet','noch-offen','boerse-datei','von-hand'].filter(x=>!anch.some(m=>m[1]===x)),[]);
end();
