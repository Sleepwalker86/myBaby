#!/usr/bin/env python3
"""
Script zum Erstellen eines Apple Touch Icons (180x180 PNG) aus dem SVG Favicon.
Benötigt: pip install cairosvg pillow
"""

import os
import sys

try:
    import cairosvg
    from PIL import Image
    import io
except ImportError:
    print("Fehler: Bitte installiere die benötigten Pakete:")
    print("  pip install cairosvg pillow")
    sys.exit(1)

def create_apple_touch_icon():
    """Erstellt ein 180x180 PNG aus dem SVG Favicon"""
    svg_path = "app/static/favicon.svg"
    png_path = "app/static/apple-touch-icon.png"
    
    if not os.path.exists(svg_path):
        print(f"Fehler: {svg_path} nicht gefunden!")
        sys.exit(1)
    
    print(f"Konvertiere {svg_path} zu {png_path}...")
    
    # Konvertiere SVG zu PNG (180x180)
    try:
        cairosvg.svg2png(
            url=svg_path,
            write_to=png_path,
            output_width=180,
            output_height=180
        )
        print(f"✅ Erfolgreich erstellt: {png_path}")
        print(f"   Größe: 180x180 Pixel")
    except Exception as e:
        print(f"Fehler beim Konvertieren: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_apple_touch_icon()

