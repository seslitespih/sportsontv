# -*- coding: utf-8 -*-
"""Generate the multilingual Sports-on-TV site: one static, SEO-tuned page per
language (localized <title>/description/H1/FAQ + hreflang alternates + JSON-LD),
plus sitemap.xml and robots.txt. The live match list is filled client-side by
assets/app.js from the same daily fixtures the mobile app uses."""
import os, io, sys, json, urllib.parse

# ─── Varlik surumu ───────────────────────────────────────────────────────────
# app.js GitHub Pages'te 10 dakika onbellekleniyor; tarayicilar daha uzun tutabiliyor.
# Icerige gore hash ekleyince dosya degistigi anda URL de degisir ve eski surum
# takilip kalmaz. Degismediginde hash ayni kalir, gereksiz indirme olmaz.
import hashlib as _hashlib
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "app.js"), "rb") as _f:
        ASSET_VER = _hashlib.sha1(_f.read()).hexdigest()[:8]
except OSError:
    ASSET_VER = "0"

import prerender   # mac listesini HTML e gomer (SEO)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ⚠️ GEÇİCİ: normalde https olmalı. GitHub Pages sertifikası 11 Ağu'dan beri
# "new" durumunda takılı (DNS doğru, CAA engeli yok, alan adı iki kez kaldırılıp
# eklendi) ve https hiç çalışmıyor. Canonical/sitemap https gösterdiği sürece
# Google hiçbir sayfayı çekemiyordu — site "hiç taranmamış" durumdaydı.
#
# 18 Eyl 2026: Cloudflare Pages'e taşınıyoruz (GitHub'ın sertifika kuyruğu 38
# gündür kımıldamıyor). HTTPS çalışır çalışmaz tek yapılacak şey aşağıdaki
# SEMA'yı "https" yapmak — ya da geçici denemek için ortamdan geçmek:
#     SITE_SEMA=https python build_site.py
# Sonra: derle, push'la, sitemap'i Search Console'a yeniden gönder.
SEMA = os.environ.get("SITE_SEMA", "https")   # 18 Eyl 2026: Cloudflare Pages, sertifika aktif
BASE = SEMA + "://sportstvtoday.com"
OUT  = r"C:/Users/ESAT/Desktop/sportsontv-site"
APPLE = "https://apps.apple.com/app/id6779112504"
GOOGLE = "https://play.google.com/store/apps/details?id=com.machatirlatici.app"
BRAND = "Sports on TV"

# Google Analytics 4 ölçüm kimliği. Boşken hiçbir script basılmaz — siteye
# analitik eklemek için buraya G-XXXXXXXXXX yaz, yeter. Etiket <head>'e her
# dil sayfasında otomatik girer; tek tek HTML'leri elle düzenleme (üretilen
# dosyalar her derlemede sıfırdan yazılır).
GA_ID = "G-N8YY5V2WSS"


def analytics_tag():
    if not GA_ID:
        return ""
    return (
        '\n  <script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>\n'
        '  <script>window.dataLayer=window.dataLayer||[];'
        'function gtag(){dataLayer.push(arguments);}'
        "gtag('js',new Date());gtag('config','%s');</script>" % (GA_ID, GA_ID)
    )


APPLE_SVG = ('<svg class="glyph" viewBox="0 0 384 512" width="20" height="24" fill="currentColor" aria-hidden="true">'
  '<path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 '
  '20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 '
  '125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 '
  '24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></svg>')
GOOGLE_SVG = ('<svg class="glyph" viewBox="0 0 24 24" width="21" height="23" aria-hidden="true">'
  '<path fill="#00d3ff" d="M3.6 2.2C3.3 2.5 3.1 3 3.1 3.7v16.6c0 .7.2 1.2.5 1.5l.1.1 9.3-9.3v-.2L3.6 2.2z"/>'
  '<path fill="#00f076" d="M16.5 15.1l-3.5-3.5v-.2l3.5-3.5.1.1 4.1 2.4c1.2.7 1.2 1.8 0 2.5l-4.2 2.2z"/>'
  '<path fill="#ff3a44" d="M16.6 15L13 11.5 3.6 21c.4.4 1 .5 1.8.1L16.6 15z"/>'
  '<path fill="#ffce00" d="M16.6 8L5.4 1.9c-.8-.5-1.4-.4-1.8 0L13 11.5 16.6 8z"/></svg>')

# minimal line icons (stroke = currentColor), no emoji
def _svg(body): return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
                        'stroke-linecap="round" stroke-linejoin="round">' + body + '</svg>')
IC_TV     = _svg('<rect x="2.5" y="7" width="19" height="13" rx="2.2"/><path d="M8 3.5l4 3.5 4-3.5"/>')
IC_CLOCK  = _svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3.2 1.9"/>')
IC_TROPHY = _svg('<path d="M7 4h10v5a5 5 0 0 1-10 0V4z"/><path d="M7 6H4.5a2.5 2.5 0 0 0 2.7 2.9M17 6h2.5a2.5 2.5 0 0 1-2.7 2.9"/><path d="M12 14v3M9 20h6M9.7 20l.6-3M14.3 20l-.6-3"/>')
IC_BELL   = _svg('<path d="M6 9.5a6 6 0 0 1 12 0c0 4.5 1.8 5.5 2 6H4c.2-.5 2-1.5 2-6z"/><path d="M10.2 20a2 2 0 0 0 3.6 0"/>')
FEAT_ICONS = [IC_TV, IC_CLOCK, IC_TROPHY, IC_BELL]
LOGO_SVG  = _svg('<rect x="2.5" y="7" width="19" height="13" rx="2.2"/><path d="M8 3.5l4 3.5 4-3.5"/>')
THEME_SVG = _svg('<path d="M20 14.5A8 8 0 1 1 9.5 4 6.3 6.3 0 0 0 20 14.5z"/>')
FAVICON = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
  "<rect width='100' height='100' rx='24' fill='%230b8f5a'/><g fill='none' stroke='white' "
  "stroke-width='7' stroke-linecap='round' stroke-linejoin='round'><rect x='26' y='42' width='48' "
  "height='34' rx='6'/><path d='M38 28l12 12 12-12'/></g></svg>")

# lang -> path segment ('' = root / English / x-default)
SEG = {"en":"", "tr":"tr", "de":"de", "es":"es", "fr":"fr", "it":"it", "pt":"pt", "ar":"ar"}
OG_LOCALE = {"en":"en_US","tr":"tr_TR","de":"de_DE","es":"es_ES","fr":"fr_FR","it":"it_IT","pt":"pt_BR","ar":"ar_SA"}
LANG_NATIVE = {"en":"English","tr":"Türkçe","de":"Deutsch","es":"Español","fr":"Français","it":"Italiano","pt":"Português","ar":"العربية"}
CTA = {"en":"Get the free app","tr":"Ücretsiz uygulamayı indir","de":"Hol dir die kostenlose App",
       "es":"Descarga la app gratis","fr":"Téléchargez l'appli gratuite","it":"Scarica l'app gratuita",
       "pt":"Baixe o app grátis","ar":"حمّل التطبيق المجاني"}

# ── spor sayfaları ──────────────────────────────────────────────────────────
# Ana sayfa "bugün maçlar hangi kanalda" gibi genel aramayı hedefliyor. Asıl
# arama hacmi spor bazlı sorularda ("bugün hangi futbol maçları var", "fussball
# heute im tv"). Her dil × spor için ayrı sayfa üretilir; sayfa aynı canlı maç
# listesini o spora filtrelenmiş hâlde gösterir (app.js window.__SPORT__ okur).
SPORTS = ["football", "basketball", "volleyball", "motorsport"]

