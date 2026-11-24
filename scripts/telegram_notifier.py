#!/usr/bin/env python3
"""
Vocal DNA Studio - Aviso diario en Telegram.

Publica en los canales (espanol e ingles) el "Talento Vocal del Dia" y la
base del dia. Usa estos secretos de GitHub (Settings > Secrets > Actions):
  TELEGRAM_BOT_TOKEN   token del bot
  TELEGRAM_CHANNEL_ES  canal en espanol, por ejemplo @vocaldna
  TELEGRAM_CHANNEL_EN  canal en ingles, por ejemplo @vocaldna_en
  SITE_URL             (opcional) direccion de la web
Si falta alguno, no falla: solo lo indica y termina bien.
Solo usa la libreria estandar.
"""

import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DEFAULT_URL = "https://ivanjalda.github.io/vocal-dna-studio/"


def load(name):
    with open(os.path.join(DATA, name), "r", encoding="utf-8") as f:
        return json.load(f)


def send(token, chat, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({
        "chat_id": chat, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "false",
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=30) as r:
        return json.loads(r.read().decode())


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(lang, songs, ranking, site):
    song = songs["songs"][0] if songs.get("songs") else None
    talent = ranking.get("talent_of_day")
    lines = []
    if lang == "es":
        lines.append("🎙️ <b>Vocal DNA Studio · Resumen del día</b>")
        if talent:
            lines.append(f"\n🏆 <b>Talento Vocal del Día:</b> {esc(talent['name'])}\n"
                         f"Puntuación: <b>{talent['score']}/100</b> · Voz: {esc(talent['voice_name']['es'])}")
        else:
            lines.append("\n🏆 Hoy nadie ha enviado su escáner todavía. ¿Serás tú el Talento Vocal del Día?")
        if song:
            lines.append(f"\n🎵 <b>Base del día:</b> «{esc(song['title']['es'])}»\n"
                         f"{esc(song['genre_name']['es'])} · {song['bpm']} BPM · {song['key']} "
                         f"{'menor' if song['mode'] == 'minor' else 'mayor'}\n"
                         "Libre de derechos para tus redes (mencionando a Vocal DNA Studio).")
        lines.append(f"\n👉 Escanea tu voz gratis: {site}")
    else:
        lines.append("🎙️ <b>Vocal DNA Studio · Daily digest</b>")
        if talent:
            lines.append(f"\n🏆 <b>Vocal Talent of the Day:</b> {esc(talent['name'])}\n"
                         f"Score: <b>{talent['score']}/100</b> · Voice: {esc(talent['voice_name']['en'])}")
        else:
            lines.append("\n🏆 Nobody has sent a scan yet today. Will you be the Vocal Talent of the Day?")
        if song:
            lines.append(f"\n🎵 <b>Beat of the day:</b> “{esc(song['title']['en'])}”\n"
                         f"{esc(song['genre_name']['en'])} · {song['bpm']} BPM · {song['key']} {song['mode']}\n"
                         "Royalty-free for your socials (credit Vocal DNA Studio).")
        lines.append(f"\n👉 Scan your voice for free: {site}?lang=en")
    return "\n".join(lines)


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    site = os.environ.get("SITE_URL", "").strip() or DEFAULT_URL
    channels = {"es": os.environ.get("TELEGRAM_CHANNEL_ES", "").strip(),
                "en": os.environ.get("TELEGRAM_CHANNEL_EN", "").strip()}
    songs = load("generated_songs.json")
    ranking = load("vocal_ranking.json")
    for lang in ("es", "en"):
        text = build(lang, songs, ranking, site)
        if not token or not channels[lang]:
            print(f"[{lang}] Telegram aún no configurado. Mensaje que se enviaría:\n{text}\n")
            continue
        try:
            res = send(token, channels[lang], text)
            print(f"[{lang}] enviado:", res.get("ok"))
        except Exception as e:  # noqa: BLE001
            print(f"[{lang}] ERROR al enviar:", e)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
