import sys, os, math, json, subprocess, functools, importlib.util, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fontTools.ttLib import TTCollection, TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
SPR = os.path.join(HERE, 'sprites')

def _find_ffmpeg():
    import shutil
    if os.environ.get('FFMPEG'): return os.environ['FFMPEG']
    if shutil.which('ffmpeg'): return shutil.which('ffmpeg')
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()
FFMPEG = _find_ffmpeg()
W, H, FPS = 1080, 1920, 30
SR = 24000

# role -> [edge-tts voice, rate, pitch]. Leng = InJoon (male), Chipko = SunHi (female), Blink = Vivienne (female)
VOICES = json.loads(os.environ.get('VOICES', 'null')) or {
    'leng': ['ko-KR-InJoonNeural', '+10%', '+0Hz'],
    'chipko': ['ko-KR-SunHiNeural', '+8%', '+12Hz'],
    'blink': ['fr-FR-VivienneMultilingualNeural', '+5%', '+0Hz'],
}

# ---------- colours ----------
WHITE = (244, 246, 250); MINT = (0, 206, 201); BLUE = (9, 132, 227); CORAL = (255, 140, 148)
GRAY = (160, 170, 182); DARK = (24, 30, 37); INK = (30, 36, 44); GREEN = (46, 204, 113)

# ---------- fonts ----------
SANS = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
MONO = '/System/Library/Fonts/Menlo.ttc'
EMO = '/System/Library/Fonts/Apple Color Emoji.ttc'
ARU = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
WIDX = {'r': 0, 'm': 2, 'sb': 4, 'b': 6, 'xb': 14}
CM_SANS = set(TTCollection(SANS)[14].getBestCmap())
CM_MONO = set(TTCollection(MONO)[1].getBestCmap())
CM_EMO = set(TTCollection(EMO)[0].getBestCmap())

@functools.lru_cache(None)
def font(fam, size, w='b'):
    if fam == 'mono': return ImageFont.truetype(MONO, size, index=1 if w in ('b', 'xb', 'sb') else 0)
    if fam == 'aru': return ImageFont.truetype(ARU, size)
    return ImageFont.truetype(SANS, size, index=WIDX[w])

@functools.lru_cache(None)
def emoji_img(ch, size):
    f = ImageFont.truetype(EMO, 160)
    im = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((100, 100), ch, font=f, embedded_color=True, anchor='mm')
    bb = im.getbbox()
    if bb: im = im.crop(bb)
    s = size / 160 * 1.0
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)

def char_kind(c, fam):
    o = ord(c)
    if fam == 'mono' and o in CM_MONO: return 'mono'
    if o in CM_SANS: return 'sans'
    if o in CM_EMO and o > 0x2000: return 'emo'
    return 'aru'

def parse_rich(text):
    out, hl, buf = [], False, ''
    for c in text.replace('️', ''):
        if c == '*':
            if buf: out.append((buf, hl)); buf = ''
            hl = not hl
        else: buf += c
    if buf: out.append((buf, hl))
    return out

def runs_of(segs, fam):
    runs = []
    for txt, hl in segs:
        cur, kind = '', None
        for c in txt:
            k = char_kind(c, fam)
            if k != kind and cur: runs.append((cur, hl, kind)); cur = ''
            kind = k; cur += c
        if cur: runs.append((cur, hl, kind))
    return runs

def run_w(run, size, w, fam):
    t, hl, k = run
    if k == 'emo': return sum(emoji_img(c, size).width + size * 0.08 for c in t)
    f = font('mono' if k == 'mono' else ('aru' if k == 'aru' else 'sans'), size, w)
    return f.getlength(t)

def wrap_line(segs, size, w, fam, max_w):
    # split rich segs into words, greedy wrap
    words, cur = [], []
    for txt, hl in segs:
        parts = txt.split(' ')
        for i, p in enumerate(parts):
            if i > 0: words.append(cur); cur = []
            if p: cur.append((p, hl))
    words.append(cur)
    lines, line = [], []
    def width(l):
        segs2 = []
        for j, wd in enumerate(l):
            if j: segs2.append((' ', False))
            segs2 += wd
        return sum(run_w(r, size, w, fam) for r in runs_of(segs2, fam)), segs2
    for wd in words:
        trial = line + [wd]
        if line and max_w and width(trial)[0] > max_w:
            lines.append(width(line)[1]); line = [wd]
        else: line = trial
    lines.append(width(line)[1])
    return lines

