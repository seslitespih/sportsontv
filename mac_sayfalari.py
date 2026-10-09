# -*- coding: utf-8 -*-
"""Her maça ayrı sayfa — İspanyolca ve Fransızca (Eki 2026).

NEDEN: İnsanlar "málaga espanyol canal" / "lens lyon quelle chaîne" diye
maç maç arıyor. Genel "bugün maçlar" sayfasıyla bu aramaları yakalayamıyoruz.
Her maç için o ülkenin kanalı, saati ve diğer ülkelerdeki yayıncılarla ayrı
sayfa üretilir.

NASIL: build_site.py her derlemede yaz() çağırır. matches-daily.json'daki
maçlar maclar_arsiv.json'a eklenir (veri her derlemede en güncel hâliyle
yenilenir), başlama saatinden SAKLA_GUN gün sonra arşivden ve diskten silinir.
Yani sayfa maçtan önceki gün açılır, maç günü aranır, birkaç gün sonra kalkar.
Slug ilk görüldüğünde arşive yazılır ve değişmez — URL sabit kalsın.

Yalnız o ülkede kanalı belli olan takım maçları (futbol/basketbol/voleybol).
Kanalı belirsiz maça sayfa açmak boş içerik olur.
"""
import json, os, re, shutil, unicodedata, datetime
from zoneinfo import ZoneInfo
import prerender

KOK = os.path.dirname(os.path.abspath(__file__))
ARSIV = os.path.join(KOK, "maclar_arsiv.json")
ULKE_ADLARI = json.load(open(os.path.join(KOK, "ulke_adlari.json"), encoding="utf-8"))
SAKLA_GUN = 3
BITTI_DK = 130          # app.js statusOf ile aynı: başlama + 130 dk = bitti
SPORLAR = {"football", "basketball", "volleyball"}

