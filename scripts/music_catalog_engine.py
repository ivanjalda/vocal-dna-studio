#!/usr/bin/env python3
"""
Vocal DNA Studio - Motor del catalogo musical y del ranking.

Solo usa la libreria estandar de Python.

Que hace cada dia:
  1. Compone canciones nuevas y originales (acordes, ritmo, melodia y letra)
     y las guarda en data/generated_songs.json.
  2. Si existe el secreto TELEGRAM_BOT_TOKEN, lee las puntuaciones que los
     usuarios han enviado al bot y actualiza data/vocal_ranking.json.
  3. Elige el "Talento Vocal del Dia" (la mejor puntuacion recibida en las
     ultimas 24 horas). Si nadie ha participado, no inventa a nadie.
"""

import datetime as dt
import hashlib
import json
import os
import random
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SONGS_FILE = os.path.join(DATA, "generated_songs.json")
RANKING_FILE = os.path.join(DATA, "vocal_ranking.json")
STATE_FILE = os.path.join(DATA, "telegram_state.json")

SONGS_PER_DAY = 3
KEEP_DAYS = 60
RANKING_SIZE = 100
LICENSE = {
    "owner": "Community16 LLC",
    "es": "Base y letra originales propiedad de Community16 LLC (Vocal DNA Studio). "
          "Licencia gratuita para usarla en redes sociales (TikTok, Reels, Shorts, etc.) "
          "mencionando a Vocal DNA Studio. Prohibida su venta o registro por terceros.",
    "en": "Original beat and lyrics owned by Community16 LLC (Vocal DNA Studio). "
          "Free licence to use it on social media (TikTok, Reels, Shorts, etc.) "
          "crediting Vocal DNA Studio. Resale or registration by third parties is prohibited.",
}

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
}
# Grados (0 = primer grado de la escala) de progresiones clasicas de dominio publico
PROGRESSIONS = {
    "major": [[0, 4, 5, 3], [5, 3, 0, 4], [0, 5, 3, 4], [0, 3, 5, 4], [3, 0, 4, 5]],
    "minor": [[0, 5, 2, 6], [0, 3, 5, 4], [0, 6, 5, 6], [5, 6, 0, 0], [0, 3, 6, 2]],
}
ROMAN = {
    "major": ["I", "ii", "iii", "IV", "V", "vi", "vii°"],
    "minor": ["i", "ii°", "III", "iv", "v", "VI", "VII"],
}

# Patrones de bateria en 16 pasos (1 = golpe)
def p(s):
    return [1 if c == "x" else 0 for c in s]

GENRES = {
    "pop": {
        "name": {"es": "Pop", "en": "Pop"}, "bpm": (96, 118), "modes": ["major", "minor"],
        "kick": p("x.......x.x....."), "snare": p("....x.......x..."), "hat": p("x.x.x.x.x.x.x.x."),
        "sound": "pad",
    },
    "lofi": {
        "name": {"es": "Lo-fi", "en": "Lo-fi"}, "bpm": (72, 86), "modes": ["major", "minor"],
        "kick": p("x......x..x....."), "snare": p("....x.......x..."), "hat": p("x.x.x.x.x.x.x.xx"),
        "sound": "keys",
    },
    "balada": {
        "name": {"es": "Balada", "en": "Ballad"}, "bpm": (64, 76), "modes": ["major", "minor"],
        "kick": p("x.......x......."), "snare": p("....x.......x..."), "hat": p("x...x...x...x..."),
        "sound": "keys",
    },
    "urbano": {
        "name": {"es": "Urbano latino", "en": "Latin urban"}, "bpm": (88, 98), "modes": ["minor"],
        "kick": p("x...x...x...x..."), "snare": p("...x..x....x..x."), "hat": p("x.x.x.x.x.x.x.x."),
        "sound": "pluck",
    },
    "rnb": {
        "name": {"es": "R&B", "en": "R&B"}, "bpm": (66, 80), "modes": ["minor", "major"],
        "kick": p("x.....x...x....."), "snare": p("....x.......x..."), "hat": p("x.xxx.x.x.xxx.x."),
        "sound": "pad",
    },
    "dance": {
        "name": {"es": "Dance", "en": "Dance"}, "bpm": (118, 126), "modes": ["minor", "major"],
        "kick": p("x...x...x...x..."), "snare": p("....x.......x..."), "hat": p("..x...x...x...x."),
        "sound": "pluck",
    },
}