# URL parçaları ASCII — Arapça'da da latin slug kullanıyoruz, okunabilir kalsın.
SPORT_SLUG = {
 "en": {"football":"football","basketball":"basketball","volleyball":"volleyball","motorsport":"motorsport"},
 "tr": {"football":"futbol","basketball":"basketbol","volleyball":"voleybol","motorsport":"motor-sporlari"},
 "de": {"football":"fussball","basketball":"basketball","volleyball":"volleyball","motorsport":"motorsport"},
 "es": {"football":"futbol","basketball":"baloncesto","volleyball":"voleibol","motorsport":"motor"},
 "fr": {"football":"football","basketball":"basket","volleyball":"volley","motorsport":"sport-auto"},
 "it": {"football":"calcio","basketball":"basket","volleyball":"pallavolo","motorsport":"motori"},
 "pt": {"football":"futebol","basketball":"basquete","volleyball":"volei","motorsport":"automobilismo"},
 "ar": {"football":"football","basketball":"basketball","volleyball":"volleyball","motorsport":"motorsport"},
}
SPORT_LABEL = {
 "en": {"football":"Football","basketball":"Basketball","volleyball":"Volleyball","motorsport":"Motorsport"},
 "tr": {"football":"Futbol","basketball":"Basketbol","volleyball":"Voleybol","motorsport":"Motor Sporları"},
 "de": {"football":"Fußball","basketball":"Basketball","volleyball":"Volleyball","motorsport":"Motorsport"},
 "es": {"football":"Fútbol","basketball":"Baloncesto","volleyball":"Voleibol","motorsport":"Motor"},
 "fr": {"football":"Football","basketball":"Basket","volleyball":"Volley","motorsport":"Sport auto"},
 "it": {"football":"Calcio","basketball":"Basket","volleyball":"Pallavolo","motorsport":"Motori"},
 "pt": {"football":"Futebol","basketball":"Basquete","volleyball":"Vôlei","motorsport":"Automobilismo"},
 "ar": {"football":"كرة القدم","basketball":"كرة السلة","volleyball":"الكرة الطائرة","motorsport":"رياضة السيارات"},
}
# Başlıklar çeviri değil, o dilde gerçekten aranan ifadeye göre yazıldı.
SPORT_COPY = {
 "en": {
  "football":   ("Football on TV Today — Channel & Kick-off Time", "Every football match on TV today with the channel showing it in your country and the kick-off time in your time zone.", "What channel is the football on today?", "Today's football fixtures with the broadcaster for your country and kick-off in your local time — Champions League, domestic leagues and internationals in one list."),
  "basketball": ("Basketball on TV Today — Channel & Tip-off Time", "Today's basketball games on TV: which channel is showing each game where you live and what time it tips off.", "What channel is the basketball on today?", "Every basketball game on TV today, from EuroLeague and NBA to domestic leagues, with your local tip-off time and the channel carrying it."),
  "volleyball": ("Volleyball on TV Today — Channel & Start Time", "Today's volleyball matches on TV with the channel for your country and the start time in your own time zone.", "What channel is the volleyball on today?", "Today's volleyball on television, national leagues and international competitions, each with its broadcaster and your local start time."),
  "motorsport": ("Motorsport on TV Today — Channel & Race Time", "Today's races on TV: the channel showing each session in your country and the start time where you are.", "What channel is the race on today?", "Practice, qualifying and race sessions on TV today, with the broadcaster for your country and start times converted to your time zone."),
 },
 "tr": {
  "football":   ("Bugün Hangi Futbol Maçları Var? Kanal ve Saat", "Bugünkü futbol maçları hangi kanalda, saat kaçta? Türkiye yayıncısı ve kendi saatinle başlama zamanı — her gün güncel.", "Futbol maçı bugün hangi kanalda?", "Bugünün futbol programı: Şampiyonlar Ligi'nden Süper Lig'e her maçın yayıncı kanalı ve kendi saat dilimindeki başlama saati tek listede."),
  "basketball": ("Bugün Hangi Basketbol Maçları Var? Kanal ve Saat", "Bugünkü basketbol maçları hangi kanalda yayınlanıyor, saat kaçta başlıyor? EuroLeague, NBA ve yerel ligler.", "Basketbol maçı bugün hangi kanalda?", "EuroLeague, NBA ve Türkiye ligindeki bugünkü basketbol maçları; her biri için yayıncı kanal ve senin saatinle tip-off zamanı."),
  "volleyball": ("Bugün Hangi Voleybol Maçları Var? Kanal ve Saat", "Bugünkü voleybol maçlarının yayın kanalı ve başlama saati. Sultanlar Ligi, Efeler Ligi ve uluslararası turnuvalar.", "Voleybol maçı bugün hangi kanalda?", "Sultanlar Ligi, Efeler Ligi ve milli takım maçları dahil bugünün voleybol yayın programı, kanal ve saat bilgisiyle."),
  "motorsport": ("Bugün Yarış Var mı? Kanal ve Saat", "Bugünkü Formula 1 ve motor sporları seansları hangi kanalda, saat kaçta? Antrenman, sıralama ve yarış saatleri.", "Yarış bugün hangi kanalda?", "Formula 1 ve diğer motor sporlarında bugünkü antrenman, sıralama ve yarış seansları; yayıncı kanal ve kendi saatinle başlama zamanı."),
 },
 "de": {
  "football":   ("Fußball heute im TV — Sender & Anstoßzeit", "Welcher Sender überträgt heute welches Fußballspiel? Alle Partien mit Anstoßzeit in deiner Zeitzone.", "Welcher Sender zeigt heute Fußball?", "Alle Fußballspiele von heute mit dem übertragenden Sender in deinem Land und der Anstoßzeit in deiner Zeitzone — Champions League, Bundesliga und Länderspiele."),
  "basketball": ("Basketball heute im TV — Sender & Uhrzeit", "Basketball heute live im Fernsehen: welcher Sender überträgt und wann das Spiel beginnt.", "Welcher Sender zeigt heute Basketball?", "EuroLeague, NBA und Bundesliga — die heutigen Basketballspiele mit Sender und Anwurfzeit in deiner Zeitzone."),
  "volleyball": ("Volleyball heute im TV — Sender & Uhrzeit", "Die heutigen Volleyballspiele im Fernsehen mit Sender und Startzeit in deiner Zeitzone.", "Welcher Sender zeigt heute Volleyball?", "Nationale Ligen und internationale Turniere: das heutige Volleyball-Fernsehprogramm mit Sender und lokaler Startzeit."),
  "motorsport": ("Motorsport heute im TV — Sender & Startzeit", "Training, Qualifying und Rennen heute live: welcher Sender überträgt und wann es losgeht.", "Welcher Sender zeigt heute das Rennen?", "Die heutigen Motorsport-Sessions im Fernsehen — Training, Qualifying und Rennen mit Sender und Startzeit in deiner Zeitzone."),
 },
 "es": {
  "football":   ("Fútbol Hoy en TV — Canal y Hora", "¿En qué canal es el partido de hoy y a qué hora empieza? Todos los partidos de fútbol con su emisora y tu hora local.", "¿En qué canal es el fútbol hoy?", "Los partidos de fútbol de hoy con el canal que los emite en tu país y la hora de inicio en tu zona horaria — Champions, LaLiga y selecciones."),
  "basketball": ("Baloncesto Hoy en TV — Canal y Hora", "Los partidos de baloncesto de hoy en televisión: qué canal los emite y a qué hora empiezan.", "¿En qué canal es el baloncesto hoy?", "Euroliga, NBA y ligas nacionales: el baloncesto de hoy en televisión con su canal y la hora de inicio donde vives."),
  "volleyball": ("Voleibol Hoy en TV — Canal y Hora", "Los partidos de voleibol de hoy con el canal de tu país y la hora de inicio en tu zona horaria.", "¿En qué canal es el voleibol hoy?", "Ligas nacionales y competiciones internacionales: la programación de voleibol de hoy con canal y hora local."),
  "motorsport": ("Motor Hoy en TV — Canal y Hora", "Entrenamientos, clasificación y carrera de hoy: en qué canal se ven y a qué hora empiezan.", "¿En qué canal es la carrera hoy?", "Las sesiones de motor de hoy en televisión — libres, clasificación y carrera — con su canal y la hora en tu zona horaria."),
 },
 "fr": {
  "football":   ("Football à la TV Aujourd'hui — Chaîne et Heure", "Quelle chaîne diffuse quel match aujourd'hui et à quelle heure ? Tous les matchs avec l'heure dans votre fuseau.", "Sur quelle chaîne est le match de foot aujourd'hui ?", "Les matchs de football du jour avec la chaîne qui les diffuse dans votre pays et l'heure du coup d'envoi dans votre fuseau horaire."),
  "basketball": ("Basket à la TV Aujourd'hui — Chaîne et Heure", "Les matchs de basket du jour à la télévision : quelle chaîne les diffuse et à quelle heure.", "Sur quelle chaîne est le basket aujourd'hui ?", "EuroLigue, NBA et championnats nationaux : le basket du jour à la télé, avec la chaîne et l'heure chez vous."),
  "volleyball": ("Volley à la TV Aujourd'hui — Chaîne et Heure", "Les matchs de volley du jour avec la chaîne de votre pays et l'heure de début dans votre fuseau.", "Sur quelle chaîne est le volley aujourd'hui ?", "Championnats nationaux et compétitions internationales : le programme volley du jour, chaîne et heure locale."),
  "motorsport": ("Sport Auto à la TV Aujourd'hui — Chaîne et Heure", "Essais, qualifications et course du jour : sur quelle chaîne et à quelle heure.", "Sur quelle chaîne est la course aujourd'hui ?", "Les séances de sport auto du jour à la télévision — essais, qualifications, course — avec la chaîne et l'heure dans votre fuseau."),
 },
 "it": {
  "football":   ("Calcio in TV Oggi — Canale e Orario", "Su che canale è la partita di oggi e a che ora inizia? Tutte le partite con l'orario nel tuo fuso.", "Su che canale è il calcio oggi?", "Le partite di calcio di oggi con il canale che le trasmette nel tuo paese e l'orario del fischio d'inizio nel tuo fuso orario."),
  "basketball": ("Basket in TV Oggi — Canale e Orario", "Le partite di basket di oggi in televisione: quale canale le trasmette e a che ora iniziano.", "Su che canale è il basket oggi?", "EuroLega, NBA e campionati nazionali: il basket di oggi in TV con canale e orario di inizio dove vivi."),
  "volleyball": ("Pallavolo in TV Oggi — Canale e Orario", "Le partite di pallavolo di oggi con il canale del tuo paese e l'orario di inizio nel tuo fuso.", "Su che canale è la pallavolo oggi?", "Campionati nazionali e competizioni internazionali: il programma pallavolo di oggi, con canale e orario locale."),
  "motorsport": ("Motori in TV Oggi — Canale e Orario", "Prove, qualifiche e gara di oggi: su quale canale e a che ora.", "Su che canale è la gara oggi?", "Le sessioni di motori di oggi in televisione — prove, qualifiche e gara — con il canale e l'orario nel tuo fuso."),
 },
 "pt": {
  "football":   ("Futebol na TV Hoje — Canal e Horário", "Qual canal transmite o jogo de hoje e a que horas começa? Todos os jogos com o horário no seu fuso.", "Que canal passa o futebol hoje?", "Os jogos de futebol de hoje com o canal que transmite no seu país e o horário de início no seu fuso horário — Libertadores, Brasileirão e seleções."),
  "basketball": ("Basquete na TV Hoje — Canal e Horário", "Os jogos de basquete de hoje na TV: qual canal transmite e a que horas começam.", "Que canal passa o basquete hoje?", "NBA, EuroLeague e ligas nacionais: o basquete de hoje na televisão com canal e horário de início onde você está."),
  "volleyball": ("Vôlei na TV Hoje — Canal e Horário", "Os jogos de vôlei de hoje com o canal do seu país e o horário de início no seu fuso.", "Que canal passa o vôlei hoje?", "Superliga e competições internacionais: a programação de vôlei de hoje, com canal e horário local."),
  "motorsport": ("Automobilismo na TV Hoje — Canal e Horário", "Treinos, classificação e corrida de hoje: em qual canal e a que horas.", "Que canal passa a corrida hoje?", "As sessões de automobilismo de hoje na TV — treinos, classificação e corrida — com o canal e o horário no seu fuso."),
 },
 "ar": {
  "football":   ("مباريات كرة القدم اليوم — القناة والتوقيت", "ما هي القناة الناقلة لمباريات اليوم وموعد انطلاقها بتوقيت بلدك؟ جدول يومي محدّث.", "ما القناة الناقلة لمباراة اليوم؟", "مباريات كرة القدم اليوم مع القناة الناقلة في بلدك وموعد البداية بتوقيتك المحلي — دوري أبطال أوروبا والدوريات المحلية والمباريات الدولية."),
  "basketball": ("مباريات كرة السلة اليوم — القناة والتوقيت", "مباريات كرة السلة اليوم على التلفزيون: القناة الناقلة وموعد البداية بتوقيتك.", "ما القناة الناقلة لمباراة كرة السلة اليوم؟", "الدوري الأوروبي والدوري الأمريكي والدوريات المحلية: مباريات كرة السلة اليوم مع القناة الناقلة وموعد البداية بتوقيتك."),
  "volleyball": ("مباريات الكرة الطائرة اليوم — القناة والتوقيت", "مباريات الكرة الطائرة اليوم مع القناة الناقلة في بلدك وموعد البداية بتوقيتك.", "ما القناة الناقلة لمباراة الكرة الطائرة اليوم؟", "الدوريات المحلية والبطولات الدولية: جدول الكرة الطائرة اليوم مع القناة الناقلة والتوقيت المحلي."),
  "motorsport": ("سباقات اليوم على التلفزيون — القناة والتوقيت", "التجارب والتصفيات والسباق اليوم: القناة الناقلة وموعد الانطلاق بتوقيتك.", "ما القناة الناقلة للسباق اليوم؟", "جلسات رياضة السيارات اليوم — التجارب والتصفيات والسباق — مع القناة الناقلة وموعد الانطلاق بتوقيتك المحلي."),
 },
}

