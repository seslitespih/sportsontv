# -*- coding: utf-8 -*-
"""Siteyi yeniden kurar ve DEĞİŞTİYSE push'lar.

Maç listesi artık HTML'e gömülü (prerender.py). Bu yüzden fikstür her
güncellendiğinde sitenin de yeniden kurulması gerekiyor — yoksa Google
dünkü maçları görür, ki bu hiç içerik olmamasından kötüdür.

Günde birkaç kez çalışır. Üretilen HTML değişmediyse commit atmaz.

Kullanım: python gunluk_yenile.py
"""
import subprocess, sys, os, datetime

KOK = os.path.dirname(os.path.abspath(__file__))


def kos(*a, **kw):
    return subprocess.run(a, cwd=KOK, capture_output=True, text=True,
                          encoding='utf-8', errors='replace', **kw)


def log(m):
    print('[%s] %s' % (datetime.datetime.now().strftime('%H:%M:%S'), m))


# 1) Uzaktaki değişiklikleri al (başka oturum push'lamış olabilir)
kos('git', 'pull', '--rebase', '-q', 'origin', 'main')

# 2) Yeniden kur
r = kos(sys.executable, 'build_site.py')
if r.returncode != 0:
    log('BUILD HATASI:')
    print(r.stdout[-2000:], r.stderr[-2000:])
    sys.exit(1)
log(r.stdout.strip().split('\n')[-1] if r.stdout.strip() else 'build bitti')

# 3) Değişiklik var mı?
d = kos('git', 'status', '--porcelain')
if not d.stdout.strip():
    log('degisiklik yok — push atlandi')
    sys.exit(0)

dosya = len([x for x in d.stdout.strip().split('\n') if x.strip()])
log('%d dosya degisti' % dosya)

# 4) Commit + push
kos('git', 'add', '-A')
mesaj = 'auto: gunluk mac icerigi %s [skip ci]' % datetime.date.today().isoformat()
c = kos('git', 'commit', '-q', '-m', mesaj)
p = kos('git', 'push', '-q', 'origin', 'main')
if p.returncode != 0:
    # Uzakta yeni bir sey varsa rebase edip tekrar dene
    kos('git', 'fetch', '-q', 'origin')
    kos('git', 'rebase', 'origin/main')
    p = kos('git', 'push', '-q', 'origin', 'main')
log('push ' + ('TAMAM' if p.returncode == 0 else 'BASARISIZ: ' + p.stderr[-300:]))

# 5) Cloudflare Pages'e yayinla
#
# 18 Eyl 2026: site GitHub Pages'ten Cloudflare Pages'e tasindi — GitHub'in
# sertifikasi 38 gun "new" durumunda takili kaldi, https hic calismadi ve
# Google 28 gun boyunca tek gosterim vermedi.
#
# Pages projesi DOGRUDAN YUKLEME (direct upload) tipinde, yani git push'u
# kendisi izlemiyor; her derlemeden sonra buradan yuklenmesi gerekiyor.
# Kimlik bilgileri depo DISINDA: Downloads/cloudflare_sportstv.env
# (.gitignore zaten .env* kapsiyor ama dosya repoda hic durmasin diye disarida).
KIMLIK = 'C:/Users/ESAT/Downloads/cloudflare_sportstv.env'
if os.path.exists(KIMLIK):
    ortam = dict(os.environ)
    for satir in open(KIMLIK, encoding='utf-8'):
        if '=' in satir and not satir.lstrip().startswith('#'):
            k, _, v = satir.partition('=')
            ortam[k.strip()] = v.strip()
    d = subprocess.run(
        ['npx', '--yes', 'wrangler@4', 'pages', 'deploy', '.',
         '--project-name=' + ortam.get('PAGES_PROJECT', 'sportsontv'),
         '--branch=main', '--commit-dirty=true'],
        cwd=KOK, capture_output=True, text=True, encoding='utf-8',
        errors='replace', env=ortam, shell=(os.name == 'nt'))
    # wrangler ciktisinda emoji var; Windows konsolu (cp1254) basamayip
    # UnicodeEncodeError atiyor. Log'a yazmadan once ASCII disini at.
    temiz = lambda s: (s or '').encode('ascii', 'ignore').decode().strip()
    son = [x for x in temiz(d.stdout).split('\n') if x.strip()]
    log('cloudflare ' + ('TAMAM - ' + son[-1].strip() if d.returncode == 0 and son
                         else 'BASARISIZ: ' + temiz(d.stderr)[-300:]))
else:
    log('cloudflare atlandi — kimlik dosyasi yok (%s)' % KIMLIK)