# Ritmos de melodia (inicio, duracion) en pasos de semicorchea dentro de un compas
RHYTHMS = [
    [(0, 2), (2, 2), (4, 4), (10, 2), (12, 4)],
    [(0, 3), (3, 1), (4, 2), (6, 2), (8, 6)],
    [(2, 2), (4, 2), (6, 2), (8, 4), (12, 2)],
    [(0, 4), (4, 2), (6, 2), (8, 2), (10, 6)],
    [(0, 2), (3, 3), (6, 2), (8, 2), (12, 4)],
]

# Bancos de frases ORIGINALES escritas para la plataforma.
LYRICS = {
    "es": {
        "open": [
            "Enciendo la luz de esta ciudad dormida",
            "Camino descalzo sobre el ruido del día",
            "Guardo tu nombre en el bolsillo del abrigo",
            "Hay un latido que no pide permiso",
            "Abro la ventana y entra todo el verano",
            "Llevo una canción escondida en la garganta",
            "Las calles brillan cuando vuelves a mirarme",
            "Me sobra el miedo y me falta la calma",
        ],
        "middle": [
            "y cada paso suena como un tambor",
            "y el reloj se olvida de contar",
            "aunque el mundo diga que no",
            "con el corazón a todo volumen",
            "como un eco que no quiere parar",
            "mientras la noche se vuelve canción",
            "dejando atrás lo que pesaba",
            "con la voz temblando pero firme",
        ],
        "hook": [
            "Esta es mi voz, nadie la puede callar",
            "Si tú me escuchas, vuelvo a empezar",
            "Brilla, brilla, no te apagues hoy",
            "Canta conmigo hasta que salga el sol",
            "Todo lo que soy cabe en esta canción",
            "Sube el volumen, que llego yo",
        ],
        "theme": ["libertad", "verano", "segunda oportunidad", "noche en la ciudad", "amor propio", "volver a casa"],
        "title_a": ["Luz", "Eco", "Latido", "Ciudad", "Fuego", "Marea", "Neón", "Horizonte", "Reflejo", "Brillo"],
        "title_b": ["de medianoche", "sin miedo", "en mi voz", "de verano", "infinito", "dorado", "en calma", "salvaje"],
    },
    "en": {
        "open": [
            "I light up the city while it's sleeping",
            "Walking barefoot through the noise of the day",
            "I keep your name inside my coat pocket",
            "There's a heartbeat that won't ask permission",
            "I open the window and the summer rushes in",
            "I've got a song hiding in my throat",
            "The streets start shining when you look my way",
            "Too much fear and not enough calm",
        ],
        "middle": [
            "and every step is beating like a drum",
            "and the clock forgets to count",
            "even if the world says no",
            "with my heart at full volume",
            "like an echo that won't fade away",
            "while the night turns into a song",
            "leaving behind what weighed me down",
            "with a shaking but steady voice",
        ],
        "hook": [
            "This is my voice, no one can silence it",
            "If you're listening, I'll start again",
            "Shine, shine, don't you fade tonight",
            "Sing with me until the sun comes up",
            "Everything I am fits in this song",
            "Turn it up, here I come",
        ],
        "theme": ["freedom", "summer", "second chance", "city night", "self-love", "coming home"],
        "title_a": ["Midnight", "Fearless", "Golden", "Wild", "Endless", "Neón", "Quiet", "Electric", "Burning", "Bright"],
        "title_b": ["Light", "Echo", "Heartbeat", "City", "Fire", "Tide", "Horizon", "Reflection", "Voice", "Glow"],
    },
}

