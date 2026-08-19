/* Sports on TV — runtime. Reads the same live daily fixtures the mobile app
   uses, converts each kickoff to the visitor's own time zone, shows the channel
   for their country, and lets them set a real calendar reminder (no backend). */
(function () {
  "use strict";
  var DATA_URL = "https://raw.githubusercontent.com/seslitespih/mac-hatirlatici/main/assets/matches-daily.json";
  var LANG = (document.documentElement.lang || "en").slice(0, 2);

  // Desteklenen pazarlar (curated veri bu ülkeler için var)
  var COUNTRIES = ["TR","US","GB","DE","ES","FR","IT","PT","BR","AR","MX","CO","CL","UY","PY","GT","CA","SA","DZ","IQ","JO","EG","OM"];
  var LANG_COUNTRY = { tr:"TR", en:"GB", de:"DE", es:"ES", fr:"FR", it:"IT", pt:"PT", ar:"SA" };
  // ABD/Kanada/Brezilya/Meksika birden çok saat dilimine yayılır. Ziyaretçinin
  // cihazı o ülkenin dilimlerinden birindeyse ONU kullanırız (Kaliforniyalı
  // Pasifik saatini görür), değilse aşağıdaki varsayılana düşeriz.
  var COUNTRY_ZONES = {
    US:["America/New_York","America/Detroit","America/Chicago","America/Denver","America/Phoenix",
        "America/Los_Angeles","America/Anchorage","Pacific/Honolulu","America/Boise",
        "America/Indiana/Indianapolis","America/Kentucky/Louisville"],
    CA:["America/Toronto","America/Winnipeg","America/Edmonton","America/Vancouver",
        "America/Halifax","America/St_Johns","America/Regina"],
    BR:["America/Sao_Paulo","America/Manaus","America/Fortaleza","America/Recife",
        "America/Bahia","America/Belem","America/Cuiaba","America/Porto_Velho"],
    MX:["America/Mexico_City","America/Tijuana","America/Monterrey","America/Chihuahua",
        "America/Hermosillo","America/Cancun","America/Mazatlan"]
  };
  function tzFor(cc){
    var varsayilan = COUNTRY_TZ[cc];
    var liste = COUNTRY_ZONES[cc];
    if (!liste) return varsayilan;
    try {
      var cihaz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if (cihaz && liste.indexOf(cihaz) >= 0) return cihaz;
    } catch (e) {}
    return varsayilan;
  }

  // Saatler seçilen ÜLKENİN saat diliminde gösterilir — cihazınkinde değil.
  // Ülke değiştirince yalnız kanal değil saat de değişmeli.
  var COUNTRY_TZ = {
    TR:"Europe/Istanbul", US:"America/New_York", GB:"Europe/London", DE:"Europe/Berlin",
    ES:"Europe/Madrid", FR:"Europe/Paris", IT:"Europe/Rome", PT:"Europe/Lisbon",
    BR:"America/Sao_Paulo", AR:"America/Argentina/Buenos_Aires", MX:"America/Mexico_City",
    CO:"America/Bogota", CL:"America/Santiago", UY:"America/Montevideo", PY:"America/Asuncion",
    GT:"America/Guatemala", CA:"America/Toronto", SA:"Asia/Riyadh", DZ:"Africa/Algiers",
    // Gerçek indirme gelen Arap pazarları — Irak, Ürdün, Mısır, Umman
    IQ:"Asia/Baghdad", JO:"Asia/Amman", EG:"Africa/Cairo", OM:"Asia/Muscat"
  };
  var SPORT_COLOR = { football:"#12a15f", basketball:"#e08a1e", volleyball:"#2f6bd6", motorsport:"#d23b4e" };

  var RT = {
    en:{live:"Live",none:"No broadcast listed",loading:"Loading today's matches…",err:"Couldn't load matches. Please try again.",empty:"No matches scheduled today. Check back soon.",all:"All",football:"Football",basketball:"Basketball",volleyball:"Volleyball",motorsport:"Motorsport",tz:"Your time zone",country:"Channels for",vs:"vs",retry:"Retry",updated:"Updated",remind:"Remind me",gcal:"Google Calendar",ics:"Apple / Outlook (.ics)"},
    tr:{live:"Canlı",none:"Yayın bilgisi yok",loading:"Bugünün maçları yükleniyor…",err:"Maçlar yüklenemedi. Lütfen tekrar deneyin.",empty:"Bugün planlanmış maç yok. Yakında tekrar bak.",all:"Tümü",football:"Futbol",basketball:"Basketbol",volleyball:"Voleybol",motorsport:"Motor Sporları",tz:"Saat diliminiz",country:"Kanallar",vs:"-",retry:"Tekrar dene",updated:"Güncellendi",remind:"Hatırlat",gcal:"Google Takvim",ics:"Apple / Outlook (.ics)"},
    de:{live:"Live",none:"Kein Sender gelistet",loading:"Heutige Spiele werden geladen…",err:"Spiele konnten nicht geladen werden. Bitte erneut versuchen.",empty:"Heute keine Spiele geplant. Schau bald wieder vorbei.",all:"Alle",football:"Fußball",basketball:"Basketball",volleyball:"Volleyball",motorsport:"Motorsport",tz:"Deine Zeitzone",country:"Sender für",vs:"–",retry:"Erneut",updated:"Aktualisiert",remind:"Erinnern",gcal:"Google Kalender",ics:"Apple / Outlook (.ics)"},
    es:{live:"En vivo",none:"Sin emisión confirmada",loading:"Cargando los partidos de hoy…",err:"No se pudieron cargar los partidos. Inténtalo de nuevo.",empty:"No hay partidos hoy. Vuelve pronto.",all:"Todos",football:"Fútbol",basketball:"Baloncesto",volleyball:"Voleibol",motorsport:"Motor",tz:"Tu zona horaria",country:"Canales para",vs:"vs",retry:"Reintentar",updated:"Actualizado",remind:"Recordar",gcal:"Google Calendar",ics:"Apple / Outlook (.ics)"},
    fr:{live:"En direct",none:"Aucune diffusion indiquée",loading:"Chargement des matchs du jour…",err:"Impossible de charger les matchs. Réessayez.",empty:"Aucun match aujourd'hui. Revenez bientôt.",all:"Tous",football:"Football",basketball:"Basket",volleyball:"Volley",motorsport:"Sport auto",tz:"Votre fuseau horaire",country:"Chaînes pour",vs:"vs",retry:"Réessayer",updated:"Mis à jour",remind:"Me rappeler",gcal:"Google Agenda",ics:"Apple / Outlook (.ics)"},
    it:{live:"Diretta",none:"Nessuna diretta indicata",loading:"Caricamento delle partite di oggi…",err:"Impossibile caricare le partite. Riprova.",empty:"Nessuna partita oggi. Torna presto.",all:"Tutti",football:"Calcio",basketball:"Basket",volleyball:"Pallavolo",motorsport:"Motori",tz:"Il tuo fuso orario",country:"Canali per",vs:"vs",retry:"Riprova",updated:"Aggiornato",remind:"Ricordami",gcal:"Google Calendar",ics:"Apple / Outlook (.ics)"},
    pt:{live:"Ao vivo",none:"Sem transmissão indicada",loading:"Carregando os jogos de hoje…",err:"Não foi possível carregar os jogos. Tente novamente.",empty:"Nenhum jogo hoje. Volte em breve.",all:"Todos",football:"Futebol",basketball:"Basquete",volleyball:"Vôlei",motorsport:"Automobilismo",tz:"Seu fuso horário",country:"Canais para",vs:"vs",retry:"Tentar de novo",updated:"Atualizado",remind:"Lembrar",gcal:"Google Agenda",ics:"Apple / Outlook (.ics)"},
    ar:{live:"مباشر",none:"لا يوجد بث مؤكد",loading:"جارٍ تحميل مباريات اليوم…",err:"تعذّر تحميل المباريات. حاول مرة أخرى.",empty:"لا توجد مباريات اليوم. عد قريبًا.",all:"الكل",football:"كرة القدم",basketball:"كرة السلة",volleyball:"الكرة الطائرة",motorsport:"رياضة السيارات",tz:"منطقتك الزمنية",country:"القنوات في",vs:"-",retry:"أعد المحاولة",updated:"تم التحديث",remind:"ذكّرني",gcal:"تقويم Google",ics:"Apple / Outlook (.ics)"}
  };
  var t = RT[LANG] || RT.en;

  // Remember an explicit language choice so the root page stops auto-redirecting.
  window.sotSetLang = function (sel) {
    try {
      var opt = sel.options[sel.selectedIndex];
      localStorage.setItem("sot_lang", opt.getAttribute("data-lang") || "en");
    } catch (e) {}
    location.href = sel.value;
  };

  var IC = {
    tv:'<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="7" width="19" height="13" rx="2.2"/><path d="M8 3.5l4 3.5 4-3.5"/></svg>',
    clock:'<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3.2 1.9"/></svg>',
    bell:'<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9.5a6 6 0 0 1 12 0c0 4.5 1.8 5.5 2 6H4c.2-.5 2-1.5 2-6z"/><path d="M10.2 20a2 2 0 0 0 3.6 0"/></svg>'
  };

  function flag(cc){ return cc.replace(/./g, function(c){ return String.fromCodePoint(127397 + c.charCodeAt(0)); }); }
  function regionName(cc){ try { return new Intl.DisplayNames([LANG], { type:"region" }).of(cc) || cc; } catch(e){ return cc; } }
  function $(s, r){ return (r||document).querySelector(s); }
  function esc(s){ return String(s==null?"":s).replace(/[&<>"]/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }

  // Spor sayfaları (/tr/futbol/ gibi) filtreyi window.__SPORT__ ile önceden
  // seçtirir; ana sayfada bu değer null olduğu için "all" kalır.
  var state = { matches:[], view:[], filter:(window.__SPORT__ || "all"), country:null, tz:null };

  function detectCountry(){
    // 1) Açık seçim. 2) Tarayıcı bölgesi (yalnız desteklenen pazarlar → en-US=US,
    //    pt-BR=BR; desteklenmeyen ör. it-CH elenir). 3) Sayfa dilinin ülkesi.
    var saved = localStorage.getItem("sot_country");
    if (saved && COUNTRIES.indexOf(saved) >= 0) return saved;
    try {
      var loc = (Intl.DateTimeFormat().resolvedOptions().locale || navigator.language || "");
      var mm = loc.toUpperCase().match(/[-_]([A-Z]{2})\b/);
      if (mm && COUNTRIES.indexOf(mm[1]) >= 0) return mm[1];
    } catch (e) {}
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
      buildFormatters();   // saat de ülkeye göre değişsin
      state.tz = tzFor(state.country) || state.tz;
      var tzEl = $("#tzchip"); if (tzEl) tzEl.innerHTML = IC.clock + '<span>' + state.tz + '</span>';
      updateCountryLabel(); render();
    });
    updateCountryLabel();
  }
  function updateCountryLabel(){
    var lbl = $("#countryLbl"); if (lbl) lbl.textContent = t.country + " " + regionName(state.country);
  }

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
    var k = new Date(m.kickoffUtc).getTime(), now = Date.now();
    if (m.status === "finished") return "finished";
    if (m.status === "live") return "live";
    if (now >= k && now < k + 130*60000) return "live";
    if (now >= k + 130*60000) return "finished";
    return "scheduled";
  }

  // 24-hour clock everywhere (19:00, no AM/PM) — matches TR/EU convention.
  // Seçilen ülkenin saat dilimine göre kurulur; ülke değişince yeniden kurulur.
  var fmtTime, fmtDay;
  function buildFormatters(){
    var tz = tzFor(state.country) || undefined;
    var o = { hour:"2-digit", minute:"2-digit", hourCycle:"h23" };
    var d = { weekday:"short" };
    if (tz){ o.timeZone = tz; d.timeZone = tz; }
    fmtTime = new Intl.DateTimeFormat(LANG, o);
    fmtDay  = new Intl.DateTimeFormat(LANG, d);
  }
  buildFormatters();

  function names(m){ return { home:pick(m.homeNames, m.home), away:pick(m.awayNames, m.away) }; }

  // Yalnızca ziyaretçinin ülkesinin kanalını gösterir (dil→ülke; TR sayfası → Türkiye).
  function matchCard(m, idx){
    var d = new Date(m.kickoffUtc), n = names(m);
    var comp = esc(pick(m.competition, m.competitionId || ""));
    var color = SPORT_COLOR[m.sport] || "#8892a6";
    var st = statusOf(m);
    var chans = (m.broadcasts && m.broadcasts[state.country]) || null;
    var left = '<div class="time"><div class="hm">'+fmtTime.format(d)+'</div><div class="day">'+fmtDay.format(d)+'</div></div>';
    var teams = '<span>'+esc(n.home)+'</span><span class="vs">'+t.vs+'</span><span>'+esc(n.away)+'</span>';
    var chanHtml = chans && chans.length
      ? '<span class="chan"><span class="cic">'+IC.tv+'</span>'+esc(chans.join(" · "))+'</span>'
      : '<span class="chan none">'+t.none+'</span>';
    var liveTag = st === "live" ? '<span class="live"><span class="dot"></span>'+t.live+'</span>' : '';
    var remind = st === "finished" ? '' :
      '<div class="remind"><button class="rbtn" data-idx="'+idx+'" type="button">'+IC.bell+'<span>'+t.remind+'</span></button>'
      + '<div class="rmenu" hidden><a class="ritem gcal" target="_blank" rel="noopener">'+t.gcal+'</a>'
      + '<a class="ritem ics">'+t.ics+'</a></div></div>';
    return '<article class="card">'+left
      + '<div class="mid"><div class="teams">'+teams+'</div>'
      + '<div class="comp"><span class="sdot" style="background:'+color+'"></span>'+comp+'</div></div>'
      + '<div class="right">'+liveTag+chanHtml+remind+'</div></article>';
  }

  // ── calendar reminder (no backend) ───────────────────────
  function icsStamp(d){ return new Date(d).toISOString().replace(/[-:]/g,"").replace(/\.\d{3}/,""); }
  function icsEsc(s){ return String(s).replace(/([,;\\])/g,"\\$1").replace(/\n/g," "); }
  function eventOf(m){
    var n = names(m);
    var title = n.home + " " + t.vs + " " + n.away;
    var chans = (m.broadcasts && m.broadcasts[state.country]) || [];
    var comp = pick(m.competition, m.competitionId || "");
    var desc = comp + (chans.length ? " — " + chans.join(", ") : "") + " · Sports on TV";
    var start = new Date(m.kickoffUtc), end = new Date(start.getTime() + 2*3600000);
    return { title:title, desc:desc, start:start, end:end, uid:(m.id||title)+"@sportsontv" };
  }
  function icsBlobUrl(m){
    var e = eventOf(m);
    var body = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Sports on TV//EN","CALSCALE:GREGORIAN",
      "BEGIN:VEVENT","UID:"+e.uid,"DTSTAMP:"+icsStamp(new Date()),"DTSTART:"+icsStamp(e.start),
      "DTEND:"+icsStamp(e.end),"SUMMARY:"+icsEsc(e.title),"DESCRIPTION:"+icsEsc(e.desc),
      "BEGIN:VALARM","ACTION:DISPLAY","DESCRIPTION:"+icsEsc(e.title),"TRIGGER:-PT15M","END:VALARM",
      "END:VEVENT","END:VCALENDAR"].join("\r\n");
    return "data:text/calendar;charset=utf-8," + encodeURIComponent(body);
  }
  function gcalUrl(m){
    var e = eventOf(m);
    return "https://calendar.google.com/calendar/render?action=TEMPLATE"
      + "&text=" + encodeURIComponent(e.title)
      + "&dates=" + icsStamp(e.start) + "/" + icsStamp(e.end)
      + "&details=" + encodeURIComponent(e.desc);
  }

  function wireReminders(){
    var box = $("#matchlist");
    box.querySelectorAll(".remind").forEach(function(wrap){
      var btn = wrap.querySelector(".rbtn"), menu = wrap.querySelector(".rmenu");
      var m = state.view[+btn.getAttribute("data-idx")];
      wrap.querySelector(".gcal").href = gcalUrl(m);
      var ics = wrap.querySelector(".ics");
      ics.href = icsBlobUrl(m);
      ics.setAttribute("download", (m.id||"match") + ".ics");
      btn.addEventListener("click", function(ev){
        ev.stopPropagation();
        var open = !menu.hasAttribute("hidden");
        closeMenus();
        if (open) return;
        menu.removeAttribute("hidden");
      });
    });
  }
  function closeMenus(){ document.querySelectorAll(".rmenu").forEach(function(mn){ mn.setAttribute("hidden",""); }); }
  document.addEventListener("click", closeMenus);

  function render(){
    var box = $("#matchlist"); if (!box) return;
    var list = state.matches.slice();

    // Ülke filtresi: maç yalnızca seçilen ülkede yayınlanıyorsa gösterilir.
    // Yayıncısı yoksa yalnız dünya çapında ilgi gören turnuvalar (tier "global")
    // kalır — aksi hâlde Türk ziyaretçi ABD'nin USL maçlarıyla dolu liste görüyordu.
    list = list.filter(function(m){
      var ch = (m.broadcasts && m.broadcasts[state.country]) || [];
      return ch.length > 0 || m.tier === "global";
    });

    // Biten maçlar listeden düşer; kimse dünkü sonucu aramıyor.
    list = list.filter(function(m){ return statusOf(m) !== "finished"; });

    if (state.filter !== "all") list = list.filter(function(m){ return m.sport === state.filter; });
    list.sort(function(a,b){ return new Date(a.kickoffUtc)-new Date(b.kickoffUtc); });
    state.view = list;
    if (!list.length){ box.innerHTML = '<div class="state">'+IC.clock+'<p>'+t.empty+'</p></div>'; return; }
    box.innerHTML = list.map(matchCard).join("");
    wireReminders();
  }

  function buildFilters(){
    var wrap = $("#filters"); if (!wrap) return;
    var tabs = [["all",t.all],["football",t.football],["basketball",t.basketball],["volleyball",t.volleyball],["motorsport",t.motorsport]];
    wrap.innerHTML = tabs.map(function(o){
      return '<button class="tab" data-f="'+o[0]+'" aria-pressed="'+(o[0]===state.filter)+'">'+esc(o[1])+"</button>";
    }).join("");
    wrap.querySelectorAll(".tab").forEach(function(b){
      b.addEventListener("click", function(){
        state.filter = b.getAttribute("data-f");
        wrap.querySelectorAll(".tab").forEach(function(x){ x.setAttribute("aria-pressed", x===b); });
        render();
      });
    });
  }

  function injectJsonLd(){
    try {
      var items = state.matches.slice(0, 30).map(function(m){
        var n = names(m);
        var o = { "@type":"SportsEvent", "name": n.home + " " + t.vs + " " + n.away,
          "startDate": m.kickoffUtc, "eventStatus":"https://schema.org/EventScheduled",
          "sport": m.sport,
          "competitor":[{"@type":"SportsTeam","name":n.home},{"@type":"SportsTeam","name":n.away}] };
        var chans = m.broadcasts && m.broadcasts[state.country];
        if (chans && chans.length) o.publisher = chans.map(function(c){ return {"@type":"Organization","name":c}; });
        return o;
      });
      var s = document.createElement("script"); s.type="application/ld+json"; s.id="ld-events";
      s.textContent = JSON.stringify({ "@context":"https://schema.org", "@graph": items });
      document.head.appendChild(s);
    } catch(e){}
  }
  function showUpdated(payload){
    var el = $("#updated"); if (!el || !(payload.generated_at || payload.date)) return;
    try {
      var d = new Date(payload.generated_at || payload.date);
      el.textContent = t.updated + ": " + new Intl.DateTimeFormat(LANG,{dateStyle:"medium"}).format(d);
    } catch(e){}
  }

  function boot(){
    state.country = detectCountry();
    buildFormatters();   // ülke belli olduktan SONRA kur, yoksa cihaz saati kalır
    state.tz = tzFor(state.country) || Intl.DateTimeFormat().resolvedOptions().timeZone || "";
    var tzEl = $("#tzchip"); if (tzEl) tzEl.innerHTML = IC.clock + '<span>' + (state.tz || t.tz) + '</span>';
    buildCountrySelect();
    buildFilters();
    var box = $("#matchlist");
    if (box) box.innerHTML = '<div class="state"><div class="spinner"></div><p>'+t.loading+'</p></div>';
    fetchData().then(function(payload){
      state.matches = Array.isArray(payload.matches) ? payload.matches : [];
      render(); showUpdated(payload); injectJsonLd();
    }).catch(function(){
      if (box) box.innerHTML = '<div class="state">'+IC.tv+'<p>'+t.err+'</p>'
        +'<button class="tab" id="retry" style="margin-top:12px">'+t.retry+'</button></div>';
      var r = $("#retry"); if (r) r.addEventListener("click", boot);
    });
  }

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
