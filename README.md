# Vocal DNA Studio

Descubre el ADN de tu voz · *Discover your vocal DNA*

Web gratuita, bilingüe (español e inglés), para:

1. **Escáner de potencial vocal**: canta 15 segundos y obtén tu tipo de voz, rango, afinación, estabilidad, pureza armónica y una puntuación de 0 a 100.
2. **Catálogo de canciones originales**: cada día el motor compone bases nuevas (acordes, ritmo, melodía guía y letra) propiedad de Community16 LLC, con licencia gratuita para redes sociales.
3. **Estudio**: graba tu voz sobre la base; se afina a la escala de la canción, se ecualiza, se le pone reverberación y se sincroniza. Descarga la pista en WAV.
4. **Ranking y Talento Vocal del Día**, con aviso diario en Telegram.

Todo el sonido se procesa en el navegador del usuario: la voz nunca sale de su dispositivo.

## Estructura

| Archivo | Para qué sirve |
|---|---|
| `index.html` | La web completa |
| `favicon.svg` | Logo |
| `data/generated_songs.json` | Catálogo de canciones (lo escribe el motor) |
| `data/vocal_ranking.json` | Ranking (lo escribe el motor) |
| `scripts/music_catalog_engine.py` | Compone canciones y actualiza el ranking |
| `scripts/telegram_notifier.py` | Publica el resumen diario en Telegram |
| `scripts/site_check.py` | Revisión automática diaria de la web |
| `.github/workflows/music_update.yml` | Lo ejecuta todo cada día a las 08:17 (hora de España) |

Solo usa la librería estándar de Python y servicios gratuitos (GitHub Pages, GitHub Actions, Telegram).

## Telegram (cuando se cree el bot)

En **Settings → Secrets and variables → Actions** añadir:
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_ES`, `TELEGRAM_CHANNEL_EN`.
Y en `index.html`, dentro de `CONFIG`, el nombre del bot y de los canales.

© Community16 LLC · Albuquerque, New Mexico, USA · community16jalda@gmail.com