VOICE_TYPES = {"bs": "Bajo", "br": "Barítono", "tn": "Tenor", "ct": "Contralto", "mz": "Mezzosoprano", "sp": "Soprano"}
VOICE_TYPES_EN = {"bs": "Bass", "br": "Baritone", "tn": "Tenor", "ct": "Contralto", "mz": "Mezzo-soprano", "sp": "Soprano"}


# ---------------------------------------------------------------- utilidades
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def fnv1a(text):
    """Mismo calculo que la web (JavaScript) para comprobar las puntuaciones."""
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return base36(h)


def base36(n):
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    out = ""
    while n:
        n, r = divmod(n, 36)
        out = chars[r] + out
    return out


# ---------------------------------------------------------------- composicion
def chord_notes(root_pc, mode, degree):
    """Triada (y septima opcional) construida sobre la escala."""
    sc = SCALES[mode]
    notes = []
    for k in (0, 2, 4):
        idx = degree + k
        octave, i = divmod(idx, 7)
        notes.append(root_pc + sc[i] + 12 * octave)
    return notes


def scale_pitches(tonic_midi, mode, low, high):
    sc = SCALES[mode]
    out = []
    for m in range(low, high + 1):
        if (m - tonic_midi) % 12 in sc:
            out.append(m)
    return out


def make_melody(rng, tonic_midi, mode, chords, bars):
    """Melodia con estructura A A' A B (motivo que se repite y varia)."""
    pitches = scale_pitches(tonic_midi, mode, tonic_midi - 5, tonic_midi + 12)
    base_rhythm = rng.choice(RHYTHMS)
    alt_rhythm = rng.choice(RHYTHMS)
    melody = []
    prev = tonic_midi + SCALES[mode][2]
    motif_offsets = None
    for bar in range(bars):
        chord = chords[bar % len(chords)]
        chord_pcs = {n % 12 for n in chord}
        section = bar % 4
        rhythm = alt_rhythm if section == 3 else base_rhythm
        notes_bar = []
        for j, (start, length) in enumerate(rhythm):
            strong = start in (0, 4, 8, 12)
            candidates = [m for m in pitches if abs(m - prev) <= 5]
            if strong:
                ct = [m for m in candidates if m % 12 in chord_pcs]
                if ct:
                    candidates = ct
            if not candidates:
                candidates = pitches
            # preferencia por movimiento por grado conjunto
            weights = [1.0 / (1 + abs(m - prev)) for m in candidates]
            choice = rng.choices(candidates, weights=weights, k=1)[0]
            if section == 1 and motif_offsets and j < len(motif_offsets):
                # A' : repite el contorno del compas 0
                target = prev + motif_offsets[j]
                choice = min(pitches, key=lambda m: abs(m - target))
            notes_bar.append((start, length, choice))
            prev = choice
        if section == 0 and bar == 0:
            motif_offsets = [0] + [notes_bar[k][2] - notes_bar[k - 1][2] for k in range(1, len(notes_bar))]
        # Final de frase sobre nota del acorde y larga
        if section == 3:
            s, l, m = notes_bar[-1]
            ct = [x for x in pitches if x % 12 in chord_pcs]
            if ct:
                m = min(ct, key=lambda x: abs(x - m))
            notes_bar[-1] = (s, max(l, 4), m)
        for s, l, m in notes_bar:
            melody.append({"s": bar * 16 + s, "l": l, "n": m})
    return melody


