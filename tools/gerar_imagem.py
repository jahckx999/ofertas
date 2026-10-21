#!/usr/bin/env python3
"""Gera a arte do post (1080x1350 feed, 1080x1920 story/reels e 1200x630 compartilhamento).

Uso:
  python3 tools/gerar_imagem.py --titulo "..." --chamada "..." --selo="-40%" \
      --tema "Achadinhos de casa" --saida posts/2026-10-21

Gera <saida>-feed.png, <saida>-story.png. Com --og gera img/og.png.
Requer: pip install playwright && python3 -m playwright install chromium
"""
import argparse, html, pathlib
from playwright.sync_api import sync_playwright

CORES = [  # (fundo, etiqueta, destaque) — alterna por dia para o feed não ficar repetitivo
    ("#0F2A3D", "#FF5A36", "#FFC23D"),
    ("#13334A", "#FF5A36", "#7EE0B5"),
    ("#2A1B3D", "#FF6C4A", "#FFC23D"),
    ("#0E3B32", "#FF5A36", "#FFE08A"),
]

def pagina(w, h, titulo, chamada, selo, tema, cor, rodape):
    fundo, tag, dest = cor
    t = html.escape(titulo); c = html.escape(chamada); s = html.escape(selo); tm = html.escape(tema)
    big = 118 if h > 1500 else (96 if h > 1000 else 58)
    base = min(w, h*1.1)
    tw = int(min(w*.26, h*.36)); th = int(tw*1.27)
    return f"""<html><head><meta charset=utf-8><style>
    @font-face{{font-family:B;src:local('Inter Display ExtraBold'),local('Inter ExtraBold');}}
    body{{margin:0;width:{w}px;height:{h}px;background:{fundo};color:#F2F7FA;font-family:'Inter Display','Inter',sans-serif;overflow:hidden;position:relative}}
    .pad{{position:absolute;inset:{int(min(w,h*1.4)*.07)}px;display:flex;flex-direction:column;justify-content:space-between}}
    .top{{display:flex;justify-content:space-between;align-items:flex-start;font-size:{int(base*.03)}px;font-weight:700;letter-spacing:.04em}}
    .top b{{color:{dest}}}
    .tema{{display:inline-block;background:{dest};color:{fundo};padding:.35em .8em;border-radius:999px;font-weight:800;font-size:{int(base*.032)}px;text-transform:uppercase;letter-spacing:.06em}}
    h1{{font-size:{big}px;line-height:.98;margin:.35em 0 .3em;font-weight:900;letter-spacing:-.02em}}
    p{{font-size:{int(base*.042)}px;line-height:1.3;margin:0;color:#C9DCE7;max-width:88%}}
    .tag{{position:relative;flex:0 0 auto;width:{tw}px;height:{th}px;background:{tag};clip-path:polygon(50% 0,100% 16%,100% 100%,0 100%,0 16%);transform:rotate(8deg);display:flex;flex-direction:column;justify-content:flex-end;align-items:center;padding-bottom:{int(tw*.15)}px;box-sizing:border-box;color:#fff}}
    .tag::before{{content:'';position:absolute;top:11%;left:50%;width:{int(tw*.13)}px;height:{int(tw*.13)}px;margin-left:-{int(tw*.065)}px;border-radius:50%;background:{fundo}}}
    .tag strong{{font-size:{int(tw*.33)}px;font-weight:900;letter-spacing:-.03em}}
    .tag span{{font-size:{int(tw*.1)}px;font-weight:700;text-transform:uppercase}}
    .cta{{display:inline-flex;align-items:center;gap:.6em;background:{tag};color:#fff;font-weight:800;font-size:{int(base*.045)}px;padding:.6em 1em;border-radius:999px;align-self:flex-start;box-shadow:0 .18em 0 #0005}}
    .foot{{font-size:{int(base*.026)}px;color:#9FB7C6;margin-top:.8em}}
    </style></head><body>
    <div class=pad>
      <div class=top><span>GARIMPO <b>DIÁRIO</b></span><div class=tag><strong>{s}</strong><span>achado do dia</span></div></div>
      <div><span class=tema>{tm}</span><h1>{t}</h1><p>{c}</p></div>
      <div>{'' if h < 700 else f'<div class=cta>{rodape} →</div>'}<div class=foot>Compra segura no Mercado Livre · links de afiliado</div></div>
    </div></body></html>"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--titulo", required=True); ap.add_argument("--chamada", required=True)
    ap.add_argument("--selo", default="-40%"); ap.add_argument("--tema", default="Ofertas do dia")
    ap.add_argument("--saida", required=True); ap.add_argument("--cor", type=int, default=0)
    ap.add_argument("--og", action="store_true")
    a = ap.parse_args()
    cor = CORES[a.cor % len(CORES)]
    out = pathlib.Path(a.saida); out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        alvos = [("feed", 1080, 1350, "Link na bio"), ("story", 1080, 1920, "Toque no link")]
        if a.og: alvos = [("og", 1200, 630, "Ver ofertas")]
        for nome, w, h, rod in alvos:
            pg = b.new_page(viewport={"width": w, "height": h})
            pg.set_content(pagina(w, h, a.titulo, a.chamada, a.selo, a.tema, cor, rod))
            destino = out if a.og else out.with_name(f"{out.name}-{nome}.png")
            pg.screenshot(path=str(destino)); pg.close()
            print(destino)
        b.close()

if __name__ == "__main__":
    main()