@functools.lru_cache(4096)
def text_img(text, size, w='b', color=WHITE, hl=MINT, fam='sans', max_w=None, align='center', lh=1.3, stroke=0, stroke_col=(0, 0, 0)):
    lines = []
    for raw in text.split('\n'):
        lines += wrap_line(parse_rich(raw), size, w, fam, max_w)
    lruns = [runs_of(l, fam) for l in lines]
    widths = [sum(run_w(r, size, w, fam) for r in rs) for rs in lruns]
    lhpx = int(size * lh)
    Wd = int(max(widths + [1])) + 8 + stroke * 2
    Hd = lhpx * len(lines) + int(size * 0.35) + stroke * 2
    im = Image.new('RGBA', (Wd, Hd), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, rs in enumerate(lruns):
        x = 4 + stroke + {'center': (Wd - 8 - 2 * stroke - widths[i]) / 2, 'left': 0, 'right': Wd - 8 - 2 * stroke - widths[i]}[align]
        ybase = stroke + i * lhpx + int(size * 1.0)
        for t, h, k in rs:
            col = hl if h else color
            if k == 'emo':
                for c in t:
                    e = emoji_img(c, size)
                    im.alpha_composite(e, (int(x), int(ybase - size * 0.88)))
                    x += e.width + size * 0.08
            else:
                f = font('mono' if k == 'mono' else ('aru' if k == 'aru' else 'sans'), size, w)
                d.text((x, ybase), t, font=f, fill=col, anchor='ls', stroke_width=stroke, stroke_fill=stroke_col)
                x += f.getlength(t)
    return im

# ---------- sprites ----------
@functools.lru_cache(None)
def sprite(name, height):
    im = Image.open(os.path.join(SPR, name + '.png')).convert('RGBA')
    s = height / im.height
    return im.resize((int(im.width * s), height), Image.LANCZOS)

POSE = {'basic': 'leng_basic', 'explain': 'leng_explain', 'surprise': 'leng_surprise', 'think': 'leng_think', 'proud': 'leng_proud', 'point': 'leng_point'}
GUEST_NAME = {'chipko': '칩코 Chipko', 'blink': '깜빡 Blink'}

# ---------- helpers ----------
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def back_out(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def elastic(x):
    x = clamp(x)
    if x in (0, 1): return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi / 3)) + 1

def paste(canvas, im, cx, cy, scale=1.0, alpha=1.0, rot=0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 0.01:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.99:
        a = im.getchannel('A').point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

@functools.lru_cache(512)
def rrect(w, h, r, fill, outline=None, ow=0, shadow=True):
    pad = 40 if shadow else 0
    im = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 14, pad + w, pad + h + 14), r, fill=(0, 0, 0, 110))
        im = sh.filter(ImageFilter.GaussianBlur(16))
    ImageDraw.Draw(im).rounded_rectangle((pad, pad, pad + w, pad + h), r, fill=fill, outline=outline, width=ow)
    return im

@functools.lru_cache(64)
def glow(radius, color, strength=160):
    s = radius * 2
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((s * .3, s * .3, s * .7, s * .7), fill=color + (strength,))
    return im.filter(ImageFilter.GaussianBlur(radius * 0.22))