def make_lyrics(rng, lang, bars):
    bank = LYRICS[lang]
    lines = []
    for i in range(bars // 2):
        if i % 4 == 3:
            lines.append(rng.choice(bank["hook"]))
        elif i % 2 == 0:
            lines.append(rng.choice(bank["open"]))
        else:
            lines.append(rng.choice(bank["middle"]))
    return lines


def make_title(rng):
    es = f'{rng.choice(LYRICS["es"]["title_a"])} {rng.choice(LYRICS["es"]["title_b"])}'
    en = f'{rng.choice(LYRICS["en"]["title_a"])} {rng.choice(LYRICS["en"]["title_b"])}'
    return {"es": es, "en": en}


def compose_song(day, index):
    seed = int(hashlib.sha256(f"vocal-dna-{day}-{index}".encode()).hexdigest(), 16)
    rng = random.Random(seed)
    genre_key = rng.choice(list(GENRES))
    g = GENRES[genre_key]
    mode = rng.choice(g["modes"])
    tonic_pc = rng.randrange(12)
    tonic_midi = 57 + ((tonic_pc - 9) % 12)  # tonica entre A3 y G#4: comoda para cantar
    if tonic_midi > 64:
        tonic_midi -= 12
    prog = rng.choice(PROGRESSIONS[mode])
    bars = 8
    chords = [chord_notes(tonic_midi - 12, mode, d) for d in prog]
    melody = make_melody(rng, tonic_midi, mode, chords, bars)
    variation = rng.random() < 0.5
    hat = list(g["hat"])
    if variation:
        hat = [1 if (i % 2 == 0 or rng.random() < 0.15) else 0 for i in range(16)]
    lyrics_seed = rng.random()
    rl = random.Random(seed + 1)
    song = {
        "id": f"{day.replace('-', '')}-{index + 1}",
        "date": day,
        "title": make_title(rng),
        "genre": genre_key,
        "genre_name": g["name"],
        "sound": g["sound"],
        "bpm": rng.randint(*g["bpm"]),
        "key": NOTE_NAMES[tonic_midi % 12],
        "mode": mode,
        "tonic": tonic_midi,
        "bars": bars,
        "progression": [ROMAN[mode][d] for d in prog],
        "chords": chords,
        "drums": {"kick": g["kick"], "snare": g["snare"], "hat": hat},
        "melody": melody,
        "theme": {"es": LYRICS["es"]["theme"][int(lyrics_seed * 6)], "en": LYRICS["en"]["theme"][int(lyrics_seed * 6)]},
        "lyrics": {"es": make_lyrics(rl, "es", bars), "en": make_lyrics(random.Random(seed + 2), "en", bars)},
        "license": LICENSE,
    }
    return song


def update_catalog(today):
    data = load_json(SONGS_FILE, {"songs": []})
    songs = [s for s in data.get("songs", []) if s.get("date")]
    have = {s["id"] for s in songs}
    # El primer dia se crea un catalogo inicial mas grande
    count = 12 if not songs else SONGS_PER_DAY
    for i in range(count):
        s = compose_song(today, i)
        if s["id"] not in have:
            songs.append(s)
    limit = (dt.date.fromisoformat(today) - dt.timedelta(days=KEEP_DAYS)).isoformat()
    songs = [s for s in songs if s["date"] >= limit]
    songs.sort(key=lambda s: s["id"], reverse=True)
    out = {
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": len(songs),
        "songs": songs,
    }
    save_json(SONGS_FILE, out)
    print(f"Catalogo: {len(songs)} canciones")
    return out


# ---------------------------------------------------------------- ranking
PAYLOAD_RE = re.compile(r"^v1-([A-Za-z0-9]{2,14})-(\d{1,3})-(bs|br|tn|ct|mz|sp)-(\d{8})-([0-9a-z]{1,8})$")


def tg_api(token, method, params):
    url = f"https://api.telegram.org/bot{token}/{method}"
    body = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=body)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def read_submissions(token, ranking):
    state = load_json(STATE_FILE, {"offset": 0})
    try:
        res = tg_api(token, "getUpdates", {"offset": state.get("offset", 0), "timeout": 0, "allowed_updates": '["message"]'})
    except Exception as e:  # noqa: BLE001
        print("Aviso: no se pudo leer Telegram:", e)
        return 0
    added = 0
    today = dt.date.today()
    for upd in res.get("result", []):
        state["offset"] = upd["update_id"] + 1
        msg = upd.get("message") or {}
        text = (msg.get("text") or "").strip()
        if not text.startswith("/start"):
            continue
        payload = text[6:].strip()
        m = PAYLOAD_RE.match(payload)
        lang = "es" if str((msg.get("from") or {}).get("language_code", "")).startswith("es") else "en"
        chat_id = (msg.get("chat") or {}).get("id")
        ok = False
        if m:
            name, score, vt, date, chk = m.groups()
            score_i = int(score)
            try:
                d = dt.datetime.strptime(date, "%Y%m%d").date()
            except ValueError:
                d = None
            valid = (
                d is not None
                and abs((today - d).days) <= 2
                and 0 <= score_i <= 100
                and fnv1a(f"{name}|{score}|{vt}|{date}") == chk
            )
            if valid:
                uid = hashlib.sha256(f"vdna-{(msg.get('from') or {}).get('id')}".encode()).hexdigest()[:12]
                entry = {"uid": uid, "name": name, "score": score_i, "voice": vt, "date": d.isoformat()}
                prev = next((e for e in ranking["entries"] if e["uid"] == uid), None)
                if prev is None:
                    ranking["entries"].append(entry)
                elif score_i > prev["score"] or d.isoformat() > prev["date"]:
                    prev.update({"name": name, "score": max(score_i, prev["score"]),
                                 "voice": vt, "date": d.isoformat(), "last": score_i})
                added += 1
                ok = True
        if chat_id:
            if ok:
                txt = ("✅ ¡Puntuación recibida! Aparecerás en el ranking de Vocal DNA Studio en la próxima actualización."
                       if lang == "es" else
                       "✅ Score received! You will appear in the Vocal DNA Studio ranking in the next update.")
            else:
                txt = ("🎤 Hola. Para entrar en el ranking, haz tu escáner vocal en la web y pulsa «Enviar al ranking»."
                       if lang == "es" else
                       "🎤 Hi! To join the ranking, run your vocal scan on the website and tap “Send to ranking”.")
            try:
                tg_api(token, "sendMessage", {"chat_id": chat_id, "text": txt})
            except Exception as e:  # noqa: BLE001
                print("Aviso: no se pudo responder:", e)
    save_json(STATE_FILE, state)
    return added


