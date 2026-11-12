# escpos-thermal-printer

Print text, ASCII art, images and QR codes to an Epson TM-L90 thermal printer using Python and ESC/POS.

## Requirements

- Windows with the the EPSON Advanced Printer Driver (APD) for the TM-L90 installed, using a USB port
- Python 3.14 (3.15 isn't supported yet by the PyYAML dependency)

```powershell
py -3.14 -m pip install "python-escpos[all]" pillow
```

## Usage

```powershell
py -3.14 tm_l90_print.py --list                  # show installed printers
py -3.14 tm_l90_print.py                         # demo print
py -3.14 tm_l90_print.py --text "Hello world"    # custom text
py -3.14 tm_l90_print.py --art art.txt           # ASCII art from a file
py -3.14 tm_l90_print.py --image logo.jpg        # image (auto-resized and dithered)
```

Other options: `--printer "Name"` to choose a printer, `--no-qr` to skip the QR code.

## Notes

- Paper width is set by `PAPER_WIDTH_DOTS` at the top of the script: `576` for 80 mm paper, `420` for 58 mm.
- ASCII art fits up to 48 characters per line on 80 mm paper.
