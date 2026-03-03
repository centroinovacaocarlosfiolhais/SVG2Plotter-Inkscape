# ✂ SVG2Plotter — Inkscape Extension

**Cut directly from Inkscape. No server. No network.**  
_Extensions → Export → Send to SVG2Plotter_

> Developed by **David Marques** — *Vibe Coding with Claude.ai*  
> Centro de Inovação Carlos Fiolhais · CDI Portugal

---

## What is this?

An Inkscape extension that sends the current document directly to an HPGL vinyl cutter via USB-Serial. No intermediate server, no extra software.

Open your design, go to **Extensions → Export → Send to SVG2Plotter**, choose Normal or Mirror, click Apply.

```
Inkscape
  └── Extensions → Export → Send to SVG2Plotter
            │
            │  USB-Serial (HPGL)
            ▼
       SK1350 cutter
```

---

## Dependencies

| OS | Serial backend | Extra install? |
|---|---|---|
| **Linux / Linux Mint** | `termios` (Python stdlib) | **None** |
| **macOS** | `termios` (Python stdlib) | **None** |
| **Windows** | `pyserial` | `pip install pyserial` |

---

## Installation

### Step 1 — Find your User Extensions folder

Open Inkscape → **Edit → Preferences → System**  
Note the path shown in **User extensions** — use that exact path.

Typical locations:

| OS | Typical path |
|---|---|
| Linux (apt/deb) | `~/.config/inkscape/extensions/` |
| Linux (Flatpak) | `~/.var/app/org.inkscape.Inkscape/config/inkscape/extensions/` |
| Linux (Snap) | `~/snap/inkscape/current/.config/inkscape/extensions/` |
| Windows | `%APPDATA%\inkscape\extensions\` |
| macOS | `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/` |

> Always verify in **Edit → Preferences → System** — the path depends on how Inkscape was installed.

### Step 2 — Copy the two extension files

Copy both files into that folder:

```
svg2plotter_cut.inx
svg2plotter_cut.py
```

Both files must be in the **same folder**. No subfolders.

### Step 3 — Restart Inkscape

Close and reopen Inkscape. Go to **Extensions → Export → Send to SVG2Plotter**.

---

## Automated install (recommended for CICF)

The setup script detects the correct folder automatically — including Flatpak and Snap variants:

```bash
python setup-extension.py
```

It copies the files, fixes serial port permissions on Linux, and installs pyserial on Windows.  
Restart Inkscape after running it.

---

## Usage

1. Open your design in Inkscape
2. Connect the vinyl cutter via USB
3. **Extensions → Export → Send to SVG2Plotter**
4. Set port and options:

| Field | Linux default | Windows default |
|---|---|---|
| Serial port | `/dev/ttyUSB0` | `COM5` |
| Baud rate | `9600` | `9600` |
| Mirror mode | off | off |
| Test only | off | off |

5. Click **Apply**

### Cut modes

| | Use case |
|---|---|
| **Normal** | Vinyl on opaque surfaces — cars, walls, signs |
| **Mirror** ✓ | Vinyl on glass from behind — reads correctly from outside |

### Test first

Check **Test connection only** on first use to confirm the cutter responds without cutting.

---

## Linux — serial port permissions

If you get "Permission denied" on the port:

```bash
sudo usermod -aG dialout $USER
# Then log out and back in
```

`setup-extension.py` does this automatically.

---

## Switching PCs at CICF

Full setup on a new machine, under 2 minutes:

```bash
git clone https://github.com/centroinovacaocarlosfiolhais/svg2plotter-inkscape.git
cd svg2plotter-inkscape
python setup-extension.py
# Restart Inkscape
```

---

## Troubleshooting

**Extension not appearing after restart**  
→ Confirm both `.inx` and `.py` are in the folder shown in **Edit → Preferences → System → User extensions**  
→ If using Flatpak, the path is different from the standard one — run `python setup-extension.py`  

**Permission denied on serial port (Linux)**  
→ `sudo usermod -aG dialout $USER` then log out/in  

**Port not found**  
→ Linux: `ls /dev/ttyUSB*` to see available ports  
→ Windows: check Device Manager  

**"No module named serial" (Windows)**  
→ `pip install pyserial` in Command Prompt, then restart Inkscape  

---

## CLI mode (without Inkscape)

```bash
python svg2plotter_cut.py myfile.svg --port /dev/ttyUSB0 --test-only
python svg2plotter_cut.py myfile.svg --port /dev/ttyUSB0
python svg2plotter_cut.py myfile.svg --port /dev/ttyUSB0 --mirror
python svg2plotter_cut.py myfile.svg --port COM5          # Windows
```

---

## Files

```
svg2plotter-inkscape/
├── svg2plotter_cut.inx   # Extension descriptor (menu + UI definition)
├── svg2plotter_cut.py    # Logic (SVG parsing + serial communication)
├── setup-extension.py    # Automated installer
└── README.md
```

---

## Related

- **[SVG2Plotter](https://github.com/centroinovacaocarlosfiolhais/svg2plotter)** — standalone app with layout manager, multi-file support, and LAN network edition

---

## License

**© 2026 David Marques · Centro de Inovação Carlos Fiolhais · CDI Portugal**

[![CC BY-NC-ND 4.0](https://licensebuttons.net/l/by-nc-nd/4.0/88x31.png)](https://creativecommons.org/licenses/by-nc-nd/4.0/)

[Creative Commons Attribution-NonCommercial-NoDerivatives 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) — share with attribution, no commercial use, no derivatives without authorisation.
