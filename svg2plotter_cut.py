#!/usr/bin/env python3
"""
SVG2Plotter — Inkscape Extension (Direct / Standalone)
────────────────────────────────────────────────────────────────────
Cuts the current Inkscape document directly via serial port.
No network server needed. No extra Python dependencies on Linux.

Serial communication:
  - Linux / macOS : uses termios (Python stdlib) — zero extra deps
  - Windows       : tries pyserial, falls back with install instructions

Centro de Inovação Carlos Fiolhais · CDI Portugal
© 2026 David Marques — Vibe Coding with Claude.ai
CC BY-NC-ND 4.0
"""

import sys
import os
import re
import math
import xml.etree.ElementTree as ET
import time

# ── Inkscape API ──────────────────────────────────────────────────────────────
try:
    import inkex
    from inkex import Effect, Boolean as InkexBool
    HAS_INKEX = True
except ImportError:
    HAS_INKEX = False

# ── Serial backend detection ──────────────────────────────────────────────────
SERIAL_BACKEND = None

def _detect_serial():
    global SERIAL_BACKEND
    # 1. Try pyserial (works everywhere if installed)
    try:
        import serial as _s
        SERIAL_BACKEND = "pyserial"
        return
    except ImportError:
        pass
    # 2. termios — Linux / macOS stdlib
    try:
        import termios, tty
        SERIAL_BACKEND = "termios"
        return
    except ImportError:
        pass
    # 3. Windows without pyserial
    if sys.platform == "win32":
        SERIAL_BACKEND = "win_no_pyserial"
    else:
        SERIAL_BACKEND = "unavailable"

_detect_serial()

HPGL_UNITS_PER_MM = 40

# ═══════════════════════════════════════════════════════════════════════════════
#  SERIAL PORT  (multi-backend)
# ═══════════════════════════════════════════════════════════════════════════════