# ── turnuva sayfaları (Eki 2026) ─────────────────────────────────────────────
# Genel "bugün maçlar" aramasında Marca/AS/L'Équipe ile yarışamıyoruz (Search
# Console: ES/FR'de sıra 35-80). Turnuva bazlı "LaLiga hangi kanalda" soruları
# daha dar ve kalıcı. Sayfa o turnuvanın bugünkü maçlarını + sezonun yayıncı
# bilgisini verir. Yayıncılar maç-hatırlatıcı/scripts/broadcast-rights.json'daki
# "dogrulandi" kayıtlarla aynı ve 9 Eki 2026'da web aramasıyla yeniden teyit
# edildi (Ligue 1+ tek yayıncı; ES LaLiga Movistar 5 + DAZN 5; FR LaLiga
# DAZN + Disney+). Sezon değişince metinler de güncellenmeli.
# Anahtar = matches-daily.json'daki competitionId.
COMP_PAGES = {
 "es": {
  "laliga": dict(slug="laliga", name="LaLiga",
    title="Dónde ver LaLiga hoy: canal y horario de cada partido",
    desc="Partidos de LaLiga EA Sports de hoy con su hora y el canal que los emite en España: Movistar Plus+ o DAZN. Se actualiza cada día.",
    h1="¿Dónde ver LaLiga hoy?",
    rightsT="¿Qué canal emite LaLiga en la temporada 2026-27?",
    rights="En España, LaLiga EA Sports se reparte entre Movistar Plus+ y DAZN. Movistar Plus+ tiene cinco partidos de cada jornada y tres jornadas completas en exclusiva; DAZN emite los otros cinco partidos en 35 de las 38 jornadas. El canal DAZN LaLiga también está disponible en Movistar Plus+, en el dial 55. En la lista de arriba ves los partidos de hoy con el canal exacto de cada uno.",
    faqs=[("¿Se pueden ver todos los partidos de LaLiga con DAZN?", "No. DAZN tiene cinco de los diez partidos de cada jornada y no emite tres jornadas completas, que son exclusivas de Movistar Plus+."),
          ("¿A qué hora son los partidos de LaLiga hoy?", "La lista de esta página muestra la hora de inicio de cada partido de hoy en hora peninsular. Si estás en otro país, cámbialo arriba y verás tu hora y tus canales."),
          ("¿Cómo sé en qué canal echan el partido de mi equipo?", "Mira la lista de esta página el día del partido, o usa la app de Sports on TV: te avisa 15 minutos antes del inicio con el canal que lo emite.")],
    cta_sub="Un aviso 15 minutos antes de cada partido de LaLiga, con el canal que lo emite. Prueba 10 días gratis."),
  "champions": dict(slug="champions-league", name="la Champions League",
    title="Dónde ver la Champions League hoy: canal y horario",
    desc="Partidos de la Champions League de hoy con su hora en España y el canal: en la temporada 2026-27 la Champions se ve en Movistar Plus+.",
    h1="¿Dónde ver la Champions hoy?",
    rightsT="¿Qué canal emite la Champions League en 2026-27?",
    rights="En España, Movistar Plus+ tiene los derechos de la UEFA Champions League en la temporada 2026-27 y emite los partidos desde la fase liga hasta la final. Los días de Champions, la lista de arriba muestra cada partido con su hora y su canal.",
    faqs=[("¿Qué días se juega la Champions League?", "Normalmente los martes y miércoles por la noche. Cuando hay partidos, aparecen aquí ese mismo día con su hora y su canal."),
          ("¿A qué hora empiezan los partidos de Champions?", "Los horarios habituales son las 18:45 y las 21:00, hora peninsular. La hora exacta de cada partido de hoy está en la lista.")],
    cta_sub="Un aviso 15 minutos antes de cada partido de Champions, con el canal. Prueba 10 días gratis."),
  "europa": dict(slug="europa-league", name="la Europa League",
    title="Dónde ver la Europa League hoy: canal y horario",
    desc="Partidos de la UEFA Europa League de hoy con su hora en España y el canal que los emite: Movistar Plus+ en la temporada 2026-27.",
    h1="¿Dónde ver la Europa League hoy?",
    rightsT="¿Qué canal emite la Europa League en 2026-27?",
    rights="En España, la UEFA Europa League se ve en Movistar Plus+ en la temporada 2026-27. Los partidos se juegan los jueves; ese día la lista de arriba muestra cada encuentro con su hora y su canal.",
    faqs=[("¿Qué día se juega la Europa League?", "Los jueves, normalmente a las 18:45 y a las 21:00, hora peninsular."),
          ("¿Dónde veo a los equipos españoles en la Europa League?", "En Movistar Plus+. La lista de esta página indica el canal exacto de cada partido el mismo día.")],
    cta_sub="Un aviso 15 minutos antes de cada partido de Europa League, con el canal. Prueba 10 días gratis."),
 },
 "fr": {
  "ligue1": dict(slug="ligue-1", name="Ligue 1",
    title="Ligue 1 : sur quelle chaîne voir les matchs aujourd'hui ?",
    desc="Les matchs de Ligue 1 du jour avec l'heure et la chaîne : en 2026-27, Ligue 1+ diffuse les neuf matchs de chaque journée. Mis à jour chaque jour.",
    h1="Sur quelle chaîne voir la Ligue 1 aujourd'hui ?",
    rightsT="Qui diffuse la Ligue 1 en 2026-27 ?",
    rights="Depuis la saison 2026-27, Ligue 1+ est le seul diffuseur de la Ligue 1 : les neuf matchs de chaque journée sont en direct sur la plateforme de la LFP, y compris le match du samedi 17 h qui était auparavant sur beIN SPORTS. Ligue 1+ est aussi distribuée par DAZN. La liste ci-dessus affiche les matchs du jour avec leur heure.",
    faqs=[("Peut-on voir la Ligue 1 sur beIN SPORTS en 2026-27 ?", "Non. À partir de 2026-27, beIN SPORTS ne diffuse plus de match de Ligue 1 : les neuf rencontres de chaque journée sont sur Ligue 1+."),
          ("À quelle heure sont les matchs de Ligue 1 aujourd'hui ?", "La liste de cette page indique l'heure du coup d'envoi de chaque match du jour, à l'heure de Paris. Hors de France, changez de pays en haut de la page pour voir votre heure et vos chaînes.")],
    cta_sub="Une alerte 15 minutes avant chaque match de Ligue 1, avec la chaîne. 10 jours d'essai gratuit."),
  "champions": dict(slug="ligue-des-champions", name="Ligue des champions",
    title="Ligue des champions : sur quelle chaîne voir les matchs aujourd'hui ?",
    desc="Les matchs de Ligue des champions du jour avec l'heure et la chaîne en France : CANAL+ diffuse la compétition en 2026-27.",
    h1="Sur quelle chaîne voir la Ligue des champions aujourd'hui ?",
    rightsT="Qui diffuse la Ligue des champions en 2026-27 ?",
    rights="En France, CANAL+ détient les droits de la Ligue des champions pour la saison 2026-27 et diffuse les matchs de la phase de ligue jusqu'à la finale. Les soirs de Ligue des champions, la liste ci-dessus indique chaque match avec son heure et sa chaîne.",
    faqs=[("Quels jours se joue la Ligue des champions ?", "En général le mardi et le mercredi soir. Les jours de match, les rencontres apparaissent ici avec l'heure et la chaîne."),
          ("À quelle heure commencent les matchs ?", "Les horaires habituels sont 18 h 45 et 21 h, heure de Paris. L'heure exacte de chaque match du jour est dans la liste.")],
    cta_sub="Une alerte 15 minutes avant chaque match de Ligue des champions, avec la chaîne. 10 jours d'essai gratuit."),
  "europa": dict(slug="ligue-europa", name="Ligue Europa",
    title="Ligue Europa : sur quelle chaîne voir les matchs aujourd'hui ?",
    desc="Les matchs de Ligue Europa du jour avec l'heure et la chaîne en France : CANAL+ en 2026-27.",
    h1="Sur quelle chaîne voir la Ligue Europa aujourd'hui ?",
    rightsT="Qui diffuse la Ligue Europa en 2026-27 ?",
    rights="En France, la Ligue Europa est diffusée par CANAL+ en 2026-27. Les matchs ont lieu le jeudi ; ce jour-là, la liste ci-dessus montre chaque rencontre avec son heure et sa chaîne.",
    faqs=[("Quel jour se joue la Ligue Europa ?", "Le jeudi, avec des coups d'envoi habituels à 18 h 45 et 21 h, heure de Paris.")],
    cta_sub="Une alerte 15 minutes avant chaque match de Ligue Europa, avec la chaîne. 10 jours d'essai gratuit."),
  "conference": dict(slug="ligue-conference", name="Ligue Conférence",
    title="Ligue Conférence : sur quelle chaîne voir les matchs aujourd'hui ?",
    desc="Les matchs de Ligue Conférence du jour avec l'heure et la chaîne en France : CANAL+ en 2026-27.",
    h1="Sur quelle chaîne voir la Ligue Conférence aujourd'hui ?",
    rightsT="Qui diffuse la Ligue Conférence en 2026-27 ?",
    rights="En France, la Ligue Conférence est diffusée par CANAL+ en 2026-27. Comme la Ligue Europa, elle se joue le jeudi ; ce jour-là, la liste ci-dessus affiche chaque match avec son heure et sa chaîne.",
    faqs=[("Quel jour se joue la Ligue Conférence ?", "Le jeudi, avec des coups d'envoi habituels à 18 h 45 et 21 h, heure de Paris.")],
    cta_sub="Une alerte 15 minutes avant chaque match de Ligue Conférence, avec la chaîne. 10 jours d'essai gratuit."),
  "laliga": dict(slug="liga", name="Liga",
    title="Liga espagnole : sur quelle chaîne voir les matchs aujourd'hui ?",
    desc="Les matchs de Liga du jour avec l'heure et la chaîne en France : en 2026-27, DAZN et Disney+ diffusent chacun les 380 matchs.",
    h1="Sur quelle chaîne voir la Liga aujourd'hui ?",
    rightsT="Qui diffuse la Liga en France en 2026-27 ?",
    rights="Après 14 saisons sur beIN SPORTS, la Liga est diffusée en France par DAZN et Disney+ à partir de 2026-27. Les deux plateformes proposent chacune les dix matchs de chaque journée : un seul des deux abonnements suffit pour suivre tout le championnat.",
    faqs=[("Faut-il DAZN et Disney+ pour voir toute la Liga ?", "Non. DAZN comme Disney+ diffusent les 380 matchs de la saison, un seul abonnement suffit."),
          ("La Liga est-elle encore sur beIN SPORTS ?", "Non, plus à partir de la saison 2026-27.")],
    cta_sub="Une alerte 15 minutes avant chaque match de Liga, avec la chaîne. 10 jours d'essai gratuit."),
 },
}
COMP_NAV = {"es": "Competiciones:", "fr": "Compétitions :"}
COMP_EMPTY = {
 "es": '<div class="state"><p>Hoy no hay partidos de %s. <a href="%s">Ver todos los partidos de fútbol de hoy</a></p></div>',
 "fr": '<div class="state"><p>Pas de match de %s aujourd\'hui. <a href="%s">Voir tous les matchs de foot du jour</a></p></div>',
}
APPLINE = {"es": "Recibe un aviso con el canal antes de cada partido:",
           "fr": "Recevez une alerte avec la chaîne avant chaque match :"}

