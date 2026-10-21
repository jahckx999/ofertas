#!/usr/bin/env python3
"""Gera o Reel do dia (1080x1920, ~10 s, H.264 + AAC, faststart) com música original sintetizada.

Cenas: 1) gancho (0–3 s)  2) arte do story com zoom lento (3–7 s)  3) chamada para ação (7–10 s).
A música é gerada aqui mesmo (acordes + batida), então não tem direitos autorais de terceiros.

Uso:
  python3 tools/gerar_reel.py --gancho "Pare de gastar errado com a casa" \
      --tema "Achadinhos de casa" --arte posts/2026-10-21-story.png --saida posts/2026-10-21-reel.mp4 [--cor 0]
Requer: playwright (chromium), ffmpeg, numpy.
"""
import argparse, html, pathlib, subprocess, tempfile, wave
import numpy as np
from playwright.sync_api import sync_playwright

CORES = [("#0F2A3D", "#FF5A36", "#FFC23D"), ("#13334A", "#FF5A36", "#7EE0B5"),
         ("#2A1B3D", "#FF6C4A", "#FFC23D"), ("#0E3B32", "#FF5A36", "#FFE08A")]
W, H, FPS = 1080, 1920, 30

def cena(fundo, tag, dest, topo, grande, pequeno, rodape):
    e = html.escape
    return f"""<html><body style="margin:0;width:{W}px;height:{H}px;background:{fundo};color:#F2F7FA;
    font-family:'Inter Display','Inter',sans-serif;display:flex;flex-direction:column;justify-content:center;
    padding:0 90px;box-sizing:border-box;gap:40px;overflow:hidden">
    <div style="font-weight:800;font-size:40px;letter-spacing:.06em">GARIMPO <span style="color:{dest}">DIÁRIO</span></div>
    <div style="display:inline-block;align-self:flex-start;background:{dest};color:{fundo};font-weight:800;font-size:38px;
      padding:14px 30px;border-radius:999px;text-transform:uppercase;letter-spacing:.05em">{e(topo)}</div>
    <div style="font-weight:900;font-size:118px;line-height:1;letter-spacing:-.02em">{e(grande)}</div>
    <div style="font-size:52px;line-height:1.3;color:#C9DCE7">{e(pequeno)}</div>
    <div style="align-self:flex-start;background:{tag};color:#fff;font-weight:800;font-size:56px;padding:26px 46px;
      border-radius:999px;box-shadow:0 10px 0 #0005">{e(rodape)}</div></body></html>"""

def musica(caminho, segundos=10.0, sr=44100, bpm=100):
    t = np.arange(int(sr * segundos)) / sr
    beat = 60 / bpm
    nota = lambda f: 440 * 2 ** ((f - 69) / 12)
    acordes = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]  # C G Am F
    som = np.zeros_like(t)
    compasso = beat * 4
    for i, ac in enumerate(acordes * 4):
        ini = i * compasso
        if ini >= segundos: break
        m = (t >= ini) & (t < ini + compasso)
        tt = t[m] - ini
        env = np.minimum(1, tt / 0.15) * np.exp(-tt * 0.6)
        for n in ac:
            som[m] += 0.07 * env * (np.sin(2 * np.pi * nota(n) * tt) + 0.3 * np.sin(2 * np.pi * nota(n + 12) * tt))
        b = nota(ac[0] - 24)  # baixo
        for k in range(4):
            mk = (t >= ini + k * beat) & (t < ini + k * beat + beat * 0.9)
            tk = t[mk] - ini - k * beat
            som[mk] += 0.12 * np.exp(-tk * 5) * np.sin(2 * np.pi * b * tk)
    n_beats = int(segundos / beat) + 1
    rng = np.random.default_rng(7)
    for k in range(n_beats):
        ini = k * beat
        m = (t >= ini) & (t < ini + 0.25)
        tk = t[m] - ini
        som[m] += 0.35 * np.exp(-tk * 18) * np.sin(2 * np.pi * (110 * np.exp(-tk * 25) + 45) * tk)  # bumbo
        for h in (0, beat / 2):
            mh = (t >= ini + h) & (t < ini + h + 0.05)
            th = t[mh] - ini - h
            som[mh] += 0.05 * np.exp(-th * 80) * rng.uniform(-1, 1, mh.sum())  # chimbal
    fade = np.minimum(1, np.minimum(t / 0.3, (segundos - t) / 0.8))
    som = np.clip(som * fade, -0.95, 0.95)
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((som * 32767).astype(np.int16).tobytes())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gancho", required=True); ap.add_argument("--tema", required=True)
    ap.add_argument("--arte", required=True); ap.add_argument("--saida", required=True)
    ap.add_argument("--cor", type=int, default=0)
    a = ap.parse_args()
    fundo, tag, dest = CORES[a.cor % len(CORES)]
    tmp = pathlib.Path(tempfile.mkdtemp())
    with sync_playwright() as p:
        b = p.chromium.launch()
        for nome, args in [
            ("c1", (a.tema, a.gancho, "Separei os achados de hoje 👇", "Assista até o fim")),
            ("c3", ("Ofertas de hoje", "Link na bio 🏷️", "Comente EU QUERO que eu te mando o link", "Compra segura no Mercado Livre")),
        ]:
            pg = b.new_page(viewport={"width": W, "height": H})
            pg.set_content(cena(fundo, tag, dest, *args)); pg.screenshot(path=str(tmp / f"{nome}.png")); pg.close()
        b.close()
    musica(tmp / "m.wav")
    arte = str(pathlib.Path(a.arte).resolve())
    z = lambda d, ini, fim: (f"scale=1188:2112,zoompan=z='{ini}+({fim}-{ini})*on/{int(d*FPS)}':"
                             f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(d*FPS)}:s={W}x{H}:fps={FPS},setsar=1")
    filtro = (f"[0:v]{z(3.4,1.0,1.06)}[a];[1:v]{z(4.4,1.0,1.10)}[b];[2:v]{z(3.4,1.06,1.0)}[c];"
              f"[a][b]xfade=transition=slideup:duration=0.4:offset=3.0[ab];"
              f"[ab][c]xfade=transition=fade:duration=0.4:offset=7.0,format=yuv420p[v]")
    saida = pathlib.Path(a.saida); saida.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-loop", "1", "-t", "3.4", "-i", str(tmp / "c1.png"),
           "-loop", "1", "-t", "4.4", "-i", arte,
           "-loop", "1", "-t", "3.4", "-i", str(tmp / "c3.png"),
           "-i", str(tmp / "m.wav"),
           "-filter_complex", filtro, "-map", "[v]", "-map", "3:a",
           "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-b:v", "4M", "-maxrate", "4.5M", "-bufsize", "8M",
           "-g", "60", "-keyint_min", "60", "-sc_threshold", "0", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
           "-shortest", "-movflags", "+faststart", str(saida)]
    subprocess.run(cmd, check=True)
    print(saida)

if __name__ == "__main__":
    main()
