#!/usr/bin/env python3
"""Erzeugt index.html aus katalog.json und den HTML-Dateien im selben Ordner.

Aufruf im Ordner der Trainer:   python3 build_index.py

- katalog.json enthält Kategorie, Niveau, Sprachen und Kurzbeschreibung je Datei.
- HTML-Dateien, die nicht in katalog.json stehen, erscheinen unter
  "Noch nicht zugeordnet" (Titel aus <title>), damit nichts verloren geht.
- Einträge in katalog.json, deren Datei fehlt, werden gemeldet und übersprungen.
"""
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
SPRACHEN = {
    "en": "Englisch", "ru": "Russisch", "uk": "Ukrainisch", "tr": "Türkisch",
    "ar": "Arabisch", "be": "Belarussisch", "bn": "Bengalisch", "fr": "Französisch",
}


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self._in = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in = False

    def handle_data(self, data):
        if self._in:
            self.title += data


def seitentitel(pfad):
    p = TitleParser()
    p.feed(pfad.read_text(encoding="utf-8", errors="replace"))
    return " ".join(p.title.split()) or pfad.stem


def main():
    katalog = json.loads((HERE / "katalog.json").read_text(encoding="utf-8"))
    vorhanden = {f.name for f in HERE.glob("*.html") if f.name != "index.html"}
    eintraege, fehlend = [], []

    for e in katalog["eintraege"]:
        if e["datei"] not in vorhanden:
            fehlend.append(e["datei"])
            continue
        e = dict(e)
        e["href"] = quote(e["datei"])
        eintraege.append(e)

    bekannt = {e["datei"] for e in katalog["eintraege"]}
    neu = sorted(vorhanden - bekannt)
    kategorien = list(katalog["kategorien"])
    if neu:
        kategorien.append({
            "id": "neu", "name": "Noch nicht zugeordnet", "farbe": "#5f6672",
            "text": "Neue Dateien. In katalog.json eintragen, dann erscheinen sie in der passenden Kategorie.",
        })
        for name in neu:
            eintraege.append({
                "datei": name, "href": quote(name), "titel": seitentitel(HERE / name),
                "kat": "neu", "niveau": "", "stufe": "", "sprachen": [], "text": "",
            })

    daten = {
        "titel": katalog["titel"],
        "hinweis": katalog.get("hinweis", ""),
        "sprachen": SPRACHEN,
        "kategorien": kategorien,
        "eintraege": eintraege,
    }
    # "</" maskieren, damit der JSON-Block das Script-Tag nie schließen kann
    blob = json.dumps(daten, ensure_ascii=False).replace("</", "<\\/")
    out = TEMPLATE.replace("__DATEN__", blob).replace("__TITEL__", katalog["titel"])
    (HERE / "index.html").write_text(out, encoding="utf-8")

    print(f"index.html geschrieben: {len(eintraege)} Einträge, {len(kategorien)} Kategorien")
    if neu:
        print("Noch nicht zugeordnet:", ", ".join(neu))
    if fehlend:
        print("In katalog.json, aber Datei fehlt:", ", ".join(fehlend), file=sys.stderr)


TEMPLATE = r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITEL__</title>
<style>
:root{
  --ink:#1d2433; --muted:#566074; --paper:#eef1f5; --card:#ffffff; --line:#d5dbe4;
  --focus:#0b57d0; --chip:#e4e9f0; --chip-on:#1d2433; --chip-on-text:#ffffff;
  --radius:10px;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ink:#e8ecf3; --muted:#a3adbf; --paper:#12161f; --card:#1b2130; --line:#2f384b;
    --focus:#8ab4ff; --chip:#27303f; --chip-on:#e8ecf3; --chip-on-text:#12161f;
  }
}
:root[data-theme="dark"]{
  --ink:#e8ecf3; --muted:#a3adbf; --paper:#12161f; --card:#1b2130; --line:#2f384b;
  --focus:#8ab4ff; --chip:#27303f; --chip-on:#e8ecf3; --chip-on-text:#12161f;
}
*{box-sizing:border-box}
html{scroll-padding-top:1rem}
body{margin:0;background:var(--paper);color:var(--ink);
  font:16px/1.5 "Avenir Next","Segoe UI",system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif}