def update_ranking():
    ranking = load_json(RANKING_FILE, {"entries": []})
    ranking.setdefault("entries", [])
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    added = 0
    if token:
        added = read_submissions(token, ranking)
        print(f"Ranking: {added} puntuaciones nuevas recibidas por Telegram")
    else:
        print("Ranking: sin TELEGRAM_BOT_TOKEN, no se leen envios (normal hasta crear el bot)")
    entries = sorted(ranking["entries"], key=lambda e: (-e["score"], e["date"]))[:RANKING_SIZE]
    since = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    recent = [e for e in entries if e["date"] >= since]
    talent = None
    if recent:
        best = max(recent, key=lambda e: e["score"])
        talent = {"name": best["name"], "score": best["score"], "voice": best["voice"],
                  "voice_name": {"es": VOICE_TYPES[best["voice"]], "en": VOICE_TYPES_EN[best["voice"]]},
                  "date": dt.date.today().isoformat()}
    out = {
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "participants": len(entries),
        "talent_of_day": talent,
        "entries": entries,
    }
    save_json(RANKING_FILE, out)
    return out


def main():
    os.makedirs(DATA, exist_ok=True)
    today = dt.date.today().isoformat()
    update_catalog(today)
    update_ranking()
    return 0


if __name__ == "__main__":
    sys.exit(main())