def comp_path(lang, comp):
    return "/%s/%s/" % (SEG[lang], COMP_PAGES[lang][comp]["slug"])

def comp_alt_path(lang, comp):
    # Dil seçicide: o dilde aynı turnuva sayfası varsa ona, yoksa futbol sayfasına.
    return comp_path(lang, comp) if comp in COMP_PAGES.get(lang, {}) else path_for(lang, "football")

def comp_hreflangs(comp):
    return "\n  ".join('<link rel="alternate" hreflang="%s" href="%s">' % (l, BASE + comp_path(l, comp))
                       for l in COMP_PAGES if comp in COMP_PAGES[l])

def comp_links(lang, current=None):
    if lang not in COMP_PAGES:
        return ""
    out = ['<span>%s</span>' % COMP_NAV[lang]]
    for k in COMP_PAGES[lang]:
        cur = ' aria-current="true"' if k == current else ''
        out.append('<a href="%s"%s>%s</a>' % (comp_path(lang, k), cur, _comp_label(lang, k)))
    return '<nav class="sportnav compnav">' + "\n      ".join(out) + '</nav>'

def _comp_label(lang, k):
    # Kısa bağlantı adı: "la Champions League" -> "Champions League"
    n = COMP_PAGES[lang][k]["name"]
    return n[3:] if n.startswith("la ") else n

def play_link(lang, key):
    # Play kurulum yönlendiricisi: Play Console > Edinme raporunda kampanya ayrı görünür.
    ref = "utm_source=sportstvtoday&utm_medium=web&utm_campaign=web_%s_%s" % (lang, key)
    return GOOGLE + "&amp;referrer=" + urllib.parse.quote(ref, safe="")

def url_for(lang, sport=None):
    return BASE + path_for(lang, sport)

def path_for(lang, sport=None):
    # root-relative nav path — works over http and https, any host
    s = SEG[lang]
    p = "/" + (s + "/" if s else "")
    return p + (SPORT_SLUG[lang][sport] + "/" if sport else "")

L = {
 "en": dict(dir="ltr", store="Download",
   title="Sports on TV Today — What Channel & What Time",
   desc="Find what channel every match is on and what time it starts in your time zone. Live football, basketball & volleyball TV schedule, updated daily.",
   h1="What channel is the match on today?",
   sub="Every game, its exact kick-off time in your time zone, and the channel showing it — all in one place.",
   today="Today's matches",
   featT="Why fans use it",
   feats=[("📺","Channel for your country","See exactly which channel or streaming service is showing each match where you live."),
          ("🕒","Your local time","Kick-off times convert automatically to your device's time zone — no time-zone maths."),
          ("⚽","Every sport","Football, basketball, volleyball and motorsport — today's full TV schedule in one list."),
          ("🔔","Never miss a game","Get the free app for a reminder before every match you care about.")],
   faqT="Frequently asked questions",
   faqs=[("What channel is the game on today?","This page lists today's matches with the broadcaster for your country. Choose your country at the top to see the right channel or streaming service."),
         ("How do I know the match time where I live?","Kick-off times are shown automatically in your device's time zone, so the time you see is your local start time."),
         ("Which sports are covered?","Football, basketball, volleyball and motorsport — from Champions League and World Cup qualifiers to domestic leagues."),
         ("Is it free?","Yes. The website and the app are free. The app adds match reminders and notifications.")],
   proseT="Today's sport on TV, wherever you are",
   prose="Stop searching five sites to find out where a match is on. Sports on TV brings today's fixtures together with the broadcaster for your country and the kick-off time in your own time zone. Pick your country once and every game shows the channel or stream carrying it.",
   foot="Match times and TV channels, in your language and your time zone."),
 "tr": dict(dir="ltr", store="İndir",
   title="Maç Hangi Kanalda? Bugünkü Maçlar ve Saatleri",
   desc="Bugün hangi maç hangi kanalda, saat kaçta? Kendi saat diliminde canlı futbol, basketbol ve voleybol yayın rehberi — her gün güncel.",
   h1="Maç bugün hangi kanalda?",
   sub="Her maç, kendi saatinle tam başlama zamanı ve yayınlayan kanal — hepsi tek yerde.",
   today="Bugünkü maçlar",
   featT="Neden kullanılıyor",
   feats=[("📺","Ülkene göre kanal","Yaşadığın yerde her maçı hangi kanal veya yayın servisi veriyor, net gör."),
          ("🕒","Kendi saatin","Başlama saatleri cihazının saat dilimine otomatik çevrilir — hesap yok."),
          ("⚽","Her spor","Futbol, basketbol, voleybol ve motor sporları — bugünün tüm yayın rehberi tek listede."),
          ("🔔","Maçı kaçırma","Önemsediğin her maçtan önce hatırlatma için ücretsiz uygulamayı indir.")],
   faqT="Sıkça sorulan sorular",
   faqs=[("Maç bugün hangi kanalda?","Bu sayfa bugünkü maçları ülkene göre yayıncısıyla listeler. Üstten ülkeni seç, doğru kanal veya yayın servisi görünsün."),
         ("Maçın saatini kendi saat dilimimde nasıl görürüm?","Başlama saatleri cihazının saat diliminde otomatik gösterilir; gördüğün saat senin yerel başlama saatindir."),
         ("Hangi sporlar var?","Futbol, basketbol, voleybol ve motor sporları — Şampiyonlar Ligi ve Dünya Kupası elemelerinden yerel liglere."),
         ("Ücretsiz mi?","Evet. Site de uygulama da ücretsiz. Uygulama ayrıca maç hatırlatmaları ve bildirim ekler.")],
   proseT="Nerede olursan ol, bugünkü maçlar TV'de",
   prose="Bir maçın hangi kanalda olduğunu bulmak için beş siteyi dolaşmayı bırak. Maç Hangi Kanalda, bugünkü maçları ülkenin yayıncısı ve kendi saat dilimindeki başlama saatiyle bir araya getirir. Ülkeni bir kez seç, her maç onu veren kanalı veya yayını göstersin.",
   foot="Maç saatleri ve TV kanalları; kendi dilinde, kendi saat diliminde."),
 "de": dict(dir="ltr", store="Laden",
   title="Fußball heute im TV — Welcher Sender & Uhrzeit",
   desc="Welcher Sender überträgt heute welches Spiel und wann? Live-TV-Programm für Fußball, Basketball & Volleyball in deiner Zeitzone — täglich aktuell.",
   h1="Welcher Sender zeigt heute das Spiel?",
   sub="Jedes Spiel, die genaue Anstoßzeit in deiner Zeitzone und der übertragende Sender — alles an einem Ort.",
   today="Spiele heute",
   featT="Darum nutzen es Fans",
   feats=[("📺","Sender für dein Land","Sieh genau, welcher Sender oder Streamingdienst jedes Spiel bei dir überträgt."),
          ("🕒","Deine Ortszeit","Anstoßzeiten werden automatisch in die Zeitzone deines Geräts umgerechnet."),
          ("⚽","Jeder Sport","Fußball, Basketball, Volleyball und Motorsport — das ganze TV-Programm von heute in einer Liste."),
          ("🔔","Kein Spiel verpassen","Hol dir die kostenlose App für eine Erinnerung vor jedem wichtigen Spiel.")],
   faqT="Häufige Fragen",
   faqs=[("Welcher Sender zeigt heute das Spiel?","Diese Seite listet die heutigen Spiele mit dem Sender für dein Land. Wähle oben dein Land, um den richtigen Sender oder Stream zu sehen."),
         ("Wie sehe ich die Spielzeit in meiner Zeitzone?","Anstoßzeiten werden automatisch in der Zeitzone deines Geräts angezeigt — die angezeigte Zeit ist deine Ortszeit."),
         ("Welche Sportarten sind dabei?","Fußball, Basketball, Volleyball und Motorsport — von Champions League und WM-Qualifikation bis zu den Ligen."),
         ("Ist es kostenlos?","Ja. Website und App sind kostenlos. Die App bietet zusätzlich Spiel-Erinnerungen und Benachrichtigungen.")],
   proseT="Sport heute im TV, wo immer du bist",
   prose="Kein Suchen auf fünf Seiten mehr, um zu wissen, wo ein Spiel läuft. Sports on TV bündelt die heutigen Spiele mit dem Sender für dein Land und der Anstoßzeit in deiner Zeitzone. Land einmal wählen — jedes Spiel zeigt den passenden Sender oder Stream.",
   foot="Spielzeiten und TV-Sender — in deiner Sprache und Zeitzone."),
 "es": dict(dir="ltr", store="Descargar",
   title="Fútbol hoy en TV — Qué canal y a qué hora",
   desc="Descubre en qué canal es cada partido y a qué hora empieza en tu zona horaria. Guía de TV de fútbol, baloncesto y voleibol en vivo, actualizada a diario.",
   h1="¿En qué canal es el partido hoy?",
   sub="Cada partido, su hora exacta de inicio en tu zona horaria y el canal que lo emite — todo en un solo lugar.",
   today="Partidos de hoy",
   featT="Por qué lo usan",
   feats=[("📺","Canal de tu país","Mira exactamente qué canal o plataforma emite cada partido donde vives."),
          ("🕒","Tu hora local","Las horas de inicio se convierten automáticamente a la zona horaria de tu dispositivo."),
          ("⚽","Todos los deportes","Fútbol, baloncesto, voleibol y motor — toda la programación de hoy en una lista."),
          ("🔔","No te pierdas nada","Descarga la app gratis para recibir un aviso antes de cada partido.")],
   faqT="Preguntas frecuentes",
   faqs=[("¿En qué canal es el partido hoy?","Esta página muestra los partidos de hoy con el canal de tu país. Elige tu país arriba para ver el canal o la plataforma correcta."),
         ("¿Cómo sé la hora del partido en mi zona horaria?","Las horas se muestran automáticamente en la zona horaria de tu dispositivo, así que la hora que ves es tu hora local de inicio."),
         ("¿Qué deportes incluye?","Fútbol, baloncesto, voleibol y motor — desde la Champions y la clasificación del Mundial hasta las ligas."),
         ("¿Es gratis?","Sí. La web y la app son gratis. La app añade recordatorios y notificaciones de partidos.")],
   proseT="El deporte de hoy en la tele, estés donde estés",
   prose="Deja de mirar cinco webs para saber dónde dan un partido. Sports on TV reúne los partidos de hoy con el canal de tu país y la hora de inicio en tu zona horaria. Elige tu país una vez y cada partido mostrará el canal o la plataforma que lo emite.",
   foot="Horarios y canales de TV, en tu idioma y tu zona horaria."),
 "fr": dict(dir="ltr", store="Télécharger",
   title="Foot à la TV aujourd'hui — Quelle chaîne et heure",
   desc="Trouvez sur quelle chaîne passe chaque match et à quelle heure dans votre fuseau horaire. Programme TV foot, basket et volley en direct, mis à jour chaque jour.",
   h1="Le match est sur quelle chaîne aujourd'hui ?",
   sub="Chaque match, l'heure exacte du coup d'envoi dans votre fuseau et la chaîne qui le diffuse — au même endroit.",
   today="Matchs du jour",
   featT="Pourquoi les fans l'utilisent",
   feats=[("📺","La chaîne de votre pays","Voyez exactement quelle chaîne ou plateforme diffuse chaque match chez vous."),
          ("🕒","Votre heure locale","Les horaires sont convertis automatiquement dans le fuseau de votre appareil."),
          ("⚽","Tous les sports","Football, basket, volley et sport auto — tout le programme TV du jour en une liste."),
          ("🔔","Ne ratez aucun match","Téléchargez l'appli gratuite pour un rappel avant chaque match important.")],
   faqT="Questions fréquentes",
   faqs=[("Le match est sur quelle chaîne aujourd'hui ?","Cette page liste les matchs du jour avec le diffuseur de votre pays. Choisissez votre pays en haut pour voir la bonne chaîne ou plateforme."),
         ("Comment connaître l'heure du match chez moi ?","Les horaires s'affichent automatiquement dans le fuseau de votre appareil : l'heure affichée est votre heure locale."),
         ("Quels sports sont couverts ?","Football, basket, volley et sport auto — de la Ligue des Champions et des qualifs du Mondial aux championnats."),
         ("Est-ce gratuit ?","Oui. Le site et l'appli sont gratuits. L'appli ajoute des rappels et des notifications de matchs.")],
   proseT="Le sport du jour à la télé, où que vous soyez",
   prose="Fini de chercher sur cinq sites où passe un match. Sports on TV réunit les matchs du jour avec le diffuseur de votre pays et l'heure du coup d'envoi dans votre fuseau. Choisissez votre pays une fois et chaque match affiche la chaîne ou le stream qui le diffuse.",
   foot="Horaires et chaînes TV, dans votre langue et votre fuseau."),
 "it": dict(dir="ltr", store="Scarica",
   title="Partite oggi in TV — Che canale e a che ora",
   desc="Scopri su che canale è ogni partita e a che ora inizia nel tuo fuso orario. Guida TV di calcio, basket e volley in diretta, aggiornata ogni giorno.",
   h1="Su che canale è la partita oggi?",
   sub="Ogni partita, l'orario esatto d'inizio nel tuo fuso e il canale che la trasmette — tutto in un posto.",
   today="Partite di oggi",
   featT="Perché i tifosi la usano",
   feats=[("📺","Canale del tuo paese","Vedi esattamente quale canale o piattaforma trasmette ogni partita dove vivi."),
          ("🕒","La tua ora locale","Gli orari vengono convertiti automaticamente nel fuso del tuo dispositivo."),
          ("⚽","Ogni sport","Calcio, basket, volley e motori — tutto il programma TV di oggi in un elenco."),
          ("🔔","Non perdere una partita","Scarica l'app gratis per un promemoria prima di ogni partita che ti interessa.")],
   faqT="Domande frequenti",
   faqs=[("Su che canale è la partita oggi?","Questa pagina elenca le partite di oggi con l'emittente del tuo paese. Scegli il paese in alto per vedere il canale o la piattaforma giusta."),
         ("Come vedo l'orario della partita nel mio fuso?","Gli orari sono mostrati automaticamente nel fuso del tuo dispositivo, quindi l'ora che vedi è quella locale d'inizio."),
         ("Quali sport sono inclusi?","Calcio, basket, volley e motori — dalla Champions League e le qualificazioni ai Mondiali fino ai campionati."),
         ("È gratis?","Sì. Il sito e l'app sono gratuiti. L'app aggiunge promemoria e notifiche delle partite.")],
   proseT="Lo sport di oggi in TV, ovunque tu sia",
   prose="Basta cercare su cinque siti dove danno una partita. Sports on TV riunisce le partite di oggi con l'emittente del tuo paese e l'orario d'inizio nel tuo fuso. Scegli il paese una volta e ogni partita mostra il canale o lo streaming che la trasmette.",
   foot="Orari e canali TV, nella tua lingua e nel tuo fuso."),
 "pt": dict(dir="ltr", store="Baixar",
   title="Jogos hoje na TV — Que canal e horário",
   desc="Descubra em que canal passa cada jogo e a que horas começa no seu fuso. Guia de TV de futebol, basquete e vôlei ao vivo, atualizado todos os dias.",
   h1="Em que canal passa o jogo hoje?",
   sub="Cada jogo, o horário exato de início no seu fuso e o canal que transmite — tudo num só lugar.",
   today="Jogos de hoje",
   featT="Por que os torcedores usam",
   feats=[("📺","Canal do seu país","Veja exatamente qual canal ou plataforma transmite cada jogo onde você mora."),
          ("🕒","Seu horário local","Os horários são convertidos automaticamente para o fuso do seu aparelho."),
          ("⚽","Todos os esportes","Futebol, basquete, vôlei e automobilismo — toda a programação de hoje em uma lista."),
          ("🔔","Não perca nenhum jogo","Baixe o app grátis para um lembrete antes de cada jogo que importa.")],
   faqT="Perguntas frequentes",
   faqs=[("Em que canal passa o jogo hoje?","Esta página lista os jogos de hoje com a emissora do seu país. Escolha seu país no topo para ver o canal ou a plataforma certa."),
         ("Como sei o horário do jogo no meu fuso?","Os horários aparecem automaticamente no fuso do seu aparelho, então a hora que você vê é o início no seu horário local."),
         ("Quais esportes são cobertos?","Futebol, basquete, vôlei e automobilismo — da Champions e eliminatórias da Copa às ligas nacionais."),
         ("É grátis?","Sim. O site e o app são grátis. O app adiciona lembretes e notificações de jogos.")],
   proseT="O esporte de hoje na TV, onde você estiver",
   prose="Pare de procurar em cinco sites onde passa um jogo. Sports on TV reúne os jogos de hoje com a emissora do seu país e o horário de início no seu fuso. Escolha seu país uma vez e cada jogo mostra o canal ou o streaming que transmite.",
   foot="Horários e canais de TV, no seu idioma e no seu fuso."),
 "ar": dict(dir="rtl", store="تحميل",
   title="مباريات اليوم على التلفاز — أي قناة ومتى",
   desc="اعرف أي قناة تنقل كل مباراة ومتى تبدأ بتوقيتك المحلي. دليل بث مباشر لكرة القدم والسلة والطائرة، يُحدَّث يوميًا.",
   h1="على أي قناة المباراة اليوم؟",
   sub="كل مباراة، وقت انطلاقها الدقيق بتوقيتك، والقناة الناقلة لها — في مكان واحد.",
   today="مباريات اليوم",
   featT="لماذا يستخدمه المشجعون",
   feats=[("📺","قناة بلدك","شاهد بالضبط أي قناة أو منصة تنقل كل مباراة في مكانك."),
          ("🕒","توقيتك المحلي","تُحوَّل أوقات الانطلاق تلقائيًا إلى المنطقة الزمنية لجهازك."),
          ("⚽","كل الرياضات","كرة القدم والسلة والطائرة ورياضة السيارات — جدول اليوم كاملًا في قائمة واحدة."),
          ("🔔","لا تفوّت أي مباراة","نزّل التطبيق المجاني لتذكيرك قبل كل مباراة تهمّك.")],
   faqT="الأسئلة الشائعة",
   faqs=[("على أي قناة المباراة اليوم؟","تعرض هذه الصفحة مباريات اليوم مع الناقل في بلدك. اختر بلدك بالأعلى لرؤية القناة أو المنصة الصحيحة."),
         ("كيف أعرف موعد المباراة بتوقيتي؟","تُعرض الأوقات تلقائيًا بالمنطقة الزمنية لجهازك، فالوقت الذي تراه هو موعد البدء المحلي."),
         ("ما الرياضات المشمولة؟","كرة القدم والسلة والطائرة ورياضة السيارات — من دوري الأبطال وتصفيات كأس العالم إلى الدوريات المحلية."),
         ("هل هو مجاني؟","نعم. الموقع والتطبيق مجانيان. يضيف التطبيق تذكيرات وإشعارات المباريات.")],
   proseT="رياضة اليوم على التلفاز أينما كنت",
   prose="توقّف عن البحث في خمسة مواقع لمعرفة أين تُذاع المباراة. يجمع Sports on TV مباريات اليوم مع الناقل في بلدك ووقت الانطلاق بتوقيتك. اختر بلدك مرة واحدة، وستعرض كل مباراة القناة أو المنصة الناقلة لها.",
   foot="مواعيد المباريات وقنوات التلفاز، بلغتك وبتوقيتك."),
}