a{color:inherit}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px;border-radius:4px}

.wrap{max-width:1180px;margin:0 auto;padding:0 16px 64px}
header{padding:32px 0 20px}
h1{margin:0 0 4px;font-size:clamp(1.6rem,3.2vw,2.3rem);line-height:1.15;letter-spacing:-.01em;font-weight:750}
.sub{margin:0;color:var(--muted);max-width:60ch}

.layout{display:grid;grid-template-columns:250px minmax(0,1fr);gap:28px;align-items:start}

/* Seitenleiste */
nav.cats{position:sticky;top:12px;display:flex;flex-direction:column;gap:2px}
nav.cats button{all:unset;box-sizing:border-box;cursor:pointer;display:flex;align-items:center;gap:10px;
  padding:8px 10px;border-radius:8px;color:var(--ink);line-height:1.3}
nav.cats button:hover{background:var(--chip)}
nav.cats button[aria-pressed="true"]{background:var(--card);box-shadow:inset 0 0 0 2px var(--c,var(--ink));font-weight:650}
nav.cats button:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
nav.cats .dot{flex:none;width:12px;height:12px;border-radius:3px;background:var(--c,var(--ink))}
nav.cats .n{margin-left:auto;color:var(--muted);font-variant-numeric:tabular-nums}

/* Werkzeugleiste */
.tools{display:grid;gap:12px;margin-bottom:22px}
.search{width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:var(--radius);
  background:var(--card);color:var(--ink);font:inherit}
