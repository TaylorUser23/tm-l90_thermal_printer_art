"""
UT Tower print for the Epson TM-L90 (ESC/POS via the Windows Epson driver).

Prints a giant "UT" headline in the printer's own enlarged font with an
ASCII clock tower underneath.

Setup (once):
    1. Install the Epson TM-L90 Windows driver (APD) with the printer on and plugged in.
    2. py -3.14 -m pip install "python-escpos[all]"

Usage:
    py -3.14 tower_print.py                                  # giant UT + tower
    py -3.14 tower_print.py --text "YOUR TEXT" --size 3      # custom headline (size 1-8)
    py -3.14 tower_print.py --caption "Austin, Texas"        # small line under the tower
    py -3.14 tower_print.py --preview                        # show in terminal only
"""

import argparse
import sys

# ---------------------------------------------------------------- settings
PRINTER_NAME = None      # exact Windows printer name, or None to auto-pick an Epson
COLUMNS = 42             # characters per line; run scroll_print.py --ruler to check
DEFAULT_TEXT = "UT"
DEFAULT_SIZE = 8         # headline magnification, 1-8 (8 = largest)
# -------------------------------------------------------------------------

TOWER = r"""
              !
             /^\
            |:::|
           _|___|_
          |=======|
          | |_|_| |
          | |_|_| |
          |=======|
          |  .-.  |
          | ( + ) |
          |  '-'  |
          |=======|
          | [] [] |
          | [] [] |
          | [] [] |
          | [] [] |
          | [] [] |
          | [] [] |
 _________|_______|_________
|    [] [] []   [] [] []    |
|    [] [] []   [] [] []    |
|    [] [] []   [] [] []    |
|___________|___|___________|
/___________________________\
"""


def center_block(art, width):
    """Center a multi-line drawing as one block so its lines stay aligned."""
    lines = art.strip("\n").splitlines()
    widest = max(len(l) for l in lines)
    if widest > width:
        sys.exit(f"Drawing is {widest} characters wide but COLUMNS is {width}.")
    left = " " * ((width - widest) // 2)
    return "\n".join(left + l.rstrip() for l in lines)


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


def main():
    parser = argparse.ArgumentParser(description="Print a giant UT headline and the tower.")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="headline text")
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE, choices=range(1, 9),
                        metavar="1-8", help="headline magnification")
    parser.add_argument("--caption", help="small line printed under the tower")
    parser.add_argument("--width", type=int, default=COLUMNS, help="characters per line")
    parser.add_argument("--preview", action="store_true", help="show in terminal instead of printing")
    parser.add_argument("--printer", default=PRINTER_NAME, help="exact Windows printer name")
    parser.add_argument("--list", action="store_true", help="list installed printers and exit")
    args = parser.parse_args()

    if args.list:
        for name in list_printers():
            print(repr(name))
        return

    tower = center_block(TOWER, args.width)
    headline = args.text.upper()

    max_chars = args.width // args.size
    if len(headline) > max_chars:
        print(f"Note: at size {args.size} only {max_chars} characters fit per line; "
              "the headline will wrap. Use a smaller --size to keep it on one line.")

    if args.preview:
        print(f"[ {headline} ]  (printed at {args.size}x size)".center(args.width))
        print()
        print(tower)
        if args.caption:
            print(args.caption.center(args.width))
        return

    from escpos.printer import Win32Raw

    name = pick_printer(args.printer)
    print(f"Printing to: {name}")
    p = Win32Raw(name)

    try:
        p.set_with_default(align="left")
        p.set_with_default(align="center", bold=True, custom_size=True,
                           width=args.size, height=args.size)
        p.text(headline + "\n")

        p.set_with_default(align="left")
        p.text("\n" + tower + "\n")

        if args.caption:
            p.set_with_default(align="center")
            p.text("\n" + args.caption + "\n")

        p.set_with_default()
        p.text("\n\n")
        p.cut()
    finally:
        p.close()

    print("Done.")


if __name__ == "__main__":
    main()
