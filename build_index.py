#!/usr/bin/env python3
"""Erzeugt index.html aus katalog.json, uebersetzungen.json und den HTML-Dateien im selben Ordner.

Aufruf im Ordner der Trainer:   python3 build_index.py

- katalog.json enthält Kategorie, Niveau, Sprachen und die deutsche Kurzbeschreibung je Datei.
- uebersetzungen.json enthält die Übersetzungen (en, ar, uk, ru, tr) der Oberfläche,
  der Kategorien und der Einträge. Fehlt eine Übersetzung, zeigt die Seite den deutschen Text.
- HTML-Dateien, die nicht in katalog.json stehen, erscheinen unter
  "Noch nicht zugeordnet" (Titel aus <title>), damit nichts verloren geht.
- Einträge in katalog.json, deren Datei fehlt, werden gemeldet und übersprungen.
"""
import json
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
DEFAULT_I18N = {
    "sprachen": ["de"], "namen": {"de": "Deutsch"}, "rtl": [], "ui": {}, "sprachnamen": {},
    "kategorien": {}, "gruppen": {}, "eintraege": {},
}
DE_SPRACHNAMEN = {
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


def lade_i18n():
    pfad = HERE / "uebersetzungen.json"
    if not pfad.exists():
        print("Hinweis: uebersetzungen.json fehlt, die Seite erscheint nur auf Deutsch.", file=sys.stderr)
        return dict(DEFAULT_I18N)
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    out = dict(DEFAULT_I18N)
    out.update({k: v for k, v in daten.items() if not k.startswith("_")})
    return out


def main():
    katalog = json.loads((HERE / "katalog.json").read_text(encoding="utf-8"))
    i18n = lade_i18n()
    vorhanden = {f.name for f in HERE.glob("*.html") if f.name != "index.html"}
    eintraege, fehlend = [], []

    for e in katalog["eintraege"]:
        if e["datei"] not in vorhanden:
            fehlend.append(e["datei"])
            continue
        e = dict(e)
        e["href"] = quote(e["datei"])
        e["t"] = i18n["eintraege"].get(e["datei"], {})
        eintraege.append(e)

    bekannt = {e["datei"] for e in katalog["eintraege"]}
    neu = sorted(vorhanden - bekannt)
    kategorien = [dict(k, t=i18n["kategorien"].get(k["id"], {})) for k in katalog["kategorien"]]
    if neu:
        kategorien.append({
            "id": "neu", "name": "Noch nicht zugeordnet", "farbe": "#5f6672",
            "text": "Neue Dateien. In katalog.json eintragen, dann erscheinen sie in der passenden Kategorie.",
            "t": i18n["kategorien"].get("neu", {}),
        })
        for name in neu:
            eintraege.append({
                "datei": name, "href": quote(name), "titel": seitentitel(HERE / name),
                "kat": "neu", "niveau": "", "stufe": "", "sprachen": [], "text": "", "t": {},
            })

    sprachnamen = dict(i18n["sprachnamen"])
    sprachnamen.setdefault("de", DE_SPRACHNAMEN)
    ui = dict(i18n["ui"])
    ui.setdefault("de", {})

    daten = {
        "titel": katalog["titel"],
        "stand": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "hinweis": katalog.get("hinweis", ""),
        "kategorien": kategorien,
        "eintraege": eintraege,
        "i18n": {
            "sprachen": i18n["sprachen"], "namen": i18n["namen"], "rtl": i18n["rtl"],
            "ui": ui, "sprachnamen": sprachnamen, "gruppen": i18n["gruppen"],
        },
    }
    # "</" maskieren, damit der JSON-Block das Script-Tag nie schließen kann
    blob = json.dumps(daten, ensure_ascii=False).replace("</", "<\\/")
    out = TEMPLATE.replace("__DATEN__", blob).replace("__TITEL__", katalog["titel"])
    (HERE / "index.html").write_text(out, encoding="utf-8")

    print(f"index.html geschrieben: {len(eintraege)} Einträge, {len(kategorien)} Kategorien, "
          f"{len(i18n['sprachen'])} Sprachen")
    ohne = sorted({e["datei"] for e in eintraege if e["kat"] != "neu"
                   for l in i18n["sprachen"] if l != "de" and l not in e["t"]})
    if ohne:
        print("Ohne vollständige Übersetzung (zeigen deutschen Text):", ", ".join(ohne))
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
header{padding:32px 0 20px;display:flex;flex-wrap:wrap;gap:12px 24px;justify-content:space-between;align-items:flex-start}
.kopf{flex:1 1 420px;min-width:0}
h1{margin:0 0 4px;font-size:clamp(1.6rem,3.2vw,2.3rem);line-height:1.15;letter-spacing:-.01em;font-weight:750}
.sub{margin:0;color:var(--muted);max-width:60ch}
.sprachwahl{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px}
.sprachwahl .lbl{color:var(--muted);font-size:.9rem}
.sprache{display:flex;flex-wrap:wrap;gap:6px}
.fehler{margin:0 0 16px;padding:10px 14px;border:2px solid #b3261e;border-radius:var(--radius);background:var(--card);font-size:.95rem}
.fehler code{word-break:break-word;font-size:.85rem}
.stand{margin:8px 0 0;color:var(--muted);font-size:.8rem}

.layout{display:grid;grid-template-columns:250px minmax(0,1fr);gap:28px;align-items:start}

/* Seitenleiste */
nav.cats{position:sticky;top:12px;display:flex;flex-direction:column;gap:2px}
nav.cats button{all:unset;box-sizing:border-box;cursor:pointer;display:flex;align-items:center;gap:10px;
  padding:8px 10px;border-radius:8px;color:var(--ink);line-height:1.3}
nav.cats button:hover{background:var(--chip)}
nav.cats button[aria-pressed="true"]{background:var(--card);box-shadow:inset 0 0 0 2px var(--c,var(--ink));font-weight:650}
nav.cats button:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
nav.cats .dot{flex:none;width:12px;height:12px;border-radius:3px;background:var(--c,var(--ink))}
nav.cats .n{margin-inline-start:auto;color:var(--muted);font-variant-numeric:tabular-nums}

/* Werkzeugleiste */
.tools{display:grid;gap:12px;margin-bottom:22px}
.search{width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:var(--radius);
  background:var(--card);color:var(--ink);font:inherit}
.search::placeholder{color:var(--muted)}
.filters{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center}
.fg{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.fg .lbl{color:var(--muted);font-size:.9rem;margin-inline-end:2px}
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
.fach{background:var(--card);border:2px solid var(--c);border-radius:var(--radius);
  border-start-start-radius:0;overflow:hidden}
.fach > .info{margin:0;padding:10px 16px;color:var(--muted);font-size:.95rem;border-bottom:1px solid var(--line)}
h3.gruppe{margin:0;padding:10px 16px 6px;font-size:.95rem;font-weight:700;color:var(--ink);background:color-mix(in srgb,var(--c) 9%,var(--card))}
ul.liste{list-style:none;margin:0;padding:0}
ul.liste li{position:relative;padding:12px 16px;border-top:1px solid var(--line)}
ul.liste li:first-child{border-top:0}
ul.liste li:hover{background:color-mix(in srgb,var(--c) 7%,var(--card))}
.titel{font-weight:650;font-size:1.05rem;line-height:1.3;text-decoration:none}
.titel::after{content:"";position:absolute;inset:0}   /* ganze Zeile klickbar */
.titel:hover{text-decoration:underline}
.orig{margin:2px 0 0;color:var(--muted);font-size:.85rem;direction:ltr;text-align:start;unicode-bidi:isolate}
html[dir="rtl"] .orig{text-align:right}
.text{margin:3px 0 0;color:var(--muted);max-width:75ch;font-size:.95rem}
.meta{margin:8px 0 0;display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:.85rem;position:relative;z-index:1;pointer-events:none}
.tag{padding:1px 8px;border-radius:6px;background:var(--chip);color:var(--ink)}
.tag.niv{background:color-mix(in srgb,var(--c) 18%,var(--card));font-weight:650}
.tag.leer{background:transparent;border:1px dashed var(--line);color:var(--muted)}
.datei{color:var(--muted);font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.8rem;word-break:break-all;
  direction:ltr;unicode-bidi:isolate}
.leer-meldung{padding:40px 8px;text-align:center;color:var(--muted)}
.leer-meldung strong{display:block;color:var(--ink);font-size:1.1rem;margin-bottom:4px}
.hinweis{margin-top:40px;color:var(--muted);font-size:.9rem;max-width:70ch}

@media (max-width:820px){
  .layout{grid-template-columns:1fr;gap:14px}
  nav.cats{position:static;flex-direction:row;overflow-x:auto;padding-bottom:6px;gap:6px;scrollbar-width:thin}
  nav.cats button{flex:none;background:var(--chip);white-space:nowrap}
  nav.cats .n{margin-inline-start:6px}
}
@media (prefers-reduced-motion:no-preference){
  ul.liste li{transition:background .12s}
}
@media print{
  nav.cats,.tools,.sprache{display:none}
  .layout{display:block}
  ul.liste li{break-inside:avoid}
}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="kopf">
      <h1 id="h1">__TITEL__</h1>
      <p class="sub" id="sub"></p>
    </div>
    <div class="sprachwahl">
      <span class="lbl" id="sprachlabel">Sprache der Seite</span>
      <div class="sprache" id="sprache" role="group"></div>
    </div>
  </header>
  <p class="fehler" id="fehler" role="alert" hidden></p>
  <noscript><p class="fehler">JavaScript is required / JavaScript wird benötigt.</p></noscript>

  <div class="layout">
    <nav class="cats" id="cats"></nav>

    <main>
      <div class="tools">
        <input class="search" id="q" type="search">
        <div class="filters" id="filters"></div>
        <div class="status" id="status" aria-live="polite"></div>
      </div>
      <div id="out"></div>
      <p class="hinweis" id="hinweis"></p>
      <p class="stand" id="stand"></p>
    </main>
  </div>
</div>

<script type="application/json" id="daten">__DATEN__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('daten').textContent);
  var I = D.i18n;
  var sel = { kat: null, stufen: {}, sprachen: {}, q: '' };
  var lang = 'de';
  var STUFEN = [['A1','lvl_a1'],['A1/A2','lvl_a1a2'],['B2','lvl_b2'],['','lvl_none']];

  // ---- Hilfsfunktionen
  function norm(s){
    return (s||'').toLowerCase().normalize('NFD')
      .replace(/[̀-ًͯ-ٰٟ]/g,'').replace(/ß/g,'ss');
  }
  function el(tag, cls, text){ var e=document.createElement(tag); if(cls) e.className=cls; if(text!=null) e.textContent=text; return e; }
  function anyOn(o){ return Object.keys(o).some(function(k){ return o[k]; }); }
  function ui(key, vars){
    var s = (I.ui[lang] && I.ui[lang][key]) || (I.ui.de && I.ui.de[key]) || key;
    if(vars) Object.keys(vars).forEach(function(k){ s = s.split('{'+k+'}').join(vars[k]); });
    return s;
  }
  function field(obj, f){ var t = obj.t && obj.t[lang]; return (t && t[f]) || obj[f] || ''; }
  function spName(code){ var m = I.sprachnamen[lang] || I.sprachnamen.de || {}; return m[code] || (I.sprachnamen.de||{})[code] || code; }
  function groupName(g){ var t = I.gruppen && I.gruppen[g]; return (t && t[lang]) || g; }
  function store(){ try{ return window.localStorage; }catch(e){ return null; } }

  var katById = {}; D.kategorien.forEach(function(k){ katById[k.id] = k; });

  // verwendete Hilfssprachen in fester Reihenfolge
  var spr = []; D.eintraege.forEach(function(e){ e.sprachen.forEach(function(s){ if(spr.indexOf(s)<0) spr.push(s); }); });
  var order = ['en','ru','uk','tr','ar','be','bn','fr'];
  spr.sort(function(a,b){ return order.indexOf(a)-order.indexOf(b); });

  // ---- Seitensprache bestimmen: ?lang=… vor gespeicherter Wahl vor Browsersprache
  function valid(l){ return I.sprachen.indexOf(l) >= 0; }
  function startLang(){
    var m = /[?&]lang=([a-z]{2})/i.exec(location.search || '');
    if(m && valid(m[1].toLowerCase())) return m[1].toLowerCase();
    var s = store(), saved = null;
    try{ saved = s && s.getItem('sprache'); }catch(e){}
    if(saved && valid(saved)) return saved;
    var nav = (navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || 'de']);
    for(var i=0;i<nav.length;i++){ var c = String(nav[i]).slice(0,2).toLowerCase(); if(valid(c)) return c; }
    return 'de';
  }

  function matches(e, ignoreKat){
    if(!ignoreKat && sel.kat && e.kat!==sel.kat) return false;
    if(anyOn(sel.stufen) && !sel.stufen[e.stufe||'']) return false;
    if(anyOn(sel.sprachen) && !e.sprachen.some(function(s){ return sel.sprachen[s]; })) return false;
    if(sel.q){
      // durchsucht die gewählte Sprache und zusätzlich das deutsche Original
      var hay = norm([field(e,'titel'),field(e,'text'),e.titel,e.text,e.datei,e.gruppe||'',e.niveau,
        e.sprachen.map(spName).join(' ')].join(' '));
      var words = norm(sel.q).split(/\s+/).filter(Boolean);
      for(var i=0;i<words.length;i++) if(hay.indexOf(words[i])<0) return false;
    }
    return true;
  }

  function renderLangSwitch(){
    var box = document.getElementById('sprache'); box.textContent='';
    box.setAttribute('aria-label', ui('lang_aria'));
    I.sprachen.forEach(function(l){
      var b = el('button','chip',I.namen[l]||l); b.type='button';
      b.lang = l; b.setAttribute('aria-pressed', String(l===lang));
      b.addEventListener('click', function(){ setLang(l, true); });
      box.appendChild(b);
    });
  }

  function renderNav(){
    var nav = document.getElementById('cats'); nav.textContent='';
    nav.setAttribute('aria-label', ui('cats_aria'));
    function btn(id, name, color, n){
      var b = el('button'); b.type='button';
      b.setAttribute('aria-pressed', String(sel.kat===id));
      if(color) b.style.setProperty('--c', color);
      b.appendChild(el('span','dot'));
      b.appendChild(el('span',null,name));
      b.appendChild(el('span','n',String(n)));
      b.addEventListener('click', function(){ sel.kat = (sel.kat===id ? null : id); render(); });
      nav.appendChild(b);
    }
    var total = D.eintraege.filter(function(e){ return matches(e,true); }).length;
    var all = el('button'); all.type='button'; all.setAttribute('aria-pressed', String(sel.kat===null));
    all.style.setProperty('--c','var(--ink)');
    all.appendChild(el('span','dot'));
    all.appendChild(el('span',null,ui('all_cats')));
    all.appendChild(el('span','n',String(total)));
    all.addEventListener('click', function(){ sel.kat=null; render(); });
    nav.appendChild(all);
    D.kategorien.forEach(function(k){
      var n = D.eintraege.filter(function(e){ return e.kat===k.id && matches(e,true); }).length;
      btn(k.id, field(k,'name'), k.farbe, n);
    });
  }

  function renderFilters(){
    var f = document.getElementById('filters'); f.textContent='';
    function group(label, items, st){
      var g = el('div','fg'); g.setAttribute('role','group'); g.setAttribute('aria-label',label);
      g.appendChild(el('span','lbl',label));
      items.forEach(function(it){
        var c = el('button','chip',it[1]); c.type='button';
        c.setAttribute('aria-pressed', String(!!st[it[0]]));
        c.addEventListener('click', function(){ st[it[0]] = !st[it[0]]; render(); });
        g.appendChild(c);
      });
      f.appendChild(g);
    }
    group(ui('level'), STUFEN.map(function(s){ return [s[0], ui(s[1])]; }), sel.stufen);
    group(ui('help'), spr.map(function(s){ return [s, spName(s)]; }), sel.sprachen);
  }

  function renderList(){
    var out = document.getElementById('out'); out.textContent='';
    var shown = 0;
    D.kategorien.forEach(function(k){
      var items = D.eintraege.filter(function(e){ return e.kat===k.id && matches(e,false); });
      if(!items.length) return;
      shown += items.length;
      var sec = el('section','kat'); sec.style.setProperty('--c', k.farbe); sec.id = 'kat-'+k.id;
      sec.appendChild(el('h2','reiter',field(k,'name')));
      var fach = el('div','fach');
      var kt = field(k,'text');
      if(kt) fach.appendChild(el('p','info',kt));
      var lastGroup = null, cur = null;
      items.forEach(function(e){
        var g = e.gruppe || '';
        if(g !== lastGroup){
          if(g) fach.appendChild(el('h3','gruppe',groupName(g)));
          cur = el('ul','liste'); fach.appendChild(cur); lastGroup = g;
        }
        var li = el('li');
        var shownTitle = field(e,'titel');
        var a = el('a','titel',shownTitle); a.href = e.href;
        li.appendChild(a);
        if(lang !== 'de' && e.titel && e.titel !== shownTitle){
          var o = el('p','orig',e.titel); o.lang = 'de'; li.appendChild(o);
        }
        var tx = field(e,'text');
        if(tx) li.appendChild(el('p','text',tx));
        var m = el('div','meta');
        m.appendChild(e.niveau ? el('span','tag niv',ui('tag_level',{x:e.niveau})) : el('span','tag leer',ui('tag_level_none')));
        if(e.sprachen.length){
          e.sprachen.forEach(function(s){ m.appendChild(el('span','tag',spName(s))); });
        } else {
          m.appendChild(el('span','tag leer',ui('tag_help_none')));
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
      d.appendChild(el('strong',null,ui('none_title')));
      d.appendChild(el('span',null,ui('none_text')));
      out.appendChild(d);
    }
    var st = document.getElementById('status'); st.textContent='';
    st.appendChild(el('span',null, ui('count',{n:shown,total:D.eintraege.length})));
    if(sel.kat || anyOn(sel.stufen) || anyOn(sel.sprachen) || sel.q){
      var r = el('button',null,ui('reset')); r.type='button';
      r.addEventListener('click', function(){ sel={kat:null,stufen:{},sprachen:{},q:''}; document.getElementById('q').value=''; render(); });
      st.appendChild(r);
    }
  }

  function renderTexts(){
    var t = ui('titel');
    document.title = t;
    document.getElementById('h1').textContent = t;
    document.getElementById('sub').textContent = ui('sub',{n:D.eintraege.length});
    document.getElementById('hinweis').textContent = ui('hinweis');
    document.getElementById('sprachlabel').textContent = ui('lang_aria');
    document.getElementById('stand').textContent = ui('stand',{d:D.stand});
    var q = document.getElementById('q');
    q.placeholder = ui('search_ph'); q.setAttribute('aria-label', ui('search_aria'));
  }

  function render(){ renderLangSwitch(); renderNav(); renderFilters(); renderList(); }

  // Zeigt einen Fehler sichtbar an, statt still zu scheitern (hilft bei der Fehlersuche im Browser)
  function zeigeFehler(err){
    var box = document.getElementById('fehler');
    box.textContent = '';
    box.appendChild(el('strong',null,ui('fehler')+' '));
    box.appendChild(el('code',null,String(err && err.message || err)+' | '+navigator.userAgent));
    box.hidden = false;
  }

  function setLang(l, save){
    try{
      lang = l;
      var root = document.documentElement;
      root.lang = l;
      root.dir = (I.rtl && I.rtl.indexOf(l) >= 0) ? 'rtl' : 'ltr';
      if(save){ try{ var s = store(); if(s) s.setItem('sprache', l); }catch(e){} }
      document.getElementById('fehler').hidden = true;
      renderTexts();
      render();
    }catch(err){ zeigeFehler(err); }
  }

  document.getElementById('q').addEventListener('input', function(ev){ sel.q = ev.target.value; renderNav(); renderList(); });
  setLang(startLang(), false);
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
