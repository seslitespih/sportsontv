# -*- coding: utf-8 -*-
"""Generate the multilingual Sports-on-TV site: one static, SEO-tuned page per
language (localized <title>/description/H1/FAQ + hreflang alternates + JSON-LD),
plus sitemap.xml and robots.txt. The live match list is filled client-side by
assets/app.js from the same daily fixtures the mobile app uses."""
import os, io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ⚠️ GEÇİCİ: normalde https olmalı. GitHub Pages sertifikası 11 Ağu'dan beri
# "new" durumunda takılı (DNS doğru, CAA engeli yok, alan adı iki kez kaldırılıp
# eklendi) ve https hiç çalışmıyor. Canonical/sitemap https gösterdiği sürece
# Google hiçbir sayfayı çekemiyordu — site "hiç taranmamış" durumdaydı.
# SERTİFİKA GELİNCE: burayı https yap, derle, push'la, GitHub Pages'te
# https_enforced'ı aç, sitemap'i Search Console'a yeniden gönder.
BASE = "http://sportstvtoday.com"
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

def page(lang, sport=None):
    d = dict(L[lang])
    if sport:
        t, desc, h1, prose = SPORT_COPY[lang][sport]
        d.update(title=t, desc=desc, h1=h1, prose=prose,
                 proseT=SPORT_LABEL[lang][sport] + " — " + L[lang]["today"])
    feats = "\n".join(
        '<div class="feat"><div class="ic">%s</div><h3>%s</h3><p>%s</p></div>' % (FEAT_ICONS[idx], h, p)
        for idx, (i, h, p) in enumerate(d["feats"]))
    # SSS yalnız ana sayfada. Aynı SSS işaretlemesini 40 sayfaya kopyalamak
    # Google'ın "yinelenen içerik" saydığı şeydir; spor sayfaları bunun yerine
    # breadcrumb işaretlemesi alır.
    if sport:
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
    canon = url_for(lang, sport)
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
  <script type="application/ld+json">{faq_ld}</script>{analytics}
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
    <div class="section-head">
      <span class="tzchip" id="tzchip"></span>
      <span class="spacer"></span>
      <span class="tzchip" id="updated"></span>
    </div>
    <div class="tzchip" id="countryLbl" style="margin-bottom:6px;display:inline-block"></div>
    <nav class="sportnav">
      {sportlinks}
    </nav>
    <div class="filters" id="filters"></div>
    <div class="matchlist" id="matchlist"></div>

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
      <div>© {brand}</div>
    </div>
    <p style="margin:12px 0 0">{foot}</p>
  </div></footer>
  <script>window.__SPORT__={sportjs};</script>
  <script src="/assets/app.js"></script>
</body>
</html>""".format(
        lang=lang, dir=d["dir"], title=d["title"], desc=d["desc"], canon=canon,
        hreflangs=hreflangs(lang, sport), brand=BRAND, oglocale=OG_LOCALE[lang],
        base=BASE, selfurl=path_for(lang), langopts=lang_options(lang, sport),
        h1=d["h1"], sub=d["sub"], apple=APPLE, google=GOOGLE, store=d["store"], cta=CTA[lang],
        today=d["today"], feats=feats, proseT=d["proseT"], prose=d["prose"],
        faq_section=faq_section, langlinks=lang_links(lang, sport), foot=d["foot"],
        sportlinks=sport_links(lang, sport), sportjs=json.dumps(sport),
        apple_svg=APPLE_SVG, google_svg=GOOGLE_SVG, favicon=FAVICON,
        logo_svg=LOGO_SVG, theme_svg=THEME_SVG,
        # Dil yönlendirmesi yalnız kök sayfada; spor sayfasında olursa
        # ziyaretçiyi konudan koparıp ana sayfaya atar.
        root_redirect=(ROOT_REDIRECT if (lang == "en" and not sport) else ""), analytics=analytics_tag(),
        site_ld=json.dumps(site_ld, ensure_ascii=False), faq_ld=json.dumps(extra_ld, ensure_ascii=False))

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
