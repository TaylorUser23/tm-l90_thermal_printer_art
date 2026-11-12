"""
Parchment scroll printer for the Epson TM-L90 (ESC/POS via the Windows Epson driver).

Wraps your message inside an ASCII-art scroll and prints it. The scroll grows
as long as your text needs.

Setup (once):
    1. Install the Epson TM-L90 Windows driver (APD) with the printer on and plugged in.
    2. py -3.14 -m pip install "python-escpos[all]"

Usage:
    py -3.14 scroll_print.py                                   # demo proclamation
    py -3.14 scroll_print.py "Your message" --title "Notice"
    py -3.14 scroll_print.py "Paragraph one.\nParagraph two."  # \n = new paragraph
    py -3.14 scroll_print.py "Your message" --preview          # show in terminal only
    py -3.14 scroll_print.py --list                            # list installed printers
    py -3.14 scroll_print.py --ruler                           # find max characters per line
    py -3.14 scroll_print.py "Your message" --width 40         # override line width
"""

import argparse
import sys
import textwrap

# ---------------------------------------------------------------- settings
PRINTER_NAME = None      # exact Windows printer name, or None to auto-pick an Epson
COLUMNS = 42             # characters per line; run --ruler to find your printer's max

DEFAULT_TITLE = "A Proclamation"
DEFAULT_TEXT = (
    "Hear ye, hear ye! Let it be known throughout the land that this humble "
    "thermal printer hath been tamed by Python and ESC/POS.\n"
    "From this day forth it shall print text, art and images at the "
    "command of its keeper."
)
# -------------------------------------------------------------------------


def make_scroll(text, title=None, width=48):
    """Build an ASCII-art parchment scroll with wrapped text inside.

    width = total characters per line (48 fits Font A on 80 mm paper).
    """
    n = width - 4                 # length of the top edge
    inner = n - 2                 # space between the side bars
    pad = 2                       # margin inside the scroll
    text_w = inner - pad * 2

    def row(content="", align="left"):
        if align == "center":
            content = content.center(text_w)
        return "  |" + " " * pad + content.ljust(text_w) + " " * pad + "|"

    lines = [
        " " + "_" * n,
        "/\\" + " " * (n - 1) + "\\",
        "\\_|" + " " * inner + "|",
    ]

    if title:
        lines.append(row())
        for t in textwrap.wrap(title.upper(), text_w):
            lines.append(row(t, "center"))
        lines.append(row("~ * ~", "center"))

    lines.append(row())
    for i, para in enumerate(text.split("\n")):
        if i:
            lines.append(row())
        lines.extend(row(l) for l in textwrap.wrap(para, text_w) or [""])
    lines.append(row())

    lines += [
        "  |  " + "_" * (inner - 2) + "|_",
        "  \\_/" + "_" * (inner - 1) + "/",
    ]
    return "\n".join(lines)


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
    parser = argparse.ArgumentParser(description="Print an ASCII parchment scroll on an Epson TM-L90.")
    parser.add_argument("text", nargs="?", default=None,
                        help='message to print (use "\\n" for new paragraphs)')
    parser.add_argument("--title", help="title shown at the top of the scroll")
    parser.add_argument("--preview", action="store_true",
                        help="show the scroll in the terminal instead of printing")
    parser.add_argument("--printer", default=PRINTER_NAME, help="exact Windows printer name")
    parser.add_argument("--list", action="store_true", help="list installed printers and exit")
    parser.add_argument("--width", type=int, default=COLUMNS,
                        help=f"characters per line (default {COLUMNS})")
    parser.add_argument("--ruler", action="store_true",
                        help="print a numbered ruler to find how many characters fit per line")
    args = parser.parse_args()

    if args.list:
        for name in list_printers():
            print(repr(name))
        return

    if args.ruler:
        tens = "".join(str(i // 10 % 10) if i % 10 == 0 else " " for i in range(1, 65))
        ones = "".join(str(i % 10) for i in range(1, 65))
        output = ("Last visible number = your max width\n\n"
                  + tens + "\n" + ones + "\n" + ("|" + "-" * 9) * 6 + "|---")
    else:
        if args.width < 20:
            sys.exit("--width must be at least 20")
        if args.text is None:
            text, title = DEFAULT_TEXT, args.title or DEFAULT_TITLE
        else:
            text, title = args.text.replace("\\n", "\n"), args.title
        output = make_scroll(text, title, args.width)

    if args.preview:
        print(output)
        return

    from escpos.printer import Win32Raw

    name = pick_printer(args.printer)
    print(f"Printing to: {name}")
    p = Win32Raw(name)

    try:
        p.set_with_default(align="left")   # Font A, normal size
        p.text(output + "\n\n\n")
        p.cut()
    finally:
        p.close()

    print("Done.")


if __name__ == "__main__":
    main()