# Only injected on the root (English) page: send visitors to their own language
# unless they've explicitly chosen one (stored on language-select change).
ROOT_REDIRECT = ("<script>(function(){try{var s=['tr','de','es','fr','it','pt','ar'],"
  "p=localStorage.getItem('sot_lang'),l=(p||(navigator.language||'en').slice(0,2)).toLowerCase();"
  "if(s.indexOf(l)>=0)location.replace(l+'/');}catch(e){}})();</script>")

def hreflangs(current, sport=None):
    # Alternatifler AYNI sporun diğer dillerine gider — futbol sayfası başka
    # dilin ana sayfasına işaret ederse Google eşleşmeyi yok sayar.
    out = []
    for lang in SEG:
        out.append('<link rel="alternate" hreflang="%s" href="%s">' % (lang, url_for(lang, sport)))
    out.append('<link rel="alternate" hreflang="x-default" href="%s">' % url_for("en", sport))
    return "\n  ".join(out)

def lang_options(current, sport=None):
    opts = []
    for lang in SEG:
        sel = " selected" if lang == current else ""
        opts.append('<option value="%s" data-lang="%s"%s>%s</option>' % (path_for(lang, sport), lang, sel, LANG_NATIVE[lang]))
    return "".join(opts)

def lang_links(current, sport=None):
    out = []
    for lang in SEG:
        cur = ' aria-current="true"' if lang == current else ""
        out.append('<a href="%s"%s>%s</a>' % (path_for(lang, sport), cur, LANG_NATIVE[lang]))
    return "\n      ".join(out)

def sport_links(lang, current_sport):
    # Ana sayfa ↔ spor sayfaları arası iç bağlantı. Tarayıcının sayfaları
    # bulmasını sağlar ve her spor sayfasına konu bağlamı verir.
    out = ['<a href="%s"%s>%s</a>' % (path_for(lang), '' if current_sport else ' aria-current="true"', L[lang]["today"])]
    for s in SPORTS:
        cur = ' aria-current="true"' if s == current_sport else ''
        out.append('<a href="%s"%s>%s</a>' % (path_for(lang, s), cur, SPORT_LABEL[lang][s]))
    return "\n      ".join(out)

def _match_ld_tag(lang, sport=None, comp=None):
    """JSON-LD SportsEvent script etiketi — mac yoksa hic basma."""
    ld = prerender.sports_ld(lang, sport, comp)
    if not ld:
        return ""
    return chr(10) + '  <script type="application/ld+json">' + ld + '</script>'


