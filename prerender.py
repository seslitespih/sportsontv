# -*- coding: utf-8 -*-
"""Maç listesini HTML'e GÖMER (build sırasında).

NEDEN: Site 11 KB HTML üretiyordu ve içinde tek bir takım adı yoktu — maçlar
app.js ile çalışma anında geliyordu. Googlebot boş bir tanıtım sayfası görüyor,
indekslenecek özgün içerik bulamıyordu. 25 Ağu 2026: Search Console 30 günde
0 gösterim.

ÇÖZÜM: build sırasında matches-daily.json okunur, o dilin varsayılan ülkesine
göre maç kartları HTML'e basılır + JSON-LD SportsEvent üretilir. app.js sayfa
yüklenince aynı div'i ziyaretçinin kendi ülkesine/saatine göre yeniden yazar,
yani görsel olarak hiçbir şey değişmez — sadece Google artık içerik görür.

Her dil sayfası farklı ülkenin kanallarını gösterdiği için içerik de gerçekten
farklılaşır (hreflang'in beklediği şey budur).
"""
import json, re, urllib.request, datetime
from zoneinfo import ZoneInfo

KAYNAK = "https://raw.githubusercontent.com/seslitespih/mac-hatirlatici/main/assets/matches-daily.json"

# Dil → o dilin varsayılan ülkesi (app.js'teki LANG_COUNTRY ile aynı)
LANG_COUNTRY = {"tr": "TR", "en": "GB", "de": "DE", "es": "ES",
                "fr": "FR", "it": "IT", "pt": "PT", "ar": "SA"}
COUNTRY_TZ = {"TR": "Europe/Istanbul", "GB": "Europe/London", "DE": "Europe/Berlin",
              "ES": "Europe/Madrid", "FR": "Europe/Paris", "IT": "Europe/Rome",
              "PT": "Europe/Lisbon", "SA": "Asia/Riyadh"}
SPORT_COLOR = {"football": "#12a15f", "basketball": "#e08a1e",
               "volleyball": "#2f6bd6", "motorsport": "#d23b4e"}
VS = {"tr": "-", "en": "vs", "de": "–", "es": "vs", "fr": "vs", "it": "vs", "pt": "vs", "ar": "-"}
YOK = {"tr": "Yayın bilgisi yok", "en": "No broadcast listed", "de": "Kein Sender gelistet",
       "es": "Sin emisión confirmada", "fr": "Aucune diffusion indiquée",
       "it": "Nessuna diretta indicata", "pt": "Sem transmissão indicada", "ar": "لا يوجد بث مؤكد"}

_cache = {}


def fixtures():
    """matches-daily.json'ı bir kez indir, bellekte tut."""
    if "data" not in _cache:
        try:
            with urllib.request.urlopen(KAYNAK, timeout=20) as r:
                _cache["data"] = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("  ! fikstur indirilemedi (%s) — mac listesi bos basilacak" % e)
            _cache["data"] = {"matches": []}
    return _cache["data"]


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _gun_penceresi(m, tz):
    """app.js ile aynı kural: bugün olanlar + bu gecenin 06:00 öncesi geç maçları."""
    d = datetime.datetime.fromisoformat(m["kickoffUtc"].replace("Z", "+00:00")).astimezone(tz)
    bugun = datetime.datetime.now(tz).date()
    if d.date() == bugun:
        return True
    return d.date() > bugun and d.hour < 6


def maclar(lang, sport=None):
    """Bu dil/spor sayfasında gösterilecek maçlar — app.js'in filtresiyle birebir."""
    ulke = LANG_COUNTRY.get(lang, "GB")
    tz = ZoneInfo(COUNTRY_TZ.get(ulke, "UTC"))
    out = []
    for m in fixtures().get("matches", []):
        kanal = (m.get("broadcasts") or {}).get(ulke) or []
        if not kanal and m.get("tier") != "global":
            continue
        if sport and m.get("sport") != sport:
            continue
        if not _gun_penceresi(m, tz):
            continue
        out.append(m)
    out.sort(key=lambda x: x["kickoffUtc"])
    return out, ulke, tz


def _ad(m, alan, yedek, lang):
    d = m.get(alan) or {}
    return d.get(lang) or d.get("en") or yedek