@functools.lru_cache(8)
def shadow_ell(w):
    im = Image.new('RGBA', (w + 40, 80), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((20, 20, w + 20, 60), fill=(0, 0, 0, 120))
    return im.filter(ImageFilter.GaussianBlur(8))

def character(canvas, name, cx, base_y, h, t, enter=0.0, bob=True, shake=0.0):
    img = sprite(name, h)
    k = back_out((t - enter) / 0.45)
    if t < enter: return
    by = base_y + (math.sin(t * 3.2) * 10 if bob else 0)
    sx = math.sin(t * 60) * shake * max(0, 1 - (t - enter) / 0.6) * 12
    sq = 1 + 0.03 * math.sin(t * 6.4)
    paste(canvas, shadow_ell(int(img.width * 0.6)), cx, base_y + 14, scale=max(0.01, k), alpha=0.8)
    im2 = img.resize((img.width, max(1, int(img.height * sq))), Image.BILINEAR) if bob else img
    paste(canvas, im2, cx + sx, by - im2.height / 2 * k, scale=k)

# ---------- background ----------
@functools.lru_cache(1)
def background():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    a = np.array([27, 52, 74], np.float32); b = np.array([28, 33, 40], np.float32); c = np.array([24, 60, 62], np.float32)
    t1 = clamp_np((x / W * 0.5 + y / H * 0.6))
    col = a[None, None] * (1 - t1[..., None]) + b[None, None] * t1[..., None]
    t2 = clamp_np(((x / W) * 0.5 + (y / H) - 1.0) * 1.6)
    col = col * (1 - t2[..., None]) + c[None, None] * t2[..., None]
    im = Image.fromarray(col.astype(np.uint8), 'RGB').convert('RGBA')
    d = ImageDraw.Draw(im)
    for gx in range(0, W, 60):
        for gy in range(0, H, 60):
            d.point((gx, gy), fill=(255, 255, 255, 18))
    return im

def clamp_np(a): return np.clip(a, 0, 1)

@functools.lru_cache(1)
def logo():
    im = Image.new('RGBA', (110, 110), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((8, 8, 102, 102), outline=MINT, width=9)
    d.ellipse((40, 40, 70, 70), fill=BLUE)
    return im.resize((64, 64), Image.LANCZOS)

CAT_LABEL = {'OS': '운영체제', 'DB': '데이터베이스', 'AI': 'AI', 'DL': '딥러닝', 'NLP': '자연어처리', 'CV': '컴퓨터 비전',
             'BASIC': '프로그래밍 기초', 'WEEKLY': '주간 복습', 'DS': '자료구조', 'ARCH': '컴퓨터 구조', 'SYS': '시스템',
             'NET': '네트워크', 'COMM': '데이터 통신', 'C': 'C 언어', 'SEC': '보안', 'CRYPTO': '암호', 'ALGO': '알고리즘',
             'DISC': '이산수학', 'OOP': '객체지향', 'CG': '그래픽스', 'CLOUD': '클라우드', 'PY': '파이썬'}

def header(canvas, reel, T, total):
    # progress bar (retention cue)
    d = ImageDraw.Draw(canvas)
    d.rectangle((0, 0, W, 10), fill=(255, 255, 255, 30))
    d.rectangle((0, 0, int(W * T / total), 10), fill=MINT)
    canvas.alpha_composite(logo(), (64, 118))
    canvas.alpha_composite(text_img('Lenlab', 50, 'xb'), (140, 116))
    canvas.alpha_composite(text_img('| *CS*', 50, 'xb'), (300, 116))
    num = text_img(f"#{reel['n']:03d}", 44, 'b', color=GRAY)
    canvas.alpha_composite(num, (W - 64 - num.width, 122))
    pill = text_img(f"{CAT_LABEL.get(reel['tag'], reel['tag'])} · 오늘의 1분 지식", 36, 'b')
    bg = rrect(pill.width + 50, 64, 32, BLUE, shadow=False)
    canvas.alpha_composite(bg, (64, 214))
    canvas.alpha_composite(pill, (64 + 25, 214 + 4))

# ---------- subtitles ----------
def chunk_sub(text, maxc=17):
    words = text.split(' ')
    chunks, cur = [], ''
    for w_ in words:
        if cur and len(cur) + 1 + len(w_) > maxc:
            chunks.append(cur); cur = w_
        else: cur = (cur + ' ' + w_).strip()
        if cur.endswith(('!', '?', '.')) and len(cur) > 6:
            chunks.append(cur); cur = ''
    if cur: chunks.append(cur)
    return chunks

def subtitle(canvas, segs, t):
    for st, dur, text, en in segs:
        if st <= t < st + dur + 0.15:
            if en:
                ei = text_img(en, 38, 'sb', color=(190, 236, 234), stroke=5, stroke_col=(10, 14, 18), max_w=940, lh=1.25)
                paste(canvas, ei, W / 2, 1478 + ei.height / 2, alpha=clamp((t - st) / 0.2 + 0.3))
            chunks = chunk_sub(text)
            tot = sum(len(c) for c in chunks)
            acc = st
            for c in chunks:
                cd = dur * len(c) / tot
                if acc <= t < acc + cd or (c is chunks[-1] and t >= acc):
                    im = text_img(c, 58, 'xb', color=WHITE, stroke=7, stroke_col=(10, 14, 18))
                    k = back_out((t - acc) / 0.18)
                    paste(canvas, im, W / 2, 1420, scale=0.85 + 0.15 * k)
                    return
                acc += cd

# ---------- scene renderers ----------
def guest_sprite(reel): return reel['guest'] or 'leng_explain'

def sc_hook(cv, sc, reel, t, dur):
    lines = sc['lines']
    for i, ln in enumerate(lines):
        im = text_img(ln, 96 if i == 0 else 84, 'xb', max_w=960)
        punch = 1 + 0.10 * math.exp(-t * 4) * math.cos(t * 14 + i)
        paste(cv, im, W / 2, 440 + i * 140, scale=punch)
    # burst lines behind leng
    paste(cv, glow(360, MINT, 90), W / 2, 1050, scale=1 + 0.05 * math.sin(t * 5))
    character(cv, 'leng_surprise', W / 2, 1290, 460, t + 0.5, enter=0.0, shake=1.0)
    if True:
        for j in range(8):
            ang = j * math.pi / 4 + t * 0.6
            r0, r1 = 300, 340 + 14 * math.sin(t * 8 + j)
            d = ImageDraw.Draw(cv)
            d.line((W / 2 + r0 * math.cos(ang), 1060 + r0 * math.sin(ang), W / 2 + r1 * math.cos(ang), 1060 + r1 * math.sin(ang)), fill=MINT + (200,), width=8)

def bubble_box(text, who):
    tx = text_img(text, 62, 'b', color=INK, hl=BLUE, max_w=800)
    bw, bh = max(tx.width + 100, 520), tx.height + 80
    box = rrect(bw, bh, 48, (245, 247, 251)).copy()
    pad = 40
    d = ImageDraw.Draw(box)
    tail_x = pad + (140 if who == 'left' else bw - 140)
    d.polygon([(tail_x - 30, pad + bh - 2), (tail_x + 30, pad + bh - 2), (tail_x + (-40 if who == 'left' else 40), pad + bh + 60)], fill=(245, 247, 251))
    box.alpha_composite(tx, (pad + (bw - tx.width) // 2, pad + (bh - tx.height) // 2 + 6))
    return box

def sc_bubble(cv, sc, reel, t, dur):
    who = sc['who']
    name = guest_sprite(reel) if who == 'guest' else POSE[sc.get('pose', 'explain')]
    label = GUEST_NAME.get(reel['guest'], '렝 Leng') if who == 'guest' else '렝 Leng'
    side = 'left' if who == 'guest' else 'right'
    cx = 300 if side == 'left' else W - 330
    character(cv, name, cx, 1290, 430, t, enter=0.0)
    tag = text_img(label, 38, 'b', color=MINT)
    paste(cv, tag, cx, 1330, alpha=clamp(t / 0.3))
    box = bubble_box(sc.get('b', sc['v']), side)
    k = back_out((t - 0.15) / 0.4)
    paste(cv, box, W / 2, 380 + box.height / 2 + (1 - clamp(k)) * 40, scale=0.7 + 0.3 * k, alpha=clamp(k * 2))

@functools.lru_cache(256)
def card_img(e, title, desc, w, h, hl=False):
    im = rrect(w, h, 40, (36, 46, 58), outline=(MINT if hl else (70, 84, 100)), ow=4).copy()
    pad = 40
    cy = pad + 30
    if e:
        em = emoji_img(e.replace('️', '')[0], int(min(120, w * 0.38)))
        im.alpha_composite(em, (pad + (w - em.width) // 2, cy)); cy += em.height + 20
    tt = text_img(title, 54 if w > 400 else 46, 'xb', color=MINT if not hl else WHITE, max_w=w - 40)
    im.alpha_composite(tt, (pad + (w - tt.width) // 2, cy)); cy += tt.height + 6
    if desc:
        dd = text_img(desc, 42 if w > 400 else 36, 'm', color=(215, 222, 230), hl=MINT, max_w=w - 40, lh=1.35)
        im.alpha_composite(dd, (pad + (w - dd.width) // 2, cy))
    return im

def sc_cards(cv, sc, reel, t, dur):
    items = sc['items']; n = len(items)
    if n == 2:
        w, h = 440, 600; pos = [(W / 2 - 240, 690), (W / 2 + 240, 690)]
    elif n == 3:
        w, h = 300, 400 if all(len(i['d']) < 8 for i in items) else 560; pos = [(W / 2 - 330, 640), (W / 2, 640), (W / 2 + 330, 640)]
    else:
        w, h = 430, 330; pos = [(W / 2 - 230, 520), (W / 2 + 230, 520), (W / 2 - 230, 880), (W / 2 + 230, 880)]
    span = min(dur * 0.6, 0.5 * n)
    for i, it in enumerate(items):
        st = i * span / n
        k = back_out((t - st) / 0.45)
        im = card_img(it.get('e', ''), it['t'], it.get('d', ''), w, h)
        x, y = pos[i]
        paste(cv, im, x, y + (1 - clamp(k)) * 120, scale=0.6 + 0.4 * k, alpha=clamp(k * 2))
    if n == 2:
        k = elastic((t - span) / 0.6)
        vs = text_img('VS', 64, 'xb', color=DARK)
        c = Image.new('RGBA', (130, 130), (0, 0, 0, 0)); ImageDraw.Draw(c).ellipse((0, 0, 129, 129), fill=CORAL)
        c.alpha_composite(vs, ((130 - vs.width) // 2, (130 - vs.height) // 2 + 4))
        paste(cv, c, W / 2, 690, scale=max(0.01, k))
    name = guest_sprite(reel) if reel['guest'] else 'leng_explain'
    if n >= 4: character(cv, 'leng_explain', W - 170, 1350, 220, t, enter=0.1)
    else: character(cv, 'leng_explain', W - 200, 1300, 300, t, enter=0.1)

def sc_steps(cv, sc, reel, t, dur):
    items = sc['items']; n = len(items)
    rowh = 116 if n <= 4 else 100
    gap = 28 if n <= 4 else 16
    total_h = n * rowh + (n - 1) * gap
    y0 = 330 + max(0, (760 - total_h) / 2)
    span = dur * 0.75
    for i, it in enumerate(items):
        st = i * span / n
        k = ease_out((t - st) / 0.35)
        if t < st: continue
        tx = text_img(it, 46 if n <= 4 else 42, 'b', max_w=860, align='left')
        box = rrect(960, rowh, 30, (38, 50, 64, 235), outline=(MINT if i == min(n - 1, int(t / (span / n))) else (60, 74, 90)), ow=3, shadow=False).copy()
        box.alpha_composite(tx, (50, (rowh - tx.height) // 2 + 4))
        paste(cv, box, W / 2 + (1 - k) * -200, y0 + i * (rowh + gap) + rowh / 2, alpha=k)
    name = POSE['explain'] if not reel['guest'] else reel['guest']
    if n > 4: character(cv, name, W - 170, 1360, 210, t, enter=0.0)
    else: character(cv, name, W - 210, 1300, 280, t, enter=0.0)

def sc_code(cv, sc, reel, t, dur):
    lines = sc['code'].split('\n')
    tx_full = [text_img(l if l.strip() else ' ', 50, 'b', fam='mono', color=(220, 226, 235), hl=MINT, align='left') for l in lines]
    w = max(860, max(i.width for i in tx_full) + 100)
    w = min(w, 1000)
    h = sum(i.height for i in tx_full) + 150
    panel = rrect(w, h, 34, (14, 20, 26), outline=(60, 74, 90), ow=3).copy()
    d = ImageDraw.Draw(panel)
    for j, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((40 + 40 + j * 40, 40 + 30, 40 + 64 + j * 40, 40 + 54), fill=c)
    k = back_out(t / 0.4)
    y = 40 + 90
    reveal = clamp((t - 0.2) / max(0.6, dur * 0.55)) * len(lines)
    for i, im in enumerate(tx_full):
        if i < reveal:
            panel.alpha_composite(im, (40 + 50, y))
        y += im.height
    if int(t * 2) % 2 == 0 and reveal < len(lines):
        d.rectangle((40 + 50, y - tx_full[-1].height + 10, 40 + 72, y - 8), fill=MINT)
    paste(cv, panel, W / 2, 360 + panel.height / 2, scale=0.8 + 0.2 * k, alpha=clamp(k * 2))
    name = reel['guest'] or 'leng_explain'
    character(cv, name, 220, 1300, 300, t, enter=0.2)

def sc_point(cv, sc, reel, t, dur):
    k = back_out(t / 0.45)
    lab = text_img('💡 핵심 포인트', 44, 'xb', color=DARK)
    pill = rrect(lab.width + 60, 76, 38, MINT, shadow=False).copy(); pill.alpha_composite(lab, (30, 6))
    paste(cv, pill, W / 2, 380, scale=max(0.01, k))
    tx = text_img(sc['text'], 70, 'xb', max_w=880, lh=1.35)
    bw, bh = 980, tx.height + 110
    box = rrect(bw, bh, 44, (30, 42, 54), outline=MINT, ow=5).copy()
    box.alpha_composite(tx, (40 + (bw - tx.width) // 2, 40 + (bh - tx.height) // 2 + 6))
    k2 = back_out((t - 0.15) / 0.45)
    paste(cv, glow(560, MINT, 50 + int(30 * math.sin(t * 4))), W / 2, 460 + bh / 2)
    paste(cv, box, W / 2, 460 + bh / 2, scale=0.7 + 0.3 * k2, alpha=clamp(k2 * 2))
    # leng with glowing antenna
    paste(cv, glow(120, MINT, 180 + int(70 * math.sin(t * 9))), W / 2 - 3, 1300 - 330 * 0.98)
    character(cv, 'leng_basic', W / 2, 1300, 330, t, enter=0.3)

def sc_quiz(cv, sc, reel, t, dur, qa, cd=3.0):
    # phases: question [0,qa), countdown [qa, qa+cd), reveal after
    k = elastic(t / 0.7)
    lab = text_img('QUIZ', 56, 'xb', color=DARK)
    pill = rrect(lab.width + 80, 86, 43, CORAL, shadow=False).copy(); pill.alpha_composite(lab, (40, 10))
    paste(cv, pill, W / 2, 360, scale=max(0.01, k), rot=4 * math.sin(t * 3))
    q = text_img(sc['q'], 66, 'xb', max_w=900, lh=1.3)
    paste(cv, q, W / 2, 470 + q.height / 2, alpha=clamp(t / 0.3))
    reveal = t >= qa + cd
    opts = sc['opts']; ans = sc['ans']
    oy = 520 + q.height + 40
    if opts == ['O', 'X']:
        for i, o in enumerate(opts):
            x = W / 2 + (-210 if i == 0 else 210)
            col = (MINT if i == 0 else CORAL)
            c = Image.new('RGBA', (300, 300), (0, 0, 0, 0)); dd = ImageDraw.Draw(c)
            right = reveal and i == ans
            dim = reveal and i != ans
            dd.ellipse((6, 6, 294, 294), fill=(36, 46, 58), outline=(GREEN if right else (70, 84, 100)), width=10 if right else 4)
            sym = text_img('⭕' if i == 0 else '❌', 150)
            c.alpha_composite(sym, ((300 - sym.width) // 2, (300 - sym.height) // 2 + 8))
            kk = back_out((t - 0.3 - i * 0.12) / 0.4)
            sc_ = (0.6 + 0.4 * kk) * (1 + (0.12 * math.sin((t - qa - cd) * 10) * max(0, 1 - (t - qa - cd)) if right else 0))
            paste(cv, c, x, oy + 150, scale=sc_, alpha=(0.25 if dim else 1) * clamp(kk * 2))
        oy2 = oy + 330
    else:
        rowh = 108
        for i, o in enumerate(opts):
            right = reveal and i == ans; dim = reveal and i != ans
            box = rrect(900, rowh, 30, (46, 120, 90) if right else (36, 46, 58), outline=(GREEN if right else (70, 84, 100)), ow=5 if right else 3, shadow=False).copy()
            tx = text_img(f"{'①②③④'[i]}  {o}", 50, 'b', align='left')
            box.alpha_composite(tx, (50, (rowh - tx.height) // 2 + 4))
            if right:
                ck = text_img('✅', 56); box.alpha_composite(ck, (900 - 100, (rowh - ck.height) // 2 + 4))
            kk = ease_out((t - 0.3 - i * 0.12) / 0.35)
            paste(cv, box, W / 2 + (1 - kk) * 150, oy + i * (rowh + 22) + rowh / 2, alpha=(0.35 if dim else 1) * kk)
        oy2 = oy + len(opts) * (rowh + 22) + 20
    # countdown
    if qa <= t < qa + cd:
        rem = qa + cd - t
        num = int(math.ceil(rem))
        frac = rem - (num - 1)
        c = Image.new('RGBA', (220, 220), (0, 0, 0, 0)); dd = ImageDraw.Draw(c)
        dd.ellipse((10, 10, 210, 210), fill=(20, 26, 32, 230))
        dd.arc((10, 10, 210, 210), -90, -90 + 360 * (rem / cd), fill=CORAL, width=14)
        nm = text_img(str(num), 110, 'xb')
        c.alpha_composite(nm, ((220 - nm.width) // 2, (220 - nm.height) // 2 + 8))
        paste(cv, c, W / 2, min(oy2 + 100, 1160), scale=0.9 + 0.25 * (frac - 0.0) ** 3)
        character(cv, 'leng_think', 170, 1360, 220, t, enter=0.0)
    elif reveal:
        rt = t - qa - cd
        why = text_img('정답! ' + sc['why'], 54, 'xb', color=WHITE, hl=MINT, max_w=900)
        kk = back_out(rt / 0.45)
        paste(cv, why, W / 2, min(oy2 + 45, 1110), scale=0.6 + 0.4 * kk, alpha=clamp(kk * 2))
        character(cv, 'leng_proud', 170, 1360, 210, rt, enter=0.0)
        # confetti
        rng = np.random.default_rng(reel['n'])
        d = ImageDraw.Draw(cv)
        for j in range(40):
            x0 = rng.uniform(0, W); vy = rng.uniform(300, 700); vx = rng.uniform(-120, 120)
            col = [MINT, CORAL, BLUE, (255, 214, 90)][j % 4]
            yy = 250 + vy * rt - 60 * rt * rt * 0 ; xx = x0 + vx * rt
            if yy < H and rt < 2.5:
                s_ = 10 + (j % 3) * 4
                d.rectangle((xx, yy, xx + s_, yy + s_ * 0.6), fill=col)
    else:
        character(cv, 'leng_think', 170, 1360, 220, t, enter=0.0)

def sc_outro(cv, sc, reel, t, dur):
    paste(cv, glow(420, MINT, 80), W / 2, 760)
    character(cv, 'leng_proud', W / 2, 1000, 440, t, enter=0.0)
    if reel['guest']:
        character(cv, reel['guest'], W / 2 + 330, 1000, 260, t, enter=0.25)
    tt = text_img('오늘의 1분 지식 *끝!*', 74, 'xb')
    k = back_out((t - 0.1) / 0.4)
    paste(cv, tt, W / 2, 390, scale=0.6 + 0.4 * k, alpha=clamp(k * 2))
    btns = [('🔖 저장', MINT), ('📤 공유', BLUE), ('➕ 팔로우', CORAL)]
    for i, (lab, col) in enumerate(btns):
        tx = text_img(lab, 42, 'xb', color=DARK if col != BLUE else WHITE)
        b = rrect(280, 96, 48, col, shadow=False).copy(); b.alpha_composite(tx, ((280 - tx.width) // 2, (96 - tx.height) // 2 + 4))
        kk = back_out((t - 0.5 - i * 0.18) / 0.4)
        pulse = 1 + 0.06 * math.sin(t * 7 - i) if t > 1.2 else 1
        paste(cv, b, W / 2 + (i - 1) * 310, 1130, scale=max(0.01, kk) * pulse)
    hd = text_img('@lenlab.cs', 52, 'b', color=GRAY)
    paste(cv, hd, W / 2, 1250, alpha=clamp((t - 0.9) / 0.4))

RENDER = {'hook': sc_hook, 'bubble': sc_bubble, 'cards': sc_cards, 'steps': sc_steps, 'code': sc_code, 'point': sc_point, 'outro': sc_outro}

# ---------- audio ----------
def tts(text, path, rate, pitch=1.0, role='leng'):
    aiff = path + '.aiff'
    if VOICES:
        v, r_, p_ = VOICES[role]
        aiff = path + '.mp3'
        for _try in range(4):
            res = subprocess.run(['edge-tts', '-v', v, f'--rate={r_}', f'--pitch={p_}', '-t', text, '--write-media', aiff], capture_output=True)
            if res.returncode == 0 and os.path.exists(aiff) and os.path.getsize(aiff) > 1000: break
        else: raise RuntimeError('edge-tts failed: ' + text)
        pitch = 1.0
    else:
        subprocess.run(['say', '-v', 'Yuna', '-r', str(rate), '-o', aiff, text], check=True)
    af = 'aresample=24000'
    if pitch != 1.0:
        af = f'asetrate=24000*{pitch},aresample=24000,atempo={1/pitch:.4f}'
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', aiff, '-af', af + ',silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse',
                    '-ac', '1', '-ar', str(SR), '-f', 's16le', path], check=True)
    os.remove(aiff)
    return np.frombuffer(open(path, 'rb').read(), np.int16).astype(np.float32) / 32768

def synth_music(total):
    n = int(total * SR) + SR
    out = np.zeros(n, np.float32)
    bpm = 104; beat = 60 / bpm
    t_ = np.arange(int(SR * beat * 4)) / SR
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    def mtof(m): return 440 * 2 ** ((m - 69) / 12)
    bar = 0; pos = 0
    rng = np.random.default_rng(1)
    while pos < n:
        ch = chords[bar % 4]
        seg = np.zeros_like(t_)
        env = np.minimum(1, t_ / 0.05) * np.exp(-t_ * 0.6)
        for m in ch:
            seg += 0.05 * np.sin(2 * np.pi * mtof(m) * t_) * env
            seg += 0.02 * np.sin(2 * np.pi * mtof(m + 12) * t_) * env
        # bass
        seg += 0.08 * np.sin(2 * np.pi * mtof(ch[0] - 24) * t_) * np.exp(-((t_ % beat)) * 3)
        # kick on 1,3 ; hat on 8ths ; clap on 2,4
        for b in range(4):
            s = int(b * beat * SR)
            if b in (0, 2):
                kt = np.arange(int(0.25 * SR)) / SR
                k = 0.35 * np.sin(2 * np.pi * (50 + 90 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 14)
                seg[s:s + len(k)] += k[:len(seg) - s]
            else:
                ct = np.arange(int(0.18 * SR)) / SR
                c = 0.10 * rng.standard_normal(len(ct)) * np.exp(-ct * 25)
                seg[s:s + len(c)] += c[:len(seg) - s]
            for hh in (0, 0.5):
                s2 = int((b + hh) * beat * SR)
                ht = np.arange(int(0.05 * SR)) / SR
                hsig = 0.03 * rng.standard_normal(len(ht)) * np.exp(-ht * 90)
                hsig = np.diff(np.concatenate([[0], hsig]))
                seg[s2:s2 + len(hsig)] += hsig[:max(0, len(seg) - s2)]
        e = min(n, pos + len(seg)); out[pos:e] += seg[:e - pos]; pos += len(seg); bar += 1
    return out[:int(total * SR)]

def sfx(kind):
    if kind == 'pop':
        t_ = np.arange(int(0.12 * SR)) / SR
        return 0.25 * np.sin(2 * np.pi * (500 + 900 * t_ / 0.12) * t_) * np.exp(-t_ * 30)
    if kind == 'whoosh':
        t_ = np.arange(int(0.45 * SR)) / SR
        nz = np.random.default_rng(2).standard_normal(len(t_))
        env = np.sin(np.pi * t_ / 0.45) ** 2
        return 0.12 * np.convolve(nz, np.ones(12) / 12, 'same') * env
    if kind == 'tick':
        t_ = np.arange(int(0.08 * SR)) / SR
        return 0.25 * np.sin(2 * np.pi * 1400 * t_) * np.exp(-t_ * 60)
    if kind == 'ding':
        t_ = np.arange(int(0.9 * SR)) / SR
        return 0.18 * (np.sin(2 * np.pi * 1318 * t_) + 0.6 * np.sin(2 * np.pi * 1975 * t_)) * np.exp(-t_ * 5)
    return np.zeros(1)

def mixin(buf, sig, t):
    s = int(t * SR); e = min(len(buf), s + len(sig))
    if s < len(buf): buf[s:e] += sig[:e - s]

# ---------- build ----------
def build(reel, outdir, tmp):
    pitch = {'chipko': 1.2, 'blink': 1.1}.get(reel['guest'], 1.0)
    rate = 205
    for attempt in range(3):
        clips = []
        for i, sc in enumerate(reel['scenes']):
            p = 1.0; role = 'leng'
            if sc['t'] == 'bubble' and sc['who'] == 'guest': p = pitch; role = reel['guest']
            a = tts(sc['v'], os.path.join(tmp, f"s{i}a.raw"), rate, p, role)
            b = tts(sc['why_v'], os.path.join(tmp, f"s{i}b.raw"), rate, 1.0, 'leng') if sc['t'] == 'quiz' else None
            clips.append((a, b))
        # timeline
        tl = []; T = 0.0
        for sc, (a, b) in zip(reel['scenes'], clips):
            la = len(a) / SR
            if sc['t'] == 'quiz':
                lb = len(b) / SR
                dur = la + 0.2 + 3.0 + lb + 0.8
                tl.append(dict(sc=sc, st=T, dur=dur, qa=la + 0.2, segs=[(0.0, la, sc['v'], sc.get('en', '')), (la + 3.2, lb, sc['why_v'], sc.get('why_en', ''))], a=a, b=b))
            else:
                pad = {'hook': 0.35, 'outro': 1.2}.get(sc['t'], 0.4)
                lead = 0.0 if sc['t'] == 'hook' else 0.15
                dur = lead + la + pad
                tl.append(dict(sc=sc, st=T, dur=dur, segs=[(lead, la, sc['v'], sc.get('en', ''))], a=a, b=None))
            T += dur
        if T <= 59 or rate >= 250 or VOICES: break
        rate += 20
    total = T
    # audio mix
    buf = np.zeros(int((total + 0.5) * SR), np.float32)
    mus = synth_music(total + 0.5)
    voice = np.zeros_like(buf)
    for e in tl:
        mixin(voice, e['a'], e['st'] + e['segs'][0][0])
        if e['b'] is not None: mixin(voice, e['b'], e['st'] + e['segs'][1][0])
        mixin(buf, sfx('whoosh' if e['sc']['t'] in ('hook', 'point') else 'pop'), e['st'])
        if e['sc']['t'] == 'quiz':
            for k in range(3): mixin(buf, sfx('tick'), e['st'] + e['qa'] + k)
            mixin(buf, sfx('ding'), e['st'] + e['qa'] + 3.0)
    # duck music under voice
    envv = np.convolve(np.abs(voice), np.ones(2400) / 2400, 'same')
    duck = 1 - 0.55 * np.clip(envv * 25, 0, 1)
    buf += voice * 1.0 + mus * 0.55 * duck
    buf = buf / max(1.0, np.abs(buf).max() / 0.95)
    wav = os.path.join(tmp, 'mix.wav')
    with wave.open(wav, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((buf * 32767).astype(np.int16).tobytes())
    # video
    out = os.path.join(outdir, f"{reel['n']:03d}-reel.mp4")
    nframes = int(total * FPS)
    proc = subprocess.Popen([FFMPEG, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                             '-i', wav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
                             '-movflags', '+faststart', '-shortest', out], stdin=subprocess.PIPE)
    bg = background()
    for f in range(nframes):
        T_ = f / FPS
        cv = bg.copy()
        # drifting glow
        paste(cv, glow(500, BLUE, 40), 200 + 120 * math.sin(T_ * 0.3), 600 + 80 * math.cos(T_ * 0.25))
        header(cv, reel, T_, total)
        for e in tl:
            if e['st'] <= T_ < e['st'] + e['dur']:
                lt = T_ - e['st']
                sc = e['sc']
                if sc['t'] == 'quiz': sc_quiz(cv, sc, reel, lt, e['dur'], e['qa'])
                else: RENDER[sc['t']](cv, sc, reel, lt, e['dur'])
                subtitle(cv, e['segs'], lt)
                # scene-in flash
                if lt < 0.12 and e['st'] > 0:
                    ImageDraw.Draw(cv).rectangle((0, 0, W, H), fill=(255, 255, 255, int(60 * (1 - lt / 0.12))))
                break
        proc.stdin.write(cv.convert('RGB').tobytes())
    proc.stdin.close(); proc.wait()
    return out, total

if __name__ == '__main__':
    # usage: python3 reels/render.py posts/<folder> [posts/<folder> ...]
    # reads <folder>/reel.json, writes <folder>/<NNN>-reel.mp4 (30~60s, 1080x1920)
    import tempfile
    for folder in sys.argv[1:]:
        reel = json.load(open(os.path.join(folder, 'reel.json')))
        with tempfile.TemporaryDirectory() as tmp:
            out, total = build(reel, folder, tmp)
        status = 'OK' if 30 <= total <= 60 else 'LENGTH_OUT_OF_RANGE'
        print(f"{status} #{reel['n']:03d} {total:.1f}s {out}", flush=True)