class SerialPort:
    """
    Thin wrapper — same interface regardless of backend.
    Usage:
        with SerialPort(port, baud) as s:
            s.write(b"IN;\x03")
    """

    def __init__(self, port, baud=9600, timeout=2):
        self.port    = port
        self.baud    = int(baud)
        self.timeout = timeout
        self._fd     = None
        self._ser    = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()

    def open(self):
        if SERIAL_BACKEND == "pyserial":
            import serial
            self._ser = serial.Serial(
                self.port, self.baud, timeout=self.timeout,
                bytesize=8, parity='N', stopbits=1)
            time.sleep(0.5)

        elif SERIAL_BACKEND == "termios":
            import termios, tty
            BAUD_MAP = {
                2400:  termios.B2400,  4800:  termios.B4800,
                9600:  termios.B9600,  19200: termios.B19200,
            }
            baud_const = BAUD_MAP.get(self.baud, termios.B9600)
            self._fd = os.open(self.port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            attrs = termios.tcgetattr(self._fd)
            # Set raw mode
            tty.setraw(self._fd)
            attrs = termios.tcgetattr(self._fd)
            # Input / output speed
            attrs[4] = baud_const   # ispeed
            attrs[5] = baud_const   # ospeed
            # 8N1
            attrs[2] &= ~termios.PARENB
            attrs[2] &= ~termios.CSTOPB
            attrs[2] &= ~termios.CSIZE
            attrs[2] |=  termios.CS8
            attrs[2] |=  termios.CREAD | termios.CLOCAL
            termios.tcsetattr(self._fd, termios.TCSANOW, attrs)
            termios.tcflush(self._fd, termios.TCIOFLUSH)
            time.sleep(0.5)

        elif SERIAL_BACKEND == "win_no_pyserial":
            raise RuntimeError(
                "pyserial is required on Windows.\n"
                "Install it by opening a Command Prompt and running:\n"
                "    pip install pyserial\n"
                "Then restart Inkscape.")

        else:
            raise RuntimeError("No serial backend available on this system.")

    def write(self, data: bytes):
        if self._ser:
            self._ser.write(data)
        elif self._fd is not None:
            os.write(self._fd, data)

    def close(self):
        if self._ser:
            try: self._ser.close()
            except: pass
            self._ser = None
        if self._fd is not None:
            try: os.close(self._fd)
            except: pass
            self._fd = None


def test_connection(port, baud):
    """Open port, send IN; and return (ok, message)."""
    try:
        with SerialPort(port, baud) as s:
            s.write(b"IN;\x03")
            time.sleep(0.3)
        return True, f"Connected: {port} @ {baud} bps"
    except Exception as e:
        return False, str(e)


# ═══════════════════════════════════════════════════════════════════════════════
#  SVG PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

def _mat_mul(a, b):
    return [
        a[0]*b[0]+a[2]*b[1], a[1]*b[0]+a[3]*b[1],
        a[0]*b[2]+a[2]*b[3], a[1]*b[2]+a[3]*b[3],
        a[0]*b[4]+a[2]*b[5]+a[4], a[1]*b[4]+a[3]*b[5]+a[5],
    ]

def _parse_transform(t):
    if not t: return [1,0,0,1,0,0]
    m = [1,0,0,1,0,0]
    for fn, args_str in re.findall(r'(\w+)\s*\(([^)]*)\)', t):
        try: a = [float(v) for v in re.split(r'[\s,]+', args_str.strip()) if v]
        except: continue
        if   fn=='matrix'    and len(a)>=6: t2=a[:6]
        elif fn=='translate': tx,ty=a[0],(a[1] if len(a)>1 else 0); t2=[1,0,0,1,tx,ty]
        elif fn=='scale':     sx,sy=a[0],(a[1] if len(a)>1 else a[0]); t2=[sx,0,0,sy,0,0]
        elif fn=='rotate':
            ang=math.radians(a[0]); ca,sa=math.cos(ang),math.sin(ang)
            if len(a)==3: cx,cy=a[1],a[2]; t2=[ca,sa,-sa,ca,cx*(1-ca)+cy*sa,cy*(1-ca)-cx*sa]
            else: t2=[ca,sa,-sa,ca,0,0]
        elif fn=='skewX': t2=[1,0,math.tan(math.radians(a[0])),1,0,0]
        elif fn=='skewY': t2=[1,math.tan(math.radians(a[0])),0,1,0,0]
        else: continue
        m=_mat_mul(m,t2)
    return m

def _tf(m, x, y):
    return (m[0]*x+m[2]*y+m[4], m[1]*x+m[3]*y+m[5])

def _parse_dim(val, default=100.0):
    if not val: return default
    val = str(val).strip()
    for s,f in [('mm',1),('cm',10),('in',25.4),('px',25.4/96),('pt',25.4/72)]:
        if val.endswith(s):
            try: return float(val[:-len(s)])*f
            except: return default
    try: return float(val)*(25.4/96)
    except: return default

def _get_svg_size(root):
    vb = root.get('viewBox')
    if vb:
        v = [float(x) for x in re.split(r'[\s,]+', vb.strip())]
        vw, vh = v[2], v[3]
    else:
        vw, vh = None, None
    wa, ha = root.get('width'), root.get('height')
    if wa and ha:
        wm, hm = _parse_dim(wa), _parse_dim(ha)
        if vw is None: vw, vh = wm, hm
    elif vw is not None:
        px = 25.4/96
        if wa:   wm=_parse_dim(wa); hm=vh*(wm/vw)
        elif ha: hm=_parse_dim(ha); wm=vw*(hm/vh)
        else:    wm=vw*px;          hm=vh*px
    else:
        wm,hm,vw,vh = 100.0,100.0,100.0,100.0
    return wm, hm, vw, vh

def _extract_paths(root):
    polylines = []

    def sn(tag): return tag.split('}')[-1] if '}' in tag else tag
    def add(pts):
        if len(pts) >= 2: polylines.append(list(pts))

    def path_pts(d, m):
        toks = re.findall(
            r'[MmLlHhVvCcSsQqTtAaZz]|[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', d)
        i=0; cx=cy=sx=sy=0.0; cur=[]; lc=None

        def flush():
            nonlocal cur; add(cur); cur=[]
        def move(x,y):
            nonlocal cx,cy,sx,sy,cur
            if cur: flush()
            cx,cy=x,y; sx,sy=x,y; cur=[_tf(m,cx,cy)]
        def lineto(x,y):
            nonlocal cx,cy; cx,cy=x,y; cur.append(_tf(m,cx,cy))

        while i < len(toks):
            t=toks[i]
            if re.match(r'[MmLlHhVvCcSsQqTtAaZz]', t): cmd=t; lc=t; i+=1
            else: cmd=lc
            try:
                if   cmd=='M': move(float(toks[i]),float(toks[i+1])); i+=2; lc='L'
                elif cmd=='m': move(cx+float(toks[i]),cy+float(toks[i+1])); i+=2; lc='l'
                elif cmd=='L': lineto(float(toks[i]),float(toks[i+1])); i+=2
                elif cmd=='l': lineto(cx+float(toks[i]),cy+float(toks[i+1])); i+=2
                elif cmd=='H': lineto(float(toks[i]),cy); i+=1
                elif cmd=='h': lineto(cx+float(toks[i]),cy); i+=1
                elif cmd=='V': lineto(cx,float(toks[i])); i+=1
                elif cmd=='v': lineto(cx,cy+float(toks[i])); i+=1
                elif cmd in('Z','z'): lineto(sx,sy); flush()
                elif cmd in('C','c'):
                    p=[float(toks[i+j]) for j in range(6)]; i+=6
                    if cmd=='c': p=[cx+p[0],cy+p[1],cx+p[2],cy+p[3],cx+p[4],cy+p[5]]
                    for tv in [.2,.4,.6,.8,1.0]:
                        lineto((1-tv)**3*cx+3*(1-tv)**2*tv*p[0]+3*(1-tv)*tv**2*p[2]+tv**3*p[4],
                               (1-tv)**3*cy+3*(1-tv)**2*tv*p[1]+3*(1-tv)*tv**2*p[3]+tv**3*p[5])
                    cx,cy=p[4],p[5]
                elif cmd in('Q','q'):
                    p=[float(toks[i+j]) for j in range(4)]; i+=4
                    if cmd=='q': p=[cx+p[0],cy+p[1],cx+p[2],cy+p[3]]
                    for tv in [.33,.66,1.0]:
                        lineto((1-tv)**2*cx+2*(1-tv)*tv*p[0]+tv**2*p[2],
                               (1-tv)**2*cy+2*(1-tv)*tv*p[1]+tv**2*p[3])
                    cx,cy=p[2],p[3]
                elif cmd in('S','s'):
                    p=[float(toks[i+j]) for j in range(4)]; i+=4
                    if cmd=='s': p=[cx+p[0],cy+p[1],cx+p[2],cy+p[3]]
                    lineto(p[2],p[3]); cx,cy=p[2],p[3]
                elif cmd in('T','t'):
                    ex,ey=float(toks[i]),float(toks[i+1]); i+=2
                    if cmd=='t': ex,ey=cx+ex,cy+ey
                    lineto(ex,ey); cx,cy=ex,ey
                elif cmd in('A','a'):
                    p=[float(toks[i+j]) for j in range(7)]; i+=7
                    ex,ey=(cx+p[5],cy+p[6]) if cmd=='a' else (p[5],p[6])
                    for s in range(1,9): lineto(cx+(ex-cx)*s/8, cy+(ey-cy)*s/8)
                    cx,cy=ex,ey
                else: i+=1
            except (IndexError, ValueError): i+=1
        if cur: flush()

    def traverse(elem, pm=None):
        if pm is None: pm=[1,0,0,1,0,0]
        lm = _parse_transform(elem.get('transform',''))
        m  = _mat_mul(pm, lm)
        tag = sn(elem.tag)

        if tag=='rect':
            x,y=float(elem.get('x',0)),float(elem.get('y',0))
            w,h=float(elem.get('width',0)),float(elem.get('height',0))
            if w>0 and h>0:
                add([_tf(m,x,y),_tf(m,x+w,y),_tf(m,x+w,y+h),_tf(m,x,y+h),_tf(m,x,y)])
        elif tag=='circle':
            cx,cy,r=float(elem.get('cx',0)),float(elem.get('cy',0)),float(elem.get('r',0))
            if r>0:
                n=max(36,int(r*2))
                add([_tf(m,cx+r*math.cos(2*math.pi*s/n),cy+r*math.sin(2*math.pi*s/n))
                     for s in range(n+1)])
        elif tag=='ellipse':
            cx,cy=float(elem.get('cx',0)),float(elem.get('cy',0))
            rx,ry=float(elem.get('rx',0)),float(elem.get('ry',0))
            if rx>0 and ry>0:
                add([_tf(m,cx+rx*math.cos(2*math.pi*s/48),cy+ry*math.sin(2*math.pi*s/48))
                     for s in range(49)])
        elif tag=='line':
            add([_tf(m,float(elem.get('x1',0)),float(elem.get('y1',0))),
                 _tf(m,float(elem.get('x2',0)),float(elem.get('y2',0)))])
        elif tag in('polyline','polygon'):
            ns=[float(v) for v in re.findall(
                r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', elem.get('points',''))]
            pts=[_tf(m,ns[i],ns[i+1]) for i in range(0,len(ns)-1,2)]
            if tag=='polygon' and pts: pts.append(pts[0])
            add(pts)
        elif tag=='path':
            d=elem.get('d','')
            if d: path_pts(d, m)
        if tag != 'defs':
            for child in elem: traverse(child, m)

    traverse(root)
    return polylines


def svg_to_hpgl(svg_file, mirror=False):
    """Parse SVG file and return list of HPGL command strings."""
    tree = ET.parse(svg_file)
    root = tree.getroot()
    wm, hm, vw, vh = _get_svg_size(root)

    sx = (wm/vw) * HPGL_UNITS_PER_MM
    sy = (hm/vh) * HPGL_UNITS_PER_MM

    if mirror:
        def hx(x): return int(float(x)*sx)
    else:
        def hx(x): return int((vw-float(x))*sx)
    def hy(y): return int((vh-float(y))*sy)

    cmds  = ['IN;', 'SP1;']
    polys = _extract_paths(root)

    for poly in polys:
        if len(poly) < 2: continue
        cmds.append(f'PU{hy(poly[0][1])},{hx(poly[0][0])};')
        cmds.append(f'PD{",".join(f"{hy(y)},{hx(x)}" for x,y in poly[1:])};')
        cmds.append('PU;')

    cmds.append('SP0;')
    return cmds, len(polys), wm, hm


# ═══════════════════════════════════════════════════════════════════════════════
#  CUT JOB
# ═══════════════════════════════════════════════════════════════════════════════

def run_cut(svg_file, port, baud, mirror, test_only):
    """
    Main entry point.
    Returns (success: bool, lines: list[str])
    """
    log = []

    if test_only:
        ok, msg = test_connection(port, baud)
        if ok:
            return True,  [f"✓ Connection OK — {msg}",
                           f"  Backend: {SERIAL_BACKEND}"]
        else:
            return False, [f"✗ Connection FAILED", f"  {msg}",
                           "", "Check port and baud rate."]

    # Parse SVG
    try:
        cmds, n_paths, wm, hm = svg_to_hpgl(svg_file, mirror=mirror)
    except Exception as e:
        return False, [f"✗ SVG parse error: {e}"]

    mode = "MIRROR" if mirror else "NORMAL"
    log.append(f"SVG2Plotter — Direct Cut")
    log.append(f"Mode:   {mode}")
    log.append(f"Size:   {wm:.1f} × {hm:.1f} mm")
    log.append(f"Paths:  {n_paths}")
    log.append(f"Port:   {port} @ {baud} bps")
    log.append(f"Cmds:   {len(cmds)}")
    log.append("")

    # Send
    try:
        with SerialPort(port, baud) as s:
            for i, cmd in enumerate(cmds):
                s.write((cmd + '\x03').encode('ascii'))
                time.sleep(0.015)
        log.append("✓ Cut job sent successfully.")
        return True, log
    except Exception as e:
        log.append(f"✗ Serial error: {e}")
        if SERIAL_BACKEND == "termios" and "Permission" in str(e):
            log += [
                "",
                "Permission denied on serial port.",
                "Fix with:",
                f"  sudo usermod -aG dialout $USER",
                "Then log out and back in.",
            ]
        return False, log


# ═══════════════════════════════════════════════════════════════════════════════
#  INKSCAPE EFFECT
# ═══════════════════════════════════════════════════════════════════════════════

if HAS_INKEX:

    class SVG2PlotterCut(Effect):

        def __init__(self):
            super().__init__()
            self.arg_parser.add_argument("--port",      type=str,       default="/dev/ttyUSB0")
            self.arg_parser.add_argument("--baud",      type=int,       default=9600)
            self.arg_parser.add_argument("--mirror",    type=InkexBool, default=False)
            self.arg_parser.add_argument("--test_only", type=InkexBool, default=False)

        def effect(self):
            port      = self.options.port.strip()
            baud      = int(self.options.baud)
            mirror    = self.options.mirror
            test_only = self.options.test_only
            svg_file  = self.options.input_file

            success, lines = run_cut(svg_file, port, baud, mirror, test_only)
            msg = "\n".join(lines)

            if success:
                inkex.utils.debug(msg)
            else:
                inkex.errormsg(msg)

    if __name__ == "__main__":
        SVG2PlotterCut().run()

# ═══════════════════════════════════════════════════════════════════════════════
#  CLI (standalone test without Inkscape)
# ═══════════════════════════════════════════════════════════════════════════════

else:
    if __name__ == "__main__":
        import argparse

        p = argparse.ArgumentParser(description="SVG2Plotter — direct cut CLI")
        p.add_argument("svg_file")
        p.add_argument("--port",      default="/dev/ttyUSB0")
        p.add_argument("--baud",      type=int, default=9600)
        p.add_argument("--mirror",    action="store_true")
        p.add_argument("--test-only", action="store_true", dest="test_only")

        args = p.parse_args()

        if not os.path.exists(args.svg_file):
            print(f"Error: {args.svg_file} not found"); sys.exit(1)

        ok, lines = run_cut(
            args.svg_file, args.port, args.baud,
            args.mirror, args.test_only)

        for line in lines: print(line)
        sys.exit(0 if ok else 1)