def kartlar(lang, sport=None):
    """app.js'teki matchCard ile AYNI markup — yüklenince fark edilmeden değişsin."""
    liste, ulke, tz = maclar(lang, sport)
    if not liste:
        return ""
    vs, yok = VS.get(lang, "vs"), YOK.get(lang, YOK["en"])
    parca = []
    for m in liste:
        d = datetime.datetime.fromisoformat(m["kickoffUtc"].replace("Z", "+00:00")).astimezone(tz)
        comp = esc(_ad(m, "competition", m.get("competitionId", ""), lang))
        ev = esc(_ad(m, "homeNames", m.get("home", ""), lang))
        dep = esc(_ad(m, "awayNames", m.get("away", ""), lang))
        kanal = (m.get("broadcasts") or {}).get(ulke) or []
        renk = SPORT_COLOR.get(m.get("sport"), "#8892a6")
        kan = ('<span class="chan">' + esc(" · ".join(kanal)) + "</span>") if kanal \
            else ('<span class="chan none">' + esc(yok) + "</span>")
        parca.append(
            '<article class="card">'
            '<div class="time"><div class="hm">%s</div><div class="day">%s</div></div>'
            '<div class="mid"><div class="teams"><span>%s</span>'
            '<span class="vs">%s</span><span>%s</span></div>'
            '<div class="comp"><span class="sdot" style="background:%s"></span>%s</div></div>'
            '<div class="right">%s</div></article>'
            % (d.strftime("%H:%M"), d.strftime("%a"), ev, esc(vs), dep, renk, comp, kan))
    return "".join(parca)


def sports_ld(lang, sport=None):
    """JSON-LD SportsEvent — Google'ın maç zengin sonucu için."""
    liste, ulke, _ = maclar(lang, sport)
    if not liste:
        return ""
    olay = []
    for m in liste[:30]:
        ev = _ad(m, "homeNames", m.get("home", ""), lang)
        dep = _ad(m, "awayNames", m.get("away", ""), lang)
        comp = _ad(m, "competition", m.get("competitionId", ""), lang)
        kanal = (m.get("broadcasts") or {}).get(ulke) or []
        o = {
            "@type": "SportsEvent",
            "name": "%s %s %s" % (ev, VS.get(lang, "vs"), dep),
            "startDate": m["kickoffUtc"],
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
            "location": {"@type": "VirtualLocation", "url": "https://sportstvtoday.com/"},
            "superEvent": {"@type": "SportsOrganization", "name": comp},
            "competitor": [{"@type": "SportsTeam", "name": ev},
                           {"@type": "SportsTeam", "name": dep}],
        }
        if kanal:
            o["broadcastOfEvent"] = {"@type": "BroadcastEvent",
                                     "name": ", ".join(kanal),
                                     "isLiveBroadcast": True}
        olay.append(o)
    return json.dumps({"@context": "https://schema.org", "@graph": olay}, ensure_ascii=False)


def ozet(lang, sport=None):
    """Sayfanın başına giren tek cümlelik özet — özgün metin, her gün değişir."""
    liste, ulke, tz = maclar(lang, sport)
    if not liste:
        return ""
    n = len(liste)
    kanalli = len([m for m in liste if (m.get("broadcasts") or {}).get(ulke)])
    ilk = datetime.datetime.fromisoformat(liste[0]["kickoffUtc"].replace("Z", "+00:00")).astimezone(tz)
    son = datetime.datetime.fromisoformat(liste[-1]["kickoffUtc"].replace("Z", "+00:00")).astimezone(tz)
    kalip = {
        "tr": "Bugün %d karşılaşma var, %d tanesinin yayın kanalı belli. İlk maç %s, son maç %s.",
        "en": "%d matches today, %d with a confirmed channel. First kick-off %s, last %s.",
        "de": "Heute %d Spiele, davon %d mit bestätigtem Sender. Erster Anstoß %s, letzter %s.",
        "es": "Hoy hay %d partidos, %d con canal confirmado. El primero a las %s, el último a las %s.",
        "fr": "%d matchs aujourd'hui, %d avec une chaîne confirmée. Premier coup d'envoi %s, dernier %s.",
        "it": "Oggi %d partite, %d con canale confermato. Primo fischio %s, ultimo %s.",
        "pt": "Hoje há %d jogos, %d com canal confirmado. Primeiro às %s, último às %s.",
        "ar": "اليوم %d مباراة، %d منها بقناة مؤكدة. الأولى %s والأخيرة %s.",
    }
    return kalip.get(lang, kalip["en"]) % (n, kanalli, ilk.strftime("%H:%M"), son.strftime("%H:%M"))
