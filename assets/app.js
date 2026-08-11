/* Sports on TV — runtime. Reads the live daily fixtures the app itself uses,
   converts each kickoff to the visitor's own time zone, and shows the channel
   for the visitor's country. Language comes from <html lang>. */
(function () {
  "use strict";
  var DATA_URL = "https://raw.githubusercontent.com/seslitespih/mac-hatirlatici/main/assets/matches-daily.json";
  var LANG = (document.documentElement.lang || "en").slice(0, 2);

  // Broadcast countries the app curates (ISO 3166-1 alpha-2).
  var COUNTRIES = ["TR","GB","US","DE","ES","FR","IT","PT","NL","BE","CH","AT","BR",
    "AR","MX","CO","CL","PE","CA","SA","QA","AE","EG","MA","DZ","TN","JP","KR","AU",
    "NG","SN","ZA","GH","IN","ID"];
  var LANG_COUNTRY = { tr:"TR", en:"GB", de:"DE", es:"ES", fr:"FR", it:"IT", pt:"PT", ar:"SA" };

  var RT = {
    en:{live:"Live",none:"No broadcast listed",loading:"Loading today's matches…",err:"Couldn't load matches. Please try again.",empty:"No matches scheduled today. Check back soon.",all:"All",football:"Football",basketball:"Basketball",volleyball:"Volleyball",motorsport:"Motorsport",tz:"Your time zone",country:"Channels for",vs:"vs",retry:"Retry",updated:"Updated"},
    tr:{live:"Canlı",none:"Yayın bilgisi yok",loading:"Bugünün maçları yükleniyor…",err:"Maçlar yüklenemedi. Lütfen tekrar deneyin.",empty:"Bugün planlanmış maç yok. Yakında tekrar bak.",all:"Tümü",football:"Futbol",basketball:"Basketbol",volleyball:"Voleybol",motorsport:"Motor Sporları",tz:"Saat diliminiz",country:"Kanallar",vs:"-",retry:"Tekrar dene",updated:"Güncellendi"},
    de:{live:"Live",none:"Kein Sender gelistet",loading:"Heutige Spiele werden geladen…",err:"Spiele konnten nicht geladen werden. Bitte erneut versuchen.",empty:"Heute keine Spiele geplant. Schau bald wieder vorbei.",all:"Alle",football:"Fußball",basketball:"Basketball",volleyball:"Volleyball",motorsport:"Motorsport",tz:"Deine Zeitzone",country:"Sender für",vs:"–",retry:"Erneut",updated:"Aktualisiert"},
    es:{live:"En vivo",none:"Sin emisión confirmada",loading:"Cargando los partidos de hoy…",err:"No se pudieron cargar los partidos. Inténtalo de nuevo.",empty:"No hay partidos hoy. Vuelve pronto.",all:"Todos",football:"Fútbol",basketball:"Baloncesto",volleyball:"Voleibol",motorsport:"Motor",tz:"Tu zona horaria",country:"Canales para",vs:"vs",retry:"Reintentar",updated:"Actualizado"},
    fr:{live:"En direct",none:"Aucune diffusion indiquée",loading:"Chargement des matchs du jour…",err:"Impossible de charger les matchs. Réessayez.",empty:"Aucun match aujourd'hui. Revenez bientôt.",all:"Tous",football:"Football",basketball:"Basket",volleyball:"Volley",motorsport:"Sport auto",tz:"Votre fuseau horaire",country:"Chaînes pour",vs:"vs",retry:"Réessayer",updated:"Mis à jour"},
    it:{live:"Diretta",none:"Nessuna diretta indicata",loading:"Caricamento delle partite di oggi…",err:"Impossibile caricare le partite. Riprova.",empty:"Nessuna partita oggi. Torna presto.",all:"Tutti",football:"Calcio",basketball:"Basket",volleyball:"Pallavolo",motorsport:"Motori",tz:"Il tuo fuso orario",country:"Canali per",vs:"vs",retry:"Riprova",updated:"Aggiornato"},
    pt:{live:"Ao vivo",none:"Sem transmissão indicada",loading:"Carregando os jogos de hoje…",err:"Não foi possível carregar os jogos. Tente novamente.",empty:"Nenhum jogo hoje. Volte em breve.",all:"Todos",football:"Futebol",basketball:"Basquete",volleyball:"Vôlei",motorsport:"Automobilismo",tz:"Seu fuso horário",country:"Canais para",vs:"vs",retry:"Tentar de novo",updated:"Atualizado"},
    ar:{live:"مباشر",none:"لا يوجد بث مؤكد",loading:"جارٍ تحميل مباريات اليوم…",err:"تعذّر تحميل المباريات. حاول مرة أخرى.",empty:"لا توجد مباريات اليوم. عد قريبًا.",all:"الكل",football:"كرة القدم",basketball:"كرة السلة",volleyball:"الكرة الطائرة",motorsport:"رياضة السيارات",tz:"منطقتك الزمنية",country:"القنوات في",vs:"-",retry:"أعد المحاولة",updated:"تم التحديث"}
  };
  var t = RT[LANG] || RT.en;
  var SPORT_ICON = { football:"⚽", basketball:"🏀", volleyball:"🏐", motorsport:"🏎️" };

  function flag(cc){ return cc.replace(/./g, function(c){ return String.fromCodePoint(127397 + c.charCodeAt(0)); }); }
  function regionName(cc){
    try { return new Intl.DisplayNames([LANG], { type:"region" }).of(cc) || cc; } catch(e){ return cc; }
  }
  function $(s, r){ return (r||document).querySelector(s); }

  var state = { matches:[], filter:"all", country:null, tz:null };

  // ── country selection (persist) ──────────────────────────
  function detectCountry(){
    var saved = localStorage.getItem("sot_country");
    if (saved && COUNTRIES.indexOf(saved) >= 0) return saved;
    try {
      var loc = (Intl.DateTimeFormat().resolvedOptions().locale || navigator.language || "");
      var m = loc.toUpperCase().match(/[-_]([A-Z]{2})\b/);
      if (m && COUNTRIES.indexOf(m[1]) >= 0) return m[1];
    } catch(e){}
    return LANG_COUNTRY[LANG] || "GB";
  }

  function buildCountrySelect(){
    var sel = $("#countrySel"); if (!sel) return;
    var list = COUNTRIES.map(function(cc){ return { cc:cc, name:regionName(cc) }; })
      .sort(function(a,b){ return a.name.localeCompare(b.name, LANG); });
    sel.innerHTML = list.map(function(o){
      return '<option value="'+o.cc+'"'+(o.cc===state.country?" selected":"")+'>'+flag(o.cc)+" "+o.name+"</option>";
    }).join("");
    sel.addEventListener("change", function(){
      state.country = sel.value; localStorage.setItem("sot_country", sel.value);
      var lbl = $("#countryLbl"); if (lbl) lbl.textContent = t.country + " " + regionName(state.country);
      render();
    });
    var lbl = $("#countryLbl"); if (lbl) lbl.textContent = t.country + " " + regionName(state.country);
  }

  // ── data ─────────────────────────────────────────────────
  function fetchData(){
    var url = DATA_URL + "?t=" + Math.floor(Date.now() / 300000);
    return fetch(url, { cache:"no-store" }).then(function(r){
      if (!r.ok) throw new Error("http " + r.status); return r.json();
    });
  }

  function pick(names, fallback){
    if (names && typeof names === "object"){ if (names[LANG]) return names[LANG]; if (names.en) return names.en; }
    return fallback;
  }

  function statusOf(m){
    var k = new Date(m.kickoffUtc).getTime(); var now = Date.now();
    if (m.status === "finished") return "finished";
    if (m.status === "live") return "live";
    if (now >= k && now < k + 130*60000) return "live";
    if (now >= k + 130*60000) return "finished";
    return "scheduled";
  }

  // ── render ───────────────────────────────────────────────
  var fmtTime = new Intl.DateTimeFormat(LANG, { hour:"2-digit", minute:"2-digit" });
  var fmtDay  = new Intl.DateTimeFormat(LANG, { weekday:"short" });

  function matchCard(m){
    var d = new Date(m.kickoffUtc);
    var teams;
    var home = pick(m.homeNames, m.home), away = pick(m.awayNames, m.away);
    teams = '<span>'+esc(home)+'</span><span class="vs">'+t.vs+'</span><span>'+esc(away)+'</span>';
    var comp = esc(pick(m.competition, m.competitionId || ""));
    var icon = SPORT_ICON[m.sport] || "🏆";
    var st = statusOf(m);
    var chans = (m.broadcasts && m.broadcasts[state.country]) || null;
    var right = st === "live"
      ? '<span class="live"><span class="dot"></span>'+t.live+'</span>'
      : '<div class="time"><div class="hm">'+fmtTime.format(d)+'</div><div class="day">'+fmtDay.format(d)+'</div></div>';
    // time also on the left column always:
    var left = '<div class="time"><div class="hm">'+fmtTime.format(d)+'</div><div class="day">'+fmtDay.format(d)+'</div></div>';
    var chanHtml = chans && chans.length
      ? '<span class="chan"><span class="tv">📺</span>'+esc(chans.join(" · "))+'</span>'
      : '<span class="chan none">'+t.none+'</span>';
    var liveTag = st === "live" ? '<span class="live"><span class="dot"></span>'+t.live+'</span>' : '';
    return '<article class="card">'
      + left
      + '<div class="mid"><div class="teams">'+teams+'</div>'
      + '<div class="comp"><span class="sporticon">'+icon+'</span>'+comp+'</div></div>'
      + '<div class="right">'+liveTag+chanHtml+'</div>'
      + '</article>';
  }

  function esc(s){ return String(s==null?"":s).replace(/[&<>"]/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }

  function render(){
    var box = $("#matchlist"); if (!box) return;
    var list = state.matches.slice();
    if (state.filter !== "all") list = list.filter(function(m){ return m.sport === state.filter; });
    list.sort(function(a,b){ return new Date(a.kickoffUtc)-new Date(b.kickoffUtc); });
    if (!list.length){ box.innerHTML = '<div class="state"><div class="big">📅</div>'+t.empty+'</div>'; return; }
    box.innerHTML = list.map(matchCard).join("");
  }

  function buildFilters(){
    var wrap = $("#filters"); if (!wrap) return;
    var sports = {}; state.matches.forEach(function(m){ sports[m.sport]=1; });
    var order = ["football","basketball","volleyball","motorsport"];
    var opts = [["all",t.all,"🏆"]];
    order.forEach(function(s){ if (sports[s]) opts.push([s, t[s], SPORT_ICON[s]]); });
    if (opts.length <= 2){ wrap.innerHTML=""; return; }
    wrap.innerHTML = opts.map(function(o){
      return '<button class="chip" data-f="'+o[0]+'" aria-pressed="'+(o[0]===state.filter)+'">'+o[2]+" "+esc(o[1])+"</button>";
    }).join("");
    wrap.querySelectorAll(".chip").forEach(function(b){
      b.addEventListener("click", function(){
        state.filter = b.getAttribute("data-f");
        wrap.querySelectorAll(".chip").forEach(function(x){ x.setAttribute("aria-pressed", x===b); });
        render();
      });
    });
  }

  function injectJsonLd(payload){
    try {
      var items = state.matches.slice(0, 30).map(function(m){
        var home = pick(m.homeNames, m.home), away = pick(m.awayNames, m.away);
        var o = {
          "@type":"SportsEvent",
          "name": home + " " + t.vs + " " + away,
          "startDate": m.kickoffUtc,
          "eventStatus":"https://schema.org/EventScheduled",
          "eventAttendanceMode":"https://schema.org/OnlineEventAttendanceMode",
          "sport": m.sport,
          "competitor":[{"@type":"SportsTeam","name":home},{"@type":"SportsTeam","name":away}],
          "location":{"@type":"VirtualLocation","url":location.href}
        };
        var chans = m.broadcasts && m.broadcasts[state.country];
        if (chans && chans.length) o.broadcastOfEvent = undefined, o.publisher = chans.map(function(c){ return {"@type":"Organization","name":c}; });
        return o;
      });
      var ld = { "@context":"https://schema.org", "@graph": items };
      var s = document.createElement("script"); s.type="application/ld+json"; s.id="ld-events";
      s.textContent = JSON.stringify(ld); document.head.appendChild(s);
    } catch(e){}
  }

  function showUpdated(payload){
    var el = $("#updated"); if (!el || !payload.date) return;
    try {
      var d = new Date(payload.generated_at || payload.date);
      el.textContent = t.updated + ": " + new Intl.DateTimeFormat(LANG,{dateStyle:"medium"}).format(d);
    } catch(e){}
  }

  function boot(){
    state.country = detectCountry();
    state.tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
    var tzEl = $("#tzchip"); if (tzEl) tzEl.textContent = "🕒 " + (state.tz || t.tz);
    buildCountrySelect();
    var box = $("#matchlist");
    if (box) box.innerHTML = '<div class="state"><div class="spinner"></div>'+t.loading+'</div>';

    fetchData().then(function(payload){
      state.matches = Array.isArray(payload.matches) ? payload.matches : [];
      buildFilters(); render(); showUpdated(payload); injectJsonLd(payload);
    }).catch(function(){
      if (box) box.innerHTML = '<div class="state"><div class="big">⚠️</div>'+t.err
        +'<div style="margin-top:14px"><button class="chip" id="retry">'+t.retry+'</button></div></div>';
      var r = $("#retry"); if (r) r.addEventListener("click", boot);
    });
  }

  // theme toggle (optional, remembers)
  function initTheme(){
    var btn = $("#themeBtn"); if (!btn) return;
    var saved = localStorage.getItem("sot_theme");
    if (saved) document.documentElement.setAttribute("data-theme", saved);
    btn.addEventListener("click", function(){
      var cur = document.documentElement.getAttribute("data-theme");
      var next = cur === "dark" ? "light" : (cur === "light" ? "dark" : (matchMedia("(prefers-color-scheme: dark)").matches ? "light" : "dark"));
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("sot_theme", next);
    });
  }

  if (document.readyState !== "loading") { initTheme(); boot(); }
  else document.addEventListener("DOMContentLoaded", function(){ initTheme(); boot(); });
})();