def page(lang, sport=None, comp=None):
    d = dict(L[lang])
    c = COMP_PAGES[lang][comp] if comp else None
    if sport:
        t, desc, h1, prose = SPORT_COPY[lang][sport]
        d.update(title=t, desc=desc, h1=h1, prose=prose,
                 proseT=SPORT_LABEL[lang][sport] + " — " + L[lang]["today"])
    if c:
        d.update(title=c["title"], desc=c["desc"], h1=c["h1"], prose=c["rights"],
                 proseT=c["rightsT"], sub=c["cta_sub"])
    feats = "\n".join(
        '<div class="feat"><div class="ic">%s</div><h3>%s</h3><p>%s</p></div>' % (FEAT_ICONS[idx], h, p)
        for idx, (i, h, p) in enumerate(d["feats"]))
    # SSS yalnız ana sayfada. Aynı SSS işaretlemesini 40 sayfaya kopyalamak
    # Google'ın "yinelenen içerik" saydığı şeydir; spor sayfaları bunun yerine
    # breadcrumb işaretlemesi alır. Turnuva sayfalarının SSS'i kendine özgü.
    if c:
        faq_section = '<section class="faq"><h2>%s</h2>%s</section>' % (d["faqT"], "\n".join(
            '<details><summary>%s</summary><p>%s</p></details>' % (q, a) for (q, a) in c["faqs"]))
        extra_ld = {"@context":"https://schema.org","@graph":[
            {"@type":"FAQPage","mainEntity":[
                {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for (q,a) in c["faqs"]]},
            {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":BRAND,"item":url_for(lang)},
                {"@type":"ListItem","position":2,"name":SPORT_LABEL[lang]["football"],"item":url_for(lang, "football")},
                {"@type":"ListItem","position":3,"name":_comp_label(lang, comp),"item":BASE + comp_path(lang, comp)}]}]}
    elif sport:
        faq_section = ""
        extra_ld = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":BRAND,"item":url_for(lang)},
            {"@type":"ListItem","position":2,"name":SPORT_LABEL[lang][sport],"item":url_for(lang, sport)}]}
    else:
        faqs = "\n".join(
            '<details><summary>%s</summary><p>%s</p></details>' % (q, a) for (q, a) in d["faqs"])
        faq_section = '<section class="faq"><h2>%s</h2>%s</section>' % (d["faqT"], faqs)
        extra_ld = {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
            {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for (q,a) in d["faqs"]]}
    site_ld = {"@context":"https://schema.org","@graph":[
        {"@type":"WebSite","name":BRAND,"url":url_for(lang),"inLanguage":lang},
        {"@type":"SoftwareApplication","name":BRAND,"operatingSystem":"iOS, Android",
         "applicationCategory":"SportsApplication","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},
         "url":url_for(lang)}]}
    canon = (BASE + comp_path(lang, comp)) if comp else url_for(lang, sport)
    key = comp or sport or "home"
    if comp:
        prematches = prerender.kartlar(lang, None, comp) or \
            COMP_EMPTY[lang] % (_comp_label(lang, comp), path_for(lang, "football"))
        alt_links = "\n  ".join([comp_hreflangs(comp)])
        langopts = "".join('<option value="%s" data-lang="%s"%s>%s</option>' % (
            comp_alt_path(l, comp), l, " selected" if l == lang else "", LANG_NATIVE[l]) for l in SEG)
        langlinks = "\n      ".join('<a href="%s"%s>%s</a>' % (
            comp_alt_path(l, comp), ' aria-current="true"' if l == lang else "", LANG_NATIVE[l]) for l in SEG)
        appline = '<p class="appline">%s <a href="%s" rel="nofollow">App Store</a> · <a href="%s" rel="nofollow">Google Play</a></p>' % (
            APPLINE[lang], APPLE, play_link(lang, key))
        pagejs = "window.__SPORT__=null;window.__COMP__=%s;window.__EMPTY__=%s;" % (
            json.dumps(comp), json.dumps(COMP_EMPTY[lang] % (_comp_label(lang, comp), path_for(lang, "football")), ensure_ascii=False))
        filters = ""
    else:
        prematches = prerender.kartlar(lang, sport)
        alt_links = hreflangs(lang, sport)
        langopts = lang_options(lang, sport)
        langlinks = lang_links(lang, sport)
        appline = ""
        pagejs = "window.__SPORT__=%s;" % json.dumps(sport)
        filters = '<div class="filters" id="filters"></div>'
    # Turnuva bağlantıları yalnız ana sayfada, futbol sayfasında ve turnuva sayfalarında.
    complinks = comp_links(lang, comp) if (comp or sport in (None, "football")) else ""
    return """<!doctype html>
<html lang="{lang}" dir="{dir}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  {root_redirect}
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{canon}">
  {hreflangs}
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{brand}">
  <meta property="og:locale" content="{oglocale}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{canon}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#0b8f5a" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#0b0f17" media="(prefers-color-scheme: dark)">
  <link rel="icon" href="{favicon}">
  <link rel="preconnect" href="https://raw.githubusercontent.com" crossorigin>
  <link rel="stylesheet" href="/assets/styles.css">
  <script type="application/ld+json">{site_ld}</script>
  <script type="application/ld+json">{faq_ld}</script>{match_ld}{analytics}
</head>
<body>
  <header class="site"><div class="wrap hrow">
    <a class="brand" href="{selfurl}"><span class="logo">{logo_svg}</span><span class="name">{brand}</span></a>
    <span class="spacer"></span>
    <div class="selects">
      <select id="countrySel" class="ctl" aria-label="Country"></select>
      <select class="ctl" aria-label="Language" onchange="sotSetLang(this)">{langopts}</select>
      <button class="iconbtn" id="themeBtn" aria-label="Theme">{theme_svg}</button>
    </div>
  </div></header>

  <main class="wrap">
    <h1 class="ptitle">{h1}</h1>
    {appline}
    <div class="section-head">
      <span class="tzchip" id="tzchip"></span>
      <span class="spacer"></span>
      <span class="tzchip" id="updated"></span>
    </div>
    <div class="tzchip" id="countryLbl" style="margin-bottom:6px;display:inline-block"></div>
    <nav class="sportnav">
      {sportlinks}
    </nav>
    {complinks}
    {filters}
    <p class="daysum">{daysum}</p>
    <div class="matchlist" id="matchlist">{prematches}</div>

    <section class="features">{feats}</section>

    <section class="prose"><h2>{proseT}</h2><p>{prose}</p></section>

    {faq_section}

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
    <p style="margin:12px 0 0">{foot}</p>
  </div></footer>
  <script>{pagejs}</script>
  <script src="/assets/app.js?v={ASSET_VER}"></script>
</body>
</html>""".format(
        ASSET_VER=ASSET_VER,
        lang=lang, dir=d["dir"], title=d["title"], desc=d["desc"], canon=canon,
        hreflangs=alt_links, brand=BRAND, oglocale=OG_LOCALE[lang],
        base=BASE, selfurl=path_for(lang), langopts=langopts,
        h1=d["h1"], sub=d["sub"], apple=APPLE, google=play_link(lang, key), store=d["store"], cta=CTA[lang],
        today=d["today"], feats=feats, proseT=d["proseT"], prose=d["prose"],
        faq_section=faq_section, langlinks=langlinks, foot=d["foot"],
        footlinks=foot_links(lang),
        sportlinks=sport_links(lang, "football" if comp else sport), pagejs=pagejs,
        complinks=complinks, filters=filters, appline=appline,
        prematches=prematches,
        daysum=prerender.ozet(lang, sport, comp),
        match_ld=_match_ld_tag(lang, sport, comp),
        apple_svg=APPLE_SVG, google_svg=GOOGLE_SVG, favicon=FAVICON,
        logo_svg=LOGO_SVG, theme_svg=THEME_SVG,
        # Dil yönlendirmesi yalnız kök sayfada; spor sayfasında olursa
        # ziyaretçiyi konudan koparıp ana sayfaya atar.
        root_redirect=(ROOT_REDIRECT if (lang == "en" and not sport) else ""), analytics=analytics_tag(),
        site_ld=json.dumps(site_ld, ensure_ascii=False), faq_ld=json.dumps(extra_ld, ensure_ascii=False))

# ── Hakkında sayfası (8 dil) ──
# Claude for Startups başvurusu (Eki 2026): değerlendiren kişi sitede kim
# olduğumuzu, ne yaptığımızı ve nasıl ulaşılacağını arıyor. Her sayfanın
# altbilgisinden bağlanır. Paragraflardaki {email} {privacy} {founder}
# yer tutucuları about_page() içinde doldurulur.
CONTACT = "esat@sportstvtoday.com"   # Cloudflare Email Routing -> ssaglamess@gmail.com
FOUNDER = "Muhammet Esat Sağlam"
PRIVACY_URL = "https://seslitespih.github.io/mac-hatirlatici/privacy.html"   # uygulamanın paywall'daki linki
ABOUT_SLUG = {"en":"about", "tr":"hakkinda", "de":"ueber-uns", "es":"sobre-nosotros",
              "fr":"a-propos", "it":"chi-siamo", "pt":"sobre", "ar":"about"}
ABOUT_LBL = {"en":"About", "tr":"Hakkında", "de":"Über uns", "es":"Sobre nosotros",
             "fr":"À propos", "it":"Chi siamo", "pt":"Sobre", "ar":"من نحن"}
CONTACT_LBL = {"en":"Contact", "tr":"İletişim", "de":"Kontakt", "es":"Contacto",
               "fr":"Contact", "it":"Contatti", "pt":"Contato", "ar":"تواصل معنا"}
