# Apple Touch Icon für iPhone erstellen

iOS/iPadOS benötigt für das Icon auf dem Home-Bildschirm eine PNG-Datei (180x180 Pixel), nicht SVG.

## Lösung

1. **Online-Tool verwenden** (einfachste Methode):
   - Öffne https://convertio.co/svg-png/ oder ein ähnliches Tool
   - Lade `app/static/favicon.svg` hoch
   - Stelle die Größe auf 180x180 Pixel ein
   - Lade die PNG-Datei herunter
   - Speichere sie als `app/static/apple-touch-icon.png`

2. **Mit Python-Script** (falls cairosvg installiert ist):
   ```bash
   pip install cairosvg pillow
   python3 create_apple_touch_icon.py
   ```

3. **Mit ImageMagick** (falls installiert):
   ```bash
   convert -background none -resize 180x180 app/static/favicon.svg app/static/apple-touch-icon.png
   ```

4. **Mit Inkscape** (falls installiert):
   ```bash
   inkscape -w 180 -h 180 app/static/favicon.svg -o app/static/apple-touch-icon.png
   ```

Nach dem Erstellen der Datei sollte das Icon auf dem iPhone Home-Bildschirm korrekt angezeigt werden.

