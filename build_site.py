# -*- coding: utf-8 -*-
"""Generate the multilingual Sports-on-TV site: one static, SEO-tuned page per
language (localized <title>/description/H1/FAQ + hreflang alternates + JSON-LD),
plus sitemap.xml and robots.txt. The live match list is filled client-side by
assets/app.js from the same daily fixtures the mobile app uses."""
import os, io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "https://sportstvtoday.com"
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

def url_for(lang):
    s = SEG[lang]
    return BASE + "/" + (s + "/" if s else "")

def path_for(lang):
    # root-relative nav path — works over http and https, any host
    s = SEG[lang]
    return "/" + (s + "/" if s else "")

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

def hreflangs(current):
    out = []
    for lang in SEG:
        out.append('<link rel="alternate" hreflang="%s" href="%s">' % (lang, url_for(lang)))
    out.append('<link rel="alternate" hreflang="x-default" href="%s">' % url_for("en"))
    return "\n  ".join(out)

def lang_options(current):
    opts = []
    for lang in SEG:
        sel = " selected" if lang == current else ""
        opts.append('<option value="%s" data-lang="%s"%s>%s</option>' % (path_for(lang), lang, sel, LANG_NATIVE[lang]))
    return "".join(opts)

def lang_links(current):
    out = []
    for lang in SEG:
        cur = ' aria-current="true"' if lang == current else ""
        out.append('<a href="%s"%s>%s</a>' % (path_for(lang), cur, LANG_NATIVE[lang]))
    return "\n      ".join(out)

def page(lang):
    d = L[lang]
    feats = "\n".join(
        '<div class="feat"><div class="ic">%s</div><h3>%s</h3><p>%s</p></div>' % (FEAT_ICONS[idx], h, p)
        for idx, (i, h, p) in enumerate(d["feats"]))
    faqs = "\n".join(
        '<details><summary>%s</summary><p>%s</p></details>' % (q, a) for (q, a) in d["faqs"])
    faq_ld = {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for (q,a) in d["faqs"]]}
    site_ld = {"@context":"https://schema.org","@graph":[
        {"@type":"WebSite","name":BRAND,"url":url_for(lang),"inLanguage":lang},
        {"@type":"SoftwareApplication","name":BRAND,"operatingSystem":"iOS, Android",
         "applicationCategory":"SportsApplication","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},
         "url":url_for(lang)}]}
    canon = url_for(lang)
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
    <div class="filters" id="filters"></div>
    <div class="matchlist" id="matchlist"></div>

    <section class="features">{feats}</section>

    <section class="prose"><h2>{proseT}</h2><p>{prose}</p></section>

    <section class="faq"><h2>{faqT}</h2>{faqs}</section>

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
  <script src="/assets/app.js"></script>
</body>
</html>""".format(
        lang=lang, dir=d["dir"], title=d["title"], desc=d["desc"], canon=canon,
        hreflangs=hreflangs(lang), brand=BRAND, oglocale=OG_LOCALE[lang],
        base=BASE, selfurl=path_for(lang), langopts=lang_options(lang),
        h1=d["h1"], sub=d["sub"], apple=APPLE, google=GOOGLE, store=d["store"], cta=CTA[lang],
        today=d["today"], feats=feats, proseT=d["proseT"], prose=d["prose"],
        faqT=d["faqT"], faqs=faqs, langlinks=lang_links(lang), foot=d["foot"],
        apple_svg=APPLE_SVG, google_svg=GOOGLE_SVG, favicon=FAVICON,
        logo_svg=LOGO_SVG, theme_svg=THEME_SVG,
        root_redirect=(ROOT_REDIRECT if lang == "en" else ""), analytics=analytics_tag(),
        site_ld=json.dumps(site_ld, ensure_ascii=False), faq_ld=json.dumps(faq_ld, ensure_ascii=False))

# ── write pages ──
for lang, seg in SEG.items():
    d = os.path.join(OUT, seg) if seg else OUT
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(lang))
    print("yazildi:", (seg or ".") + "/index.html")

# sitemap + robots + nojekyll + 404
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for lang in SEG:
    sm.append("  <url><loc>%s</loc>" % url_for(lang))
    for alt in SEG:
        sm.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (alt, url_for(alt)))
    sm.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>' % url_for("en"))
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
print("BITTI —", len(SEG), "dil")
