"""
Epson TM-L90 printer script (ESC/POS over USB via the Windows Epson driver).

Prints a text header, ASCII art, an optional image, and a QR code, then cuts.

Setup (once):
    1. Install the Epson TM-L90 Windows driver (APD) with the printer on and plugged in.
    2. python -m pip install "python-escpos[all]" pillow
    3. python tm_l90_print.py --list          (shows the exact printer name)

Usage:
    python tm_l90_print.py                                  # demo print
    python tm_l90_print.py --text "Hello world"             # print your own text
    python tm_l90_print.py --image logo.png                 # print an image
    python tm_l90_print.py --art art.txt                    # print an ASCII art file
    python tm_l90_print.py --printer "EPSON TM-L90 Receipt" # pick a printer by name
"""

import argparse
import sys

from PIL import Image

# ---------------------------------------------------------------- settings
PRINTER_NAME = None      # exact Windows printer name, or None to auto-pick an Epson
PAPER_WIDTH_DOTS = 576   # 80 mm paper = 576 dots, 58 mm paper = 420 dots
QR_TEXT = "https://tw-it.net"

DEMO_ART = r"""
   /\_/\
  ( o.o )
   > ^ <
"""
# -------------------------------------------------------------------------


def list_printers():
    import win32print
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    return [p[2] for p in win32print.EnumPrinters(flags)]


def pick_printer(name):
    printers = list_printers()
    if name:
        if name in printers:
            return name
        sys.exit(f'Printer "{name}" not found. Installed printers:\n  '
                 + "\n  ".join(printers or ["(none)"]))
    epson = [p for p in printers if "epson" in p.lower() or "tm-l90" in p.lower()]
    if not epson:
        sys.exit("No Epson printer found. Install the TM-L90 driver, then run with --list.\n"
                 "Installed printers:\n  " + "\n  ".join(printers or ["(none)"]))
    return epson[0]


def prepare_image(path, width=PAPER_WIDTH_DOTS):
    """Flatten transparency, shrink to paper width, dither to 1-bit, center on the page."""
    img = Image.open(path)

    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        background = Image.new("RGBA", img.size, "white")
        img = Image.alpha_composite(background, img)

    img = img.convert("L")

    if img.width > width:
        new_height = round(img.height * width / img.width)
        img = img.resize((width, new_height), Image.LANCZOS)

    img = img.convert("1")  # Floyd-Steinberg dithering

    # Center by padding onto a full-width white canvas
    canvas = Image.new("1", (width, img.height), 1)
    canvas.paste(img, ((width - img.width) // 2, 0))
    return canvas


def main():
    parser = argparse.ArgumentParser(description="Print to an Epson TM-L90.")
    parser.add_argument("--list", action="store_true", help="list installed printers and exit")
    parser.add_argument("--printer", default=PRINTER_NAME, help="exact Windows printer name")
    parser.add_argument("--text", help="text to print")
    parser.add_argument("--art", help="path to an ASCII art .txt file")
    parser.add_argument("--image", help="path to an image file (png, jpg, ...)")
    parser.add_argument("--no-qr", action="store_true", help="skip the QR code")
    args = parser.parse_args()

    if args.list:
        for name in list_printers():
            print(repr(name))
        return

    from escpos.printer import Win32Raw

    name = pick_printer(args.printer)
    print(f"Printing to: {name}")
    p = Win32Raw(name)
    # Tell python-escpos the paper width (silences the "media.width.pixel" warning)
    p.profile.profile_data["media"]["width"]["pixels"] = PAPER_WIDTH_DOTS

    try:
        # Header
        p.set_with_default()
        p.set(align="center", bold=True, double_height=True, double_width=True)
        p.text("TW-IT\n")
        p.set_with_default()
        p.text("\n")

        # Your text
        if args.text:
            p.set_with_default(align="left")
            p.text(args.text.replace("\\n", "\n") + "\n\n")

        # ASCII art (Font A = 48 columns on 80 mm paper, Font B = 64)
        if args.art:
            with open(args.art, encoding="utf-8") as f:
                art = f.read()
        elif not (args.text or args.image):
            art = DEMO_ART
        else:
            art = None
        if art:
            p.set_with_default(align="left")
            p.text(art.rstrip("\n") + "\n\n")

        # Image
        if args.image:
            p.image(prepare_image(args.image))
            p.text("\n")

        # QR code
        if not args.no_qr:
            p.set_with_default(align="center")
            p.qr(QR_TEXT, size=6)

        p.set_with_default()
        p.text("\n")
        p.cut()
    finally:
        p.close()

    print("Done.")


if __name__ == "__main__":
    main()