DIL = {
 "es": dict(ulke="ES", tz="Europe/Madrid", klasor="partido",
   gun=["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
   ay=["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
       "septiembre", "octubre", "noviembre", "diciembre"],
   ve=" y ",
   title="{ev} – {dep}: dónde ver el partido, canal y hora ({kisa})",
   desc="¿En qué canal echan el {ev} – {dep}? {comp}, {gun} {d} de {ay} a las {saat} (hora peninsular), en {kanal}. Canales en otros países y aviso antes del partido.",
   h1="¿Dónde ver el {ev} – {dep}?",
   once="El {ev} – {dep} ({comp}) se juega el {gun} {d} de {ay} a las {saat}, hora peninsular, y se puede ver en {kanal}.",
   sonra="El {ev} – {dep} ({comp}) se jugó el {gun} {d} de {ay} a las {saat}, hora peninsular, y se emitió en {kanal}.",
   diger="¿Dónde se ve en otros países?",
   comp_link="Todos los partidos de {comp} de hoy", spor_link="Todos los partidos de {spor} de hoy",
   takvim="Añadir al calendario",
   cta="No te pierdas el {ev} – {dep}",
   sub="La app te avisa 15 minutos antes del partido, con el canal que lo emite. Prueba 10 días gratis.",
   liste="Partidos de hoy y mañana en TV"),
 "fr": dict(ulke="FR", tz="Europe/Paris", klasor="match",
   gun=["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
   ay=["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
       "septembre", "octobre", "novembre", "décembre"],
   ve=" et ",
   title="{ev} – {dep} : sur quelle chaîne et à quelle heure ? ({kisa})",
   desc="Sur quelle chaîne voir {ev} – {dep} ? {comp}, le {gun} {d} {ay} à {saat} (heure de Paris), sur {kanal}. Diffuseurs dans les autres pays et alerte avant le match.",
   h1="{ev} – {dep} : sur quelle chaîne voir le match ?",
   once="Le match {ev} – {dep} ({comp}) a lieu le {gun} {d} {ay} à {saat}, heure de Paris, et sera diffusé sur {kanal}.",
   sonra="Le match {ev} – {dep} ({comp}) s'est joué le {gun} {d} {ay} à {saat}, heure de Paris, et a été diffusé sur {kanal}.",
   diger="Sur quelle chaîne dans les autres pays ?",
   comp_link="Tous les matchs de {comp} du jour", spor_link="Tous les matchs de {spor} du jour",
   takvim="Ajouter au calendrier",
   cta="Ne ratez pas {ev} – {dep}",
   sub="L'appli vous alerte 15 minutes avant le match, avec la chaîne qui le diffuse. 10 jours d'essai gratuit.",
   liste="Les matchs à la TV aujourd'hui et demain"),
}


def _esc(s):
    return prerender.esc(s)


# NFKD bu harfleri ayrıştırmaz, ascii'ye çevirirken düşerdi ("Preußen" -> "preuen").
_HARF = str.maketrans({"ß": "ss", "ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE",
                       "ı": "i", "İ": "I", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D", "þ": "th"})


def _slug(s):
    s = unicodedata.normalize("NFKD", s.translate(_HARF)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _ko(m):
    return datetime.datetime.fromisoformat(m["kickoffUtc"].replace("Z", "+00:00"))


def _ad(m, alan, yedek, lang):
    return prerender._ad(m, alan, yedek, lang)


def _birlestir(liste, ve):
    liste = list(liste)
    return liste[0] if len(liste) == 1 else ", ".join(liste[:-1]) + ve + liste[-1]


def arsivi_guncelle(simdi):
    try:
        arsiv = json.load(open(ARSIV, encoding="utf-8"))
    except Exception:
        arsiv = {}
    for m in prerender.fixtures().get("matches", []):
        if m.get("sport") not in SPORLAR or not m.get("id"):
            continue
        for lang, d in DIL.items():
            if not (m.get("broadcasts") or {}).get(d["ulke"]):
                continue
            key = lang + ":" + m["id"]
            eski = arsiv.get(key)
            if eski:
                eski["m"] = m          # kanal/saat düzeltmeleri sayfaya yansısın
            else:
                yerel = _ko(m).astimezone(ZoneInfo(d["tz"]))
                slug = "%s-%s-%s" % (_slug(_ad(m, "homeNames", m.get("home", ""), lang)),
                                     _slug(_ad(m, "awayNames", m.get("away", ""), lang)),
                                     yerel.strftime("%Y-%m-%d"))
                arsiv[key] = {"lang": lang, "slug": slug, "m": m}
    sinir = simdi - datetime.timedelta(days=SAKLA_GUN)
    for k in [k for k, v in arsiv.items() if _ko(v["m"]) < sinir]:
        del arsiv[k]
    # Aynı slug iki farklı maça düşerse (ör. aynı gün iki maç) ikinciye id ekle
    gorulen = {}
    for k in sorted(arsiv):
        v = arsiv[k]
        yol = v["lang"] + "/" + v["slug"]
        if yol in gorulen and gorulen[yol] != k:
            v["slug"] += "-" + _slug(v["m"]["id"])[-6:]
        gorulen[v["lang"] + "/" + v["slug"]] = k
    with open(ARSIV, "w", encoding="utf-8") as f:
        json.dump(arsiv, f, ensure_ascii=False, indent=0, sort_keys=True)
    return arsiv


def yol(lang, slug):
    return "/%s/%s/%s/" % (lang, DIL[lang]["klasor"], slug)


def _gcal(baslik, ko, detay):
    bas = ko.strftime("%Y%m%dT%H%M%SZ")
    son = (ko + datetime.timedelta(hours=2)).strftime("%Y%m%dT%H%M%SZ")
    from urllib.parse import quote
    return ("https://calendar.google.com/calendar/render?action=TEMPLATE&amp;text=%s&amp;dates=%s/%s&amp;details=%s"
            % (quote(baslik), bas, son, quote(detay)))


def sayfa(ctx, lang, v, alternatifler, simdi):
    d, m = DIL[lang], v["m"]
    tz = ZoneInfo(d["tz"])
    ko = _ko(m)
    yerel = ko.astimezone(tz)
    ev = _ad(m, "homeNames", m.get("home", ""), lang)
    dep = _ad(m, "awayNames", m.get("away", ""), lang)
    comp = _ad(m, "competition", m.get("competitionId", ""), lang)
    kanal_l = m["broadcasts"][d["ulke"]]
    alan = dict(ev=ev, dep=dep, comp=comp, kanal=_birlestir(kanal_l, d["ve"]),
                gun=d["gun"][yerel.weekday()], d=yerel.day, ay=d["ay"][yerel.month - 1],
                saat=yerel.strftime("%H:%M"), kisa=yerel.strftime("%d/%m"))
    bitti = simdi > ko + datetime.timedelta(minutes=BITTI_DK)
    giris = (d["sonra"] if bitti else d["once"]).format(**alan)
    canon = ctx["BASE"] + yol(lang, v["slug"])

    diger = []
    for u, kl in sorted(m["broadcasts"].items(), key=lambda x: ULKE_ADLARI[lang].get(x[0], x[0])):
        if u == d["ulke"] or not kl:
            continue
        diger.append("<li><b>%s</b>: %s</li>" % (_esc(ULKE_ADLARI[lang].get(u, u)), _esc(", ".join(kl))))
    diger_html = ('<section class="prose"><h2>%s</h2><ul class="ulkeler">%s</ul></section>'
                  % (d["diger"], "".join(diger))) if diger else ""

    linkler = []
    cid = m.get("competitionId")
    if cid in ctx["COMP_PAGES"].get(lang, {}):
        linkler.append('<a href="%s">%s</a>' % (ctx["comp_path"](lang, cid),
                       d["comp_link"].format(comp=_esc(ctx["comp_label"](lang, cid)))))
    sp = m.get("sport")
    linkler.append('<a href="%s">%s</a>' % (ctx["path_for"](lang, sp),
                   d["spor_link"].format(spor=ctx["SPORT_LABEL"][lang][sp].lower())))

    renk = prerender.SPORT_COLOR.get(sp, "#8892a6")
    kart = ('<article class="card"><div class="time"><div class="hm">%s</div><div class="day">%s</div></div>'
            '<div class="mid"><div class="teams"><span>%s</span><span class="vs">vs</span><span>%s</span></div>'
            '<div class="comp"><span class="sdot" style="background:%s"></span>%s</div></div>'
            '<div class="right"><span class="chan">%s</span></div></article>'
            % (yerel.strftime("%H:%M"), _esc(alan["kisa"]), _esc(ev), _esc(dep), renk, _esc(comp),
               _esc(" · ".join(kanal_l))))
    takvim = "" if bitti else ('<p><a href="%s" rel="nofollow">%s</a></p>' % (
        _gcal("%s – %s" % (ev, dep), ko, "%s · %s" % (comp, ", ".join(kanal_l))), d["takvim"]))

    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "SportsEvent", "name": "%s – %s" % (ev, dep), "description": giris,
         "startDate": m["kickoffUtc"], "url": canon,
         "eventStatus": "https://schema.org/EventScheduled",
         "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
         "location": {"@type": "VirtualLocation", "url": canon},
         "superEvent": {"@type": "SportsOrganization", "name": comp},
         "competitor": [{"@type": "SportsTeam", "name": ev}, {"@type": "SportsTeam", "name": dep}]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": ctx["BRAND"], "item": ctx["url_for"](lang)},
            {"@type": "ListItem", "position": 2, "name": ctx["SPORT_LABEL"][lang][sp], "item": ctx["url_for"](lang, sp)},
            {"@type": "ListItem", "position": 3, "name": "%s – %s" % (ev, dep), "item": canon}]}]}

    alts = "\n  ".join('<link rel="alternate" hreflang="%s" href="%s">' % (l, ctx["BASE"] + p)
                       for l, p in sorted(alternatifler.items())) if len(alternatifler) > 1 else ""
    hedef = {l: alternatifler.get(l, ctx["path_for"](l, sp)) for l in ctx["SEG"]}
    opts = "".join('<option value="%s" data-lang="%s"%s>%s</option>' % (
        hedef[l], l, " selected" if l == lang else "", ctx["LANG_NATIVE"][l]) for l in ctx["SEG"])
    langlinks = "\n      ".join('<a href="%s"%s>%s</a>' % (
        hedef[l], ' aria-current="true"' if l == lang else "", ctx["LANG_NATIVE"][l]) for l in ctx["SEG"])

    return """<!doctype html>
<html lang="{lang}" dir="ltr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{canon}">
  {alts}
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{brand}">
  <meta property="og:locale" content="{oglocale}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{canon}">
  <meta name="theme-color" content="#0b8f5a" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#0b0f17" media="(prefers-color-scheme: dark)">
  <link rel="icon" href="{favicon}">
  <link rel="stylesheet" href="/assets/styles.css?v={asset_ver}">
  <script type="application/ld+json">{ld}</script>
  {page_js}{analytics}
</head>
<body>
  <header class="site"><div class="wrap hrow">
    <a class="brand" href="{home}"><span class="logo">{logo_svg}</span><span class="name">{brand}</span></a>
    <span class="spacer"></span>
    <div class="selects">
      <select class="ctl" aria-label="Language" onchange="sotSetLang(this)">{opts}</select>
      <button class="iconbtn" id="themeBtn" aria-label="Theme">{theme_svg}</button>
    </div>
  </div></header>

  <main class="wrap">
    <h1 class="ptitle">{h1}</h1>
    <p class="daysum">{giris}</p>
    <div class="matchlist">{kart}</div>
    {takvim}
    <nav class="sportnav">{linkler}</nav>
    {diger}

    <section class="cta">
      <h2>{cta}</h2>
      <p class="sub">{sub}</p>
      <div class="badges">
        <a class="store" href="{apple}" rel="nofollow" aria-label="App Store">{apple_svg}<b>App&nbsp;Store</b></a>
        <a class="store" href="{google}" rel="nofollow" aria-label="Google Play">{google_svg}<b>Google&nbsp;Play</b></a>
      </div>
    </section>
  </main>

  <footer class="site"><div class="wrap">
    <div class="frow">
      <div class="langlinks">
      {langlinks}
      </div>
      <div>{footlinks} · © {brand}</div>
    </div>
  </div></footer>
</body>
</html>""".format(
        lang=lang, title=_esc(d["title"].format(**alan)), desc=_esc(d["desc"].format(**alan)),
        canon=canon, alts=alts, brand=ctx["BRAND"], oglocale=ctx["OG_LOCALE"][lang],
        favicon=ctx["FAVICON"], asset_ver=ctx["ASSET_VER"],
        ld=json.dumps(ld, ensure_ascii=False).replace("</", "<\\/"),
        page_js=ctx["PAGE_JS"], analytics=ctx["analytics_tag"](),
        home=ctx["path_for"](lang), logo_svg=ctx["LOGO_SVG"], opts=opts, theme_svg=ctx["THEME_SVG"],
        h1=_esc(d["h1"].format(**alan)), giris=_esc(giris), kart=kart, takvim=takvim,
        linkler="\n      ".join(linkler), diger=diger_html,
        cta=_esc(d["cta"].format(**alan)), sub=d["sub"],
        apple=ctx["APPLE"], google=ctx["play_link"](lang, "mac"),
        apple_svg=ctx["APPLE_SVG"], google_svg=ctx["GOOGLE_SVG"],
        langlinks=langlinks, footlinks=ctx["foot_links"](lang))


def yaz(OUT, ctx):
    """Sayfaları yazar, eskileri siler. Döner: (sitemap kayıtları, dil -> yaklaşan maç bağlantıları)."""
    simdi = datetime.datetime.now(datetime.timezone.utc)
    arsiv = arsivi_guncelle(simdi)

    # Aynı maçın es/fr sayfaları birbirine hreflang ile bağlanır
    mac_yollari = {}
    for v in arsiv.values():
        mac_yollari.setdefault(v["m"]["id"], {})[v["lang"]] = yol(v["lang"], v["slug"])

    sitemap, baglanti, yazilan = [], {l: [] for l in DIL}, set()
    for k, v in sorted(arsiv.items(), key=lambda x: x[1]["m"]["kickoffUtc"]):
        lang, m = v["lang"], v["m"]
        hedef = os.path.join(OUT, lang, DIL[lang]["klasor"], v["slug"])
        os.makedirs(hedef, exist_ok=True)
        with open(os.path.join(hedef, "index.html"), "w", encoding="utf-8") as f:
            f.write(sayfa(ctx, lang, v, mac_yollari[m["id"]], simdi))
        yazilan.add((lang, v["slug"]))
        sitemap.append((ctx["BASE"] + yol(lang, v["slug"]),
                        {l: ctx["BASE"] + p for l, p in mac_yollari[m["id"]].items()}))
        if simdi <= _ko(m) + datetime.timedelta(minutes=BITTI_DK):
            yerel = _ko(m).astimezone(ZoneInfo(DIL[lang]["tz"]))
            baglanti[lang].append(dict(
                comp=m.get("competitionId"), sport=m.get("sport"), path=yol(lang, v["slug"]),
                label="%s %s – %s" % (yerel.strftime("%d/%m %H:%M"),
                                      _ad(m, "homeNames", m.get("home", ""), lang),
                                      _ad(m, "awayNames", m.get("away", ""), lang))))

    # Arşivden düşen maçların klasörlerini sil (yayından da kalkar)
    for lang, d in DIL.items():
        kok = os.path.join(OUT, lang, d["klasor"])
        if not os.path.isdir(kok):
            continue
        for ad in os.listdir(kok):
            if (lang, ad) not in yazilan and os.path.isdir(os.path.join(kok, ad)):
                shutil.rmtree(os.path.join(kok, ad))
    return sitemap, baglanti


def baglanti_html(lang, baglanti, comp=None, sport=None):
    """Ana/futbol/turnuva sayfalarına yaklaşan maç sayfalarının listesi — tarayıcı bulsun."""
    if lang not in DIL:
        return ""
    l = [b for b in baglanti.get(lang, [])
         if (comp is None or b["comp"] == comp) and (sport is None or b["sport"] == sport)]
    if not l:
        return ""
    return ('<section class="prose matchlinks"><h2>%s</h2><ul>%s</ul></section>'
            % (DIL[lang]["liste"], "".join('<li><a href="%s">%s</a></li>' % (b["path"], _esc(b["label"])) for b in l)))