.search::placeholder{color:var(--muted)}
.filters{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center}
.fg{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.fg .lbl{color:var(--muted);font-size:.9rem;margin-right:2px}
.chip{all:unset;box-sizing:border-box;cursor:pointer;padding:4px 11px;border-radius:999px;background:var(--chip);
  font-size:.9rem;line-height:1.4}
.chip:hover{filter:brightness(.96)}
.chip[aria-pressed="true"]{background:var(--chip-on);color:var(--chip-on-text)}
.chip:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.status{color:var(--muted);font-size:.95rem;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.status button{all:unset;cursor:pointer;text-decoration:underline;color:var(--ink)}
.status button:focus-visible{outline:3px solid var(--focus);outline-offset:2px}

/* Karteikasten: jede Kategorie ein Karteireiter mit Fach */
section.kat{margin:0 0 34px}
.reiter{display:inline-block;margin:0;padding:7px 16px 6px;border-radius:12px 12px 0 0;
  background:var(--c);color:#fff;font-size:1.05rem;font-weight:700;line-height:1.3}
.fach{background:var(--card);border:2px solid var(--c);border-radius:0 var(--radius) var(--radius) var(--radius);overflow:hidden}
.fach > .info{margin:0;padding:10px 16px;color:var(--muted);font-size:.95rem;border-bottom:1px solid var(--line)}
h3.gruppe{margin:0;padding:10px 16px 6px;font-size:.95rem;font-weight:700;color:var(--ink);background:color-mix(in srgb,var(--c) 9%,var(--card))}
ul.liste{list-style:none;margin:0;padding:0}
ul.liste li{position:relative;padding:12px 16px;border-top:1px solid var(--line)}
ul.liste li:first-child{border-top:0}
ul.liste li:hover{background:color-mix(in srgb,var(--c) 7%,var(--card))}
.titel{font-weight:650;font-size:1.05rem;line-height:1.3;text-decoration:none}
.titel::after{content:"";position:absolute;inset:0}   /* ganze Zeile klickbar */
.titel:hover{text-decoration:underline}
.text{margin:3px 0 0;color:var(--muted);max-width:75ch;font-size:.95rem}
.meta{margin:8px 0 0;display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:.85rem;position:relative;z-index:1;pointer-events:none}
.tag{padding:1px 8px;border-radius:6px;background:var(--chip);color:var(--ink)}
.tag.niv{background:color-mix(in srgb,var(--c) 18%,var(--card));font-weight:650}
.tag.leer{background:transparent;border:1px dashed var(--line);color:var(--muted)}
.datei{color:var(--muted);font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.8rem;word-break:break-all}
.leer-meldung{padding:40px 8px;text-align:center;color:var(--muted)}
.leer-meldung strong{display:block;color:var(--ink);font-size:1.1rem;margin-bottom:4px}
.hinweis{margin-top:40px;color:var(--muted);font-size:.9rem;max-width:70ch}

@media (max-width:820px){
  .layout{grid-template-columns:1fr;gap:14px}
  nav.cats{position:static;flex-direction:row;overflow-x:auto;padding-bottom:6px;gap:6px;scrollbar-width:thin}
  nav.cats button{flex:none;background:var(--chip);white-space:nowrap}
  nav.cats .n{margin-left:6px}
}
@media (prefers-reduced-motion:no-preference){
  ul.liste li{transition:background .12s}
}
@media print{
  nav.cats,.tools{display:none}
  .layout{display:block}
  ul.liste li{break-inside:avoid}
}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>__TITEL__</h1>
    <p class="sub" id="sub"></p>
  </header>

  <div class="layout">
    <nav class="cats" id="cats" aria-label="Kategorien"></nav>

    <main>
      <div class="tools">
        <input class="search" id="q" type="search" placeholder="Suchen nach Titel, Thema oder Dateiname" aria-label="Suchen">
        <div class="filters" id="filters"></div>
        <div class="status" id="status" aria-live="polite"></div>
      </div>
      <div id="out"></div>
      <p class="hinweis" id="hinweis"></p>
    </main>
  </div>
</div>

<script type="application/json" id="daten">__DATEN__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('daten').textContent);
  var sel = { kat: null, stufen: {}, sprachen: {}, q: '' };
  var katById = {}; D.kategorien.forEach(function(k){ katById[k.id] = k; });
  var STUFEN = [['A1','A1'],['A1/A2','A1 bis A2'],['B2','B2'],['','nicht angegeben']];

  function norm(s){ return (s||'').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/ß/g,'ss'); }
  function el(tag, cls, text){ var e=document.createElement(tag); if(cls) e.className=cls; if(text!=null) e.textContent=text; return e; }
  function anyOn(o){ return Object.keys(o).some(function(k){ return o[k]; }); }

  // verwendete Sprachen in fester Reihenfolge
  var spr = []; D.eintraege.forEach(function(e){ e.sprachen.forEach(function(s){ if(spr.indexOf(s)<0) spr.push(s); }); });
  var order = ['en','ru','uk','tr','ar','be','bn','fr'];
  spr.sort(function(a,b){ return order.indexOf(a)-order.indexOf(b); });

  function matches(e, ignoreKat){
    if(!ignoreKat && sel.kat && e.kat!==sel.kat) return false;
    if(anyOn(sel.stufen) && !sel.stufen[e.stufe||'']) return false;
    if(anyOn(sel.sprachen) && !e.sprachen.some(function(s){ return sel.sprachen[s]; })) return false;
    if(sel.q){
      var hay = norm([e.titel,e.text,e.datei,e.gruppe||'',e.niveau,e.sprachen.map(function(s){return D.sprachen[s]||s;}).join(' ')].join(' '));
      var words = norm(sel.q).split(/\s+/).filter(Boolean);
      for(var i=0;i<words.length;i++) if(hay.indexOf(words[i])<0) return false;
    }
    return true;
  }

  function renderNav(){
    var nav = document.getElementById('cats'); nav.textContent='';
    function btn(id, name, color, n){
      var b = el('button'); b.type='button';
      b.setAttribute('aria-pressed', String(sel.kat===id));
      if(color) b.style.setProperty('--c', color);
      var dot = el('span','dot'); b.appendChild(dot);
      b.appendChild(el('span',null,name));
      b.appendChild(el('span','n',String(n)));
      b.addEventListener('click', function(){ sel.kat = (sel.kat===id ? null : id); render(); });
      nav.appendChild(b);
    }
    var total = D.eintraege.filter(function(e){ return matches(e,true); }).length;
    var all = el('button'); all.type='button'; all.setAttribute('aria-pressed', String(sel.kat===null));
    all.style.setProperty('--c','var(--ink)');
    all.appendChild(el('span','dot'));
    all.appendChild(el('span',null,'Alle Kategorien'));
    all.appendChild(el('span','n',String(total)));
    all.addEventListener('click', function(){ sel.kat=null; render(); });
    nav.appendChild(all);
    D.kategorien.forEach(function(k){
      var n = D.eintraege.filter(function(e){ return e.kat===k.id && matches(e,true); }).length;
      btn(k.id, k.name, k.farbe, n);
    });
  }

  function renderFilters(){
    var f = document.getElementById('filters'); f.textContent='';
    function group(label, items, store){
      var g = el('div','fg'); g.setAttribute('role','group'); g.setAttribute('aria-label',label);
      g.appendChild(el('span','lbl',label));
      items.forEach(function(it){
        var c = el('button','chip',it[1]); c.type='button';
        c.setAttribute('aria-pressed', String(!!store[it[0]]));
        c.addEventListener('click', function(){ store[it[0]] = !store[it[0]]; render(); });
        g.appendChild(c);
      });
      f.appendChild(g);
    }
    group('Niveau', STUFEN, sel.stufen);
    group('Hilfssprache', spr.map(function(s){ return [s, D.sprachen[s]||s]; }), sel.sprachen);
  }

  function renderList(){
    var out = document.getElementById('out'); out.textContent='';
    var shown = 0;
    D.kategorien.forEach(function(k){
      var items = D.eintraege.filter(function(e){ return e.kat===k.id && matches(e,false); });
      if(!items.length) return;
      shown += items.length;
      var sec = el('section','kat'); sec.style.setProperty('--c', k.farbe); sec.id = 'kat-'+k.id;
      var h = el('h2','reiter',k.name); sec.appendChild(h);
      var fach = el('div','fach');
      if(k.text) fach.appendChild(el('p','info',k.text));
      var ul = el('ul','liste'); var lastGroup = null; var holder = fach;
      // Gruppen: Überschrift, danach eigene Liste
      var cur = null;
      items.forEach(function(e){
        var g = e.gruppe || '';
        if(g !== lastGroup){
          if(g){ fach.appendChild(el('h3','gruppe',g)); }
          cur = el('ul','liste'); fach.appendChild(cur); lastGroup = g;
        }
        var li = el('li');
        var a = el('a','titel',e.titel); a.href = e.href;
        li.appendChild(a);
        if(e.text) li.appendChild(el('p','text',e.text));
        var m = el('div','meta');
        m.appendChild(e.niveau ? el('span','tag niv','Niveau '+e.niveau) : el('span','tag leer','Niveau nicht angegeben'));
        if(e.sprachen.length){
          e.sprachen.forEach(function(s){ m.appendChild(el('span','tag',D.sprachen[s]||s)); });
        } else {
          m.appendChild(el('span','tag leer','Hilfssprache: keine'));
        }
        m.appendChild(el('span','datei',e.datei));
        li.appendChild(m);
        cur.appendChild(li);
      });
      sec.appendChild(fach);
      out.appendChild(sec);
    });
    if(!shown){
      var d = el('div','leer-meldung');
      d.appendChild(el('strong',null,'Keine Treffer'));
      d.appendChild(el('span',null,'Suchbegriff kürzen oder Filter zurücksetzen.'));
      out.appendChild(d);
    }
    var st = document.getElementById('status'); st.textContent='';
    st.appendChild(el('span',null, shown+' von '+D.eintraege.length+' Dateien'));
    if(sel.kat || anyOn(sel.stufen) || anyOn(sel.sprachen) || sel.q){
      var r = el('button',null,'Filter zurücksetzen'); r.type='button';
      r.addEventListener('click', function(){ sel={kat:null,stufen:{},sprachen:{},q:''}; document.getElementById('q').value=''; render(); });
      st.appendChild(r);
    }
  }

  function render(){ renderNav(); renderFilters(); renderList(); }

  document.getElementById('sub').textContent = D.eintraege.length+' Trainer und Übungen. Ein Klick auf eine Zeile öffnet die Datei.';
  document.getElementById('hinweis').textContent = D.hinweis || '';
  document.getElementById('q').addEventListener('input', function(ev){ sel.q = ev.target.value; renderNav(); renderList(); });
  render();
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