ABOUT = {
 "en": dict(
   title="About Sports on TV — Who We Are & How It Works",
   desc="Sports on TV is an independent sports TV guide that shows which channel carries each match in your country, at your local time. Who we are, how our schedule is researched and how to reach us.",
   h1="About Sports on TV", privacy="privacy policy",
   secs=[("What we do", "Sports on TV tells you which TV channel or streaming service shows today's matches in your country, with kickoff times in your own time zone. We cover football, basketball, volleyball and motorsport for more than 40 countries, in 8 languages. The website is free, and so is our Match Reminder app for iPhone and Android."),
         ("How our schedule is made", "Broadcast rights differ from country to country, and often from match to match. Every day, an AI research agent built on Claude, the AI model made by Anthropic, reads broadcaster schedules and official league sources and records the channel for each match in each country. Automated checks reject uncertain channels and wrong dates before anything is published. Kickoff times are stored in UTC and converted to your time zone on your device. Channels can still change at short notice, so check with your broadcaster before a big game."),
         ("Who we are", "Sports on TV is an independent, self-funded project founded in 2026 by {founder} in Türkiye. We are not affiliated with any broadcaster, league or club; team, competition and channel names belong to their owners."),
         ("Contact", "Questions, corrections or partnership ideas: {email}. If you spot a wrong channel, tell us the match and your country and we will fix it."),
         ("Privacy", "You don't need an account to use this site. We use Google Analytics to count visits, and your country, language and theme choices are stored only in your browser. The Match Reminder app has its own {privacy}.")]),
 "tr": dict(
   title="Sports on TV Hakkında — Biz Kimiz, Nasıl Çalışıyoruz",
   desc="Sports on TV, her maçın senin ülkende hangi kanalda ve senin saatinle kaçta olduğunu gösteren bağımsız bir spor yayın rehberi. Biz kimiz, programı nasıl hazırlıyoruz, bize nasıl ulaşırsın.",
   h1="Sports on TV Hakkında", privacy="gizlilik politikası",
   secs=[("Ne yapıyoruz", "Sports on TV, bugünkü maçların senin ülkende hangi TV kanalında ya da dijital platformda yayınlanacağını, başlama saatiyle birlikte kendi saat diliminde gösterir. Futbol, basketbol, voleybol ve motor sporlarını 40'tan fazla ülke için 8 dilde sunuyoruz. Site ücretsiz; iPhone ve Android uygulamamız da öyle."),
         ("Yayın programı nasıl hazırlanıyor", "Yayın hakları ülkeden ülkeye, çoğu zaman da maçtan maça değişir. Her gün, Anthropic'in yapay zekâ modeli Claude üzerine kurulu bir araştırma ajanı yayıncıların programlarını ve liglerin resmî kaynaklarını okuyup her maçın her ülkedeki kanalını kaydeder. Otomatik kontroller, emin olunamayan kanalları ve hatalı tarihleri yayına girmeden eler. Başlama saatleri UTC olarak saklanır ve cihazında senin saat dilimine çevrilir. Kanallar son anda değişebilir; büyük maçlardan önce yayıncını da kontrol et."),
         ("Biz kimiz", "Sports on TV, 2026'da {founder} tarafından Türkiye'de kurulan, bağımsız ve kendi kaynaklarıyla yürüyen bir projedir. Hiçbir yayıncı, lig ya da kulüple bağlantımız yoktur; takım, turnuva ve kanal adları sahiplerine aittir."),
         ("İletişim", "Soru, düzeltme ya da iş birliği önerileri için: {email}. Yanlış bir kanal görürsen maçı ve ülkeni yaz, düzeltelim."),
         ("Gizlilik", "Siteyi kullanmak için hesap gerekmez. Ziyaretleri saymak için Google Analytics kullanıyoruz; ülke, dil ve tema seçimlerin yalnızca tarayıcında saklanır. Uygulamamızın ayrı bir {privacy} var.")]),
 "de": dict(
   title="Über Sports on TV — Wer wir sind & wie es funktioniert",
   desc="Sports on TV ist ein unabhängiger Sport-TV-Guide: welcher Sender jedes Spiel in deinem Land zeigt, zu deiner Ortszeit. Wer wir sind, wie wir das Programm recherchieren und wie du uns erreichst.",
   h1="Über Sports on TV", privacy="Datenschutzerklärung",
   secs=[("Was wir machen", "Sports on TV zeigt dir, welcher TV-Sender oder Streamingdienst die heutigen Spiele in deinem Land überträgt – mit Anstoßzeiten in deiner Zeitzone. Wir decken Fußball, Basketball, Volleyball und Motorsport in mehr als 40 Ländern und 8 Sprachen ab. Die Website ist kostenlos, ebenso unsere App für iPhone und Android."),
         ("So entsteht unser Programm", "Übertragungsrechte unterscheiden sich von Land zu Land und oft von Spiel zu Spiel. Jeden Tag liest ein KI-Recherche-Agent auf Basis von Claude, dem KI-Modell von Anthropic, die Programme der Sender und offizielle Quellen der Ligen und erfasst für jedes Spiel den Sender in jedem Land. Automatische Prüfungen sortieren unsichere Sender und falsche Termine aus, bevor etwas veröffentlicht wird. Anstoßzeiten werden in UTC gespeichert und auf deinem Gerät in deine Zeitzone umgerechnet. Sender können sich kurzfristig ändern – prüfe vor einem großen Spiel am besten auch beim Sender."),
         ("Wer wir sind", "Sports on TV ist ein unabhängiges, selbstfinanziertes Projekt, das 2026 von {founder} in der Türkei gegründet wurde. Wir sind mit keinem Sender, keiner Liga und keinem Verein verbunden; Team-, Wettbewerbs- und Sendernamen gehören ihren Inhabern."),
         ("Kontakt", "Fragen, Korrekturen oder Ideen für eine Zusammenarbeit: {email}. Wenn dir ein falscher Sender auffällt, nenne uns das Spiel und dein Land – wir korrigieren es."),
         ("Datenschutz", "Für diese Website brauchst du kein Konto. Wir nutzen Google Analytics, um Besuche zu zählen; deine Auswahl von Land, Sprache und Design wird nur in deinem Browser gespeichert. Für unsere App gilt eine eigene {privacy}.")]),
 "es": dict(
   title="Sobre Sports on TV — Quiénes somos y cómo funciona",
   desc="Sports on TV es una guía independiente de deportes en TV: qué canal emite cada partido en tu país y a tu hora local. Quiénes somos, cómo preparamos la programación y cómo contactarnos.",
   h1="Sobre Sports on TV", privacy="política de privacidad",
   secs=[("Qué hacemos", "Sports on TV te dice qué canal de televisión o plataforma de streaming emite los partidos de hoy en tu país, con la hora de inicio en tu propia zona horaria. Cubrimos fútbol, baloncesto, voleibol y motor en más de 40 países y en 8 idiomas. La web es gratuita, igual que nuestra app para iPhone y Android."),
         ("Cómo se prepara la programación", "Los derechos de emisión cambian de un país a otro y, a menudo, de un partido a otro. Cada día, un agente de investigación con IA basado en Claude, el modelo de IA de Anthropic, lee la programación de las cadenas y las fuentes oficiales de las ligas y registra el canal de cada partido en cada país. Unos controles automáticos descartan los canales dudosos y las fechas erróneas antes de publicar nada. Las horas de inicio se guardan en UTC y se convierten a tu zona horaria en tu dispositivo. Los canales pueden cambiar a última hora, así que consulta también a tu operador antes de un partido importante."),
         ("Quiénes somos", "Sports on TV es un proyecto independiente y autofinanciado, fundado en 2026 por {founder} en Turquía. No tenemos relación con ninguna cadena, liga ni club; los nombres de equipos, competiciones y canales pertenecen a sus propietarios."),
         ("Contacto", "Preguntas, correcciones o propuestas de colaboración: {email}. Si ves un canal incorrecto, dinos el partido y tu país y lo corregimos."),
         ("Privacidad", "No necesitas una cuenta para usar esta web. Usamos Google Analytics para contar las visitas, y tus preferencias de país, idioma y tema se guardan solo en tu navegador. Nuestra app tiene su propia {privacy}.")]),
 "fr": dict(
   title="À propos de Sports on TV — Qui sommes-nous et comment ça marche",
   desc="Sports on TV est un guide TV sportif indépendant : quelle chaîne diffuse chaque match dans votre pays, à votre heure locale. Qui nous sommes, comment nous établissons le programme et comment nous joindre.",
   h1="À propos de Sports on TV", privacy="politique de confidentialité",
   secs=[("Ce que nous faisons", "Sports on TV vous indique quelle chaîne de télévision ou quelle plateforme de streaming diffuse les matchs du jour dans votre pays, avec l'heure du coup d'envoi dans votre fuseau horaire. Nous couvrons le football, le basket-ball, le volley-ball et le sport automobile dans plus de 40 pays, en 8 langues. Le site est gratuit, tout comme notre application pour iPhone et Android."),
         ("Comment le programme est établi", "Les droits de diffusion varient d'un pays à l'autre, et souvent d'un match à l'autre. Chaque jour, un agent de recherche IA construit sur Claude, le modèle d'IA d'Anthropic, lit les programmes des diffuseurs et les sources officielles des ligues, puis enregistre la chaîne de chaque match dans chaque pays. Des contrôles automatiques écartent les chaînes incertaines et les dates erronées avant toute publication. Les heures de coup d'envoi sont stockées en UTC et converties dans votre fuseau horaire sur votre appareil. Les chaînes peuvent changer au dernier moment : avant un grand match, vérifiez aussi auprès de votre diffuseur."),
         ("Qui sommes-nous", "Sports on TV est un projet indépendant et autofinancé, fondé en 2026 par {founder} en Turquie. Nous ne sommes liés à aucun diffuseur, aucune ligue ni aucun club ; les noms d'équipes, de compétitions et de chaînes appartiennent à leurs propriétaires."),
         ("Contact", "Questions, corrections ou idées de partenariat : {email}. Si vous repérez une chaîne erronée, indiquez-nous le match et votre pays : nous la corrigerons."),
         ("Confidentialité", "Aucun compte n'est nécessaire pour utiliser ce site. Nous utilisons Google Analytics pour compter les visites ; vos choix de pays, de langue et de thème sont enregistrés uniquement dans votre navigateur. Notre application dispose de sa propre {privacy}.")]),
 "it": dict(
   title="Chi siamo — Sports on TV e come funziona",
   desc="Sports on TV è una guida TV sportiva indipendente: quale canale trasmette ogni partita nel tuo paese, all'ora locale. Chi siamo, come prepariamo il palinsesto e come contattarci.",
   h1="Sports on TV: chi siamo", privacy="informativa sulla privacy",
   secs=[("Cosa facciamo", "Sports on TV ti dice quale canale TV o servizio di streaming trasmette le partite di oggi nel tuo paese, con l'orario d'inizio nel tuo fuso orario. Copriamo calcio, basket, pallavolo e motori in oltre 40 paesi e in 8 lingue. Il sito è gratuito, così come la nostra app per iPhone e Android."),
         ("Come nasce il palinsesto", "I diritti TV cambiano da paese a paese e spesso da partita a partita. Ogni giorno un agente di ricerca basato su Claude, il modello di IA di Anthropic, legge i palinsesti delle emittenti e le fonti ufficiali delle leghe e registra il canale di ogni partita in ogni paese. Controlli automatici scartano i canali incerti e le date errate prima di pubblicare qualsiasi cosa. Gli orari d'inizio sono salvati in UTC e convertiti nel tuo fuso orario sul tuo dispositivo. I canali possono cambiare all'ultimo momento: prima di una partita importante, verifica anche con la tua emittente."),
         ("Chi siamo", "Sports on TV è un progetto indipendente e autofinanziato, fondato nel 2026 da {founder} in Turchia. Non siamo affiliati ad alcuna emittente, lega o club; i nomi di squadre, competizioni e canali appartengono ai rispettivi proprietari."),
         ("Contatti", "Domande, correzioni o proposte di collaborazione: {email}. Se trovi un canale sbagliato, indicaci la partita e il tuo paese e lo correggeremo."),
         ("Privacy", "Per usare questo sito non serve un account. Usiamo Google Analytics per contare le visite; le tue scelte di paese, lingua e tema restano salvate solo nel tuo browser. La nostra app ha una propria {privacy}.")]),
 "pt": dict(
   title="Sobre o Sports on TV — Quem somos e como funciona",
   desc="O Sports on TV é um guia independente de esportes na TV: qual canal transmite cada jogo no seu país, no seu horário local. Quem somos, como montamos a programação e como falar com a gente.",
   h1="Sobre o Sports on TV", privacy="política de privacidade",
   secs=[("O que fazemos", "O Sports on TV mostra qual canal de TV ou serviço de streaming transmite os jogos de hoje no seu país, com o horário de início no seu fuso horário. Cobrimos futebol, basquete, vôlei e automobilismo em mais de 40 países, em 8 idiomas. O site é gratuito, assim como o nosso app para iPhone e Android."),
         ("Como a programação é feita", "Os direitos de transmissão mudam de um país para outro e, muitas vezes, de um jogo para outro. Todos os dias, um agente de pesquisa com IA baseado no Claude, o modelo de IA da Anthropic, lê as grades das emissoras e as fontes oficiais das ligas e registra o canal de cada jogo em cada país. Verificações automáticas descartam canais incertos e datas erradas antes de qualquer publicação. Os horários de início são armazenados em UTC e convertidos para o seu fuso horário no seu aparelho. Os canais podem mudar de última hora, então confira também com a sua emissora antes de um jogo importante."),
         ("Quem somos", "O Sports on TV é um projeto independente e autofinanciado, fundado em 2026 por {founder}, na Turquia. Não temos vínculo com nenhuma emissora, liga ou clube; os nomes de times, competições e canais pertencem aos seus donos."),
         ("Contato", "Dúvidas, correções ou ideias de parceria: {email}. Se você encontrar um canal errado, diga o jogo e o seu país que a gente corrige."),
         ("Privacidade", "Você não precisa de conta para usar este site. Usamos o Google Analytics para contar as visitas, e suas escolhas de país, idioma e tema ficam salvas só no seu navegador. O nosso app tem a sua própria {privacy}.")]),
 "ar": dict(
   title="عن Sports on TV — من نحن وكيف نعمل",
   desc="Sports on TV دليل مستقل للرياضة على التلفزيون: أي قناة تنقل كل مباراة في بلدك وبتوقيتك المحلي. تعرّف على من نحن، وكيف نعدّ جدول البث، وكيف تتواصل معنا.",
   h1="عن Sports on TV", privacy="سياسة خصوصية",
   secs=[("ماذا نقدّم", "يخبرك Sports on TV بالقناة التلفزيونية أو خدمة البث التي تنقل مباريات اليوم في بلدك، مع موعد الانطلاق بحسب منطقتك الزمنية. نغطي كرة القدم وكرة السلة والكرة الطائرة ورياضة السيارات في أكثر من 40 دولة وبثماني لغات. الموقع مجاني، وكذلك تطبيقنا على iPhone وAndroid."),
         ("كيف نعدّ جدول البث", "تختلف حقوق البث من بلد إلى آخر، وكثيرًا من مباراة إلى أخرى. كل يوم، يقرأ وكيل بحث بالذكاء الاصطناعي مبني على Claude، نموذج الذكاء الاصطناعي من Anthropic، جداول القنوات والمصادر الرسمية للدوريات، ويسجّل قناة كل مباراة في كل بلد. وتستبعد فحوص تلقائية القنوات غير المؤكدة والتواريخ الخاطئة قبل نشر أي شيء. تُحفظ مواعيد الانطلاق بتوقيت UTC وتُحوَّل إلى منطقتك الزمنية على جهازك. قد تتغير القنوات في اللحظة الأخيرة، لذا تحقّق أيضًا من القناة الناقلة قبل المباريات الكبرى."),
         ("من نحن", "Sports on TV مشروع مستقل وممول ذاتيًا، أسسه {founder} في تركيا عام 2026. لا نرتبط بأي قناة أو دوري أو نادٍ، وأسماء الفرق والبطولات والقنوات ملك لأصحابها."),
         ("تواصل معنا", "للأسئلة أو التصحيحات أو أفكار الشراكة: {email}. إذا لاحظت قناة خاطئة، أخبرنا بالمباراة وببلدك وسنصححها."),
         ("الخصوصية", "لا تحتاج إلى حساب لاستخدام هذا الموقع. نستخدم Google Analytics لإحصاء الزيارات، وتُحفظ اختياراتك للبلد واللغة والمظهر في متصفحك فقط. ولتطبيقنا {privacy} خاصة به.")]),
}

