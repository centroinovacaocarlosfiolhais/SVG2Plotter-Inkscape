# ✂ SVG2Plotter — Inkscape Extension

**Cut directly from Inkscape. No server. No network.**  
_Extensions → Export → Send to SVG2Plotter_

> Developed by **David Marques** — *Vibe Coding with Claude.ai*  
> Centro de Inovação Carlos Fiolhais · CDI Portugal

---

## What is this?

An Inkscape extension that sends the current document directly to an HPGL vinyl cutter via USB-Serial — no intermediate server, no extra software running in the background.

Open your design in Inkscape, click **Extensions → Export → Send to SVG2Plotter**, choose Normal or Mirror, click Apply. Done.

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

| OS | Serial backend | Extra install needed? |
|---|---|---|
| **Linux / Linux Mint** | `termios` (Python stdlib) | **None** |
| **macOS** | `termios` (Python stdlib) | **None** |
| **Windows** | `pyserial` | `pip install pyserial` |

On Linux and macOS the extension works out of the box.  
On Windows, run `python setup-extension.py` once to install pyserial.

---

## Installation

### Step 1 — Install the extension in Inkscape

1. Open Inkscape
2. Go to **Extensions → Manage Extensions...**
3. Click **Install from file...**
4. Select `svg2plotter-inkscape-direct.zip`
5. Restart Inkscape

The extension appears at **Extensions → Export → Send to SVG2Plotter**.

### Step 2 — Install dependencies (Windows only)

```bash
python setup-extension.py
```

On Linux and macOS this step is not needed.

---

## Usage

1. Draw or open your design in Inkscape
2. Plug in the vinyl cutter via USB
3. Go to **Extensions → Export → Send to SVG2Plotter**
4. Set the serial port and options:

| Field | Linux default | Windows default |
|---|---|---|
| Serial port | `/dev/ttyUSB0` | `COM5` |
| Baud rate | `9600` | `9600` |
| Mirror mode | off | off |
| Test only | off | off |

5. Click **Apply**

### Cut modes

| Mode | Use case |
|---|---|
| **Normal** | Vinyl applied to opaque surfaces — cars, walls, signs |
| **Mirror** | Vinyl applied to glass or windows from behind — reads correctly from outside |

### Test connection

Check **Test connection only** before cutting to confirm the cutter is responding without sending a job.

---

## Switching PCs (CICF workflow)

When moving to a new computer:

1. **Extensions → Manage Extensions → Install from file...** → select the ZIP
2. Restart Inkscape
3. On Linux: done. On Windows: run `python setup-extension.py` once.

That's it. The cutter port (`/dev/ttyUSB0` or `COM5`) is remembered per-session in the extension dialog.

---

## Linux — Serial port permissions

On first use the port may refuse access. Fix it once:

```bash
sudo usermod -aG dialout $USER
# Log out and back in for the change to take effect
```

Or run `python setup-extension.py` — it handles this automatically.

---

## File structure

```
svg2plotter-inkscape/
├── svg2plotter_cut.inx     # Inkscape extension descriptor (UI definition)
├── svg2plotter_cut.py      # Extension logic (SVG parsing + serial communication)
├── setup-extension.py      # Dependency installer
└── README.md
```

To install manually (without the ZIP), copy `svg2plotter_cut.inx` and `svg2plotter_cut.py` to your Inkscape extensions folder:

| OS | Folder |
|---|---|
| Linux | `~/.config/inkscape/extensions/` |
| macOS | `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/` |
| Windows | `%APPDATA%\inkscape\extensions\` |

---

## CLI mode (testing without Inkscape)

```bash
# Test connection
python svg2plotter_cut.py myfile.svg --port /dev/ttyUSB0 --test-only

# Cut — normal mode
python svg2plotter_cut.py myfile.svg --port /dev/ttyUSB0

# Cut — mirror mode
python svg2plotter_cut.py myfile.svg --port /dev/ttyUSB0 --mirror

# Windows
python svg2plotter_cut.py myfile.svg --port COM5
```

---

## HPGL / SK1350 notes

- Axis mapping: HPGL X → cutter head · HPGL Y → vinyl feed
- Units: 1 mm = 40 HPGL units
- Command terminator: `\x03` (ETX — required by SK1350, may differ on other machines)
- Compatible with any HPGL cutter over serial, not just the SK1350

---

## Related projects

- **[SVG2Plotter Desktop](https://github.com/centroinovacaocarlosfiolhais/svg2plotter)** — standalone Python/tkinter app with full layout manager, multi-file support, and network edition

---

## License

**© 2026 David Marques · Centro de Inovação Carlos Fiolhais · CDI Portugal**

[![CC BY-NC-ND 4.0](https://licensebuttons.net/l/by-nc-nd/4.0/88x31.png)](https://creativecommons.org/licenses/by-nc-nd/4.0/)

Licensed under [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International](https://creativecommons.org/licenses/by-nc-nd/4.0/).  
Share with attribution. No commercial use. No derivatives without written authorisation.
