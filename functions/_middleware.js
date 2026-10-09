// Cloudflare Pages middleware — her istekten önce çalışır (Eki 2026).
//
// 1) www → çıplak alan adı (301). Sayfalardaki canonical çıplak adresi
//    gösteriyor ama www de 200 dönüyordu; Search Console sayfaları www
//    sürümüyle indeksliyordu. Yönlendirme sinyali tek adreste toplar.
//    (Cloudflare API anahtarında Redirect Rules yetkisi yok, o yüzden burada.)
// 2) Site deponun kökünden yükleniyor ("wrangler pages deploy ."), yani
//    derleme betikleri ve log da yayına çıkıyordu. Onlar 404.
const GIZLI = new Set([
  "/build_site.py", "/prerender.py", "/gunluk_yenile.py",
  "/gunluk_yenile.log", "/wrangler.jsonc", "/.gitignore",
]);

export async function onRequest({ request, next }) {
  const url = new URL(request.url);
  if (url.hostname === "www.sportstvtoday.com") {
    url.hostname = "sportstvtoday.com";
    return Response.redirect(url.toString(), 301);
  }
  if (GIZLI.has(url.pathname) || url.pathname.startsWith("/functions/") || url.pathname.startsWith("/__pycache__/")) {
    return new Response("Not found", { status: 404 });
  }
  return next();
}