def about_path(lang):
    s = SEG[lang]
    return "/" + (s + "/" if s else "") + ABOUT_SLUG[lang] + "/"

def foot_links(lang):
    return '<a href="%s">%s</a> · <a href="mailto:%s">%s</a>' % (
        about_path(lang), ABOUT_LBL[lang], CONTACT, CONTACT_LBL[lang])

# Hakkında sayfası app.js yüklemez (maç listesi yok); tema ve dil seçici
# için app.js'teki initTheme/sotSetLang'in küçük kopyası.
ABOUT_JS = ('<script>(function(){var d=document.documentElement;'
            'try{var s=localStorage.getItem("sot_theme");if(s)d.setAttribute("data-theme",s)}catch(e){}'
            'window.sotSetLang=function(sel){try{localStorage.setItem("sot_lang",'
            'sel.options[sel.selectedIndex].getAttribute("data-lang")||"en")}catch(e){}location.href=sel.value};'
            'document.addEventListener("DOMContentLoaded",function(){var b=document.getElementById("themeBtn");'
            'if(b)b.addEventListener("click",function(){var c=d.getAttribute("data-theme");'
            'var n=c==="dark"?"light":(c==="light"?"dark":(matchMedia("(prefers-color-scheme: dark)").matches?"light":"dark"));'
            'd.setAttribute("data-theme",n);try{localStorage.setItem("sot_theme",n)}catch(e){}})})})();</script>')

def about_page(lang):
    a = ABOUT[lang]
    fill = dict(email='<a href="mailto:%s">%s</a>' % (CONTACT, CONTACT),
                privacy='<a href="%s" rel="nofollow">%s</a>' % (PRIVACY_URL, a["privacy"]),
                founder=FOUNDER)
    secs = "\n    ".join('<section class="prose"><h2>%s</h2><p>%s</p></section>' % (h, p.format(**fill))
                         for h, p in a["secs"])
    alts = "\n  ".join(['<link rel="alternate" hreflang="%s" href="%s">' % (l, BASE + about_path(l)) for l in SEG]
                       + ['<link rel="alternate" hreflang="x-default" href="%s">' % (BASE + about_path("en"))])
    opts = "".join('<option value="%s" data-lang="%s"%s>%s</option>' % (
        about_path(l), l, " selected" if l == lang else "", LANG_NATIVE[l]) for l in SEG)
    langlinks = "\n      ".join('<a href="%s"%s>%s</a>' % (
        about_path(l), ' aria-current="true"' if l == lang else "", LANG_NATIVE[l]) for l in SEG)
    canon = BASE + about_path(lang)
    ld = {"@context":"https://schema.org","@type":"AboutPage","name":a["title"],"url":canon,"inLanguage":lang,
          "mainEntity":{"@type":"Organization","name":BRAND,"url":BASE + "/","email":CONTACT,
                        "foundingDate":"2026","founder":{"@type":"Person","name":FOUNDER},
                        "sameAs":[APPLE, GOOGLE]}}
    return """<!doctype html>
<html lang="{lang}" dir="{dir}">
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
  <link rel="stylesheet" href="/assets/styles.css">
  <script type="application/ld+json">{ld}</script>
  {about_js}{analytics}
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
    {secs}

    <section class="cta">
      <h2>{cta}</h2>
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
        lang=lang, dir=L[lang]["dir"], title=a["title"], desc=a["desc"], canon=canon, alts=alts,
        brand=BRAND, oglocale=OG_LOCALE[lang], favicon=FAVICON,
        ld=json.dumps(ld, ensure_ascii=False), about_js=ABOUT_JS, analytics=analytics_tag(),
        home=path_for(lang), logo_svg=LOGO_SVG, opts=opts, theme_svg=THEME_SVG,
        h1=a["h1"], secs=secs, cta=CTA[lang], apple=APPLE, google=GOOGLE,
        apple_svg=APPLE_SVG, google_svg=GOOGLE_SVG, langlinks=langlinks, footlinks=foot_links(lang))

# ── write pages ──
count = 0
for lang, seg in SEG.items():
    d = os.path.join(OUT, seg) if seg else OUT
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(lang))
    count += 1
    print("yazildi:", (seg or ".") + "/index.html")
    for sp in SPORTS:
        sd = os.path.join(d, SPORT_SLUG[lang][sp])
        os.makedirs(sd, exist_ok=True)
        with open(os.path.join(sd, "index.html"), "w", encoding="utf-8") as f:
            f.write(page(lang, sp))
        count += 1
        print("yazildi:", path_for(lang, sp) + "index.html")
    for comp in COMP_PAGES.get(lang, {}):
        cd = os.path.join(d, COMP_PAGES[lang][comp]["slug"])
        os.makedirs(cd, exist_ok=True)
        with open(os.path.join(cd, "index.html"), "w", encoding="utf-8") as f:
            f.write(page(lang, comp=comp))
        count += 1
        print("yazildi:", comp_path(lang, comp) + "index.html")
    ad = os.path.join(d, ABOUT_SLUG[lang])
    os.makedirs(ad, exist_ok=True)
    with open(os.path.join(ad, "index.html"), "w", encoding="utf-8") as f:
        f.write(about_page(lang))
    count += 1
    print("yazildi:", about_path(lang) + "index.html")

# sitemap + robots + nojekyll + 404
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for sp in [None] + SPORTS:
    for lang in SEG:
        sm.append("  <url><loc>%s</loc>" % url_for(lang, sp))
        for alt in SEG:
            sm.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (alt, url_for(alt, sp)))
        sm.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>' % url_for("en", sp))
        sm.append("  </url>")
for lang in SEG:
    sm.append("  <url><loc>%s</loc>" % (BASE + about_path(lang)))
    for alt in SEG:
        sm.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (alt, BASE + about_path(alt)))
    sm.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>' % (BASE + about_path("en")))
    sm.append("  </url>")
for lang in COMP_PAGES:
    for comp in COMP_PAGES[lang]:
        sm.append("  <url><loc>%s</loc>" % (BASE + comp_path(lang, comp)))
        for alt in COMP_PAGES:
            if comp in COMP_PAGES[alt]:
                sm.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (alt, BASE + comp_path(alt, comp)))
        sm.append("  </url>")
sm.append("</urlset>")
open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm))
open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(
    "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % BASE)
open(os.path.join(OUT, ".nojekyll"), "w").write("")
# language-detecting 404 -> redirect to best language root
open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(
    "<!doctype html><meta charset='utf-8'><script>"
    "var s=" + json.dumps(list(SEG.keys())) + ",l=(navigator.language||'en').slice(0,2);"
    "location.replace('%s/'+(s.indexOf(l)>0?l+'/':''));</script>" % BASE)
print("sitemap.xml, robots.txt, .nojekyll, 404.html yazildi")
print("BITTI —", len(SEG), "dil,", len(SPORTS), "spor,", count, "sayfa")
