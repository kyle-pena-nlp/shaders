import os, shutil, json, re, math
from argparse import ArgumentParser
from tqdm import tqdm
from glob import glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import imageio


FONTS = [ "./MontserratMedium-nRxlJ.ttf", "./Infinium Guardian.ttf", "./Echo.ttf", "./ace_futurism.ttf" ]

frames_per_second = 30
fpath = "./planet/planet.mp4"



def _image_number(fp):
    return int(os.path.basename(fp).split(" ")[1])

def _background(fp):
    return os.path.basename(fp).startswith("Background")

def smoothstep(start, end, t):
    if t < start:
        return 0.0
    elif t > end:
        return 1.0
    else:
        t = (t - start) / (end - start)
        #return 3 * (t**2.0) - 2 * (t**3.0) # smoothstep
        return 6*(t**5.0) - 15*(t**4.0) + 10*(t**3.0) # Ken Perlin's smootherstep

def _ensure_ext(fname, ext):
    tokens = fname.split(".")
    if len(tokens) == 1:
        tokens = tokens + [ext]
    elif len(tokens) > 1 and len(tokens[-1]) <= 3:
        tokens[-1] = ext
    else:
        tokens = tokens + [ext]
    return ".".join(tokens)


def do_it(args):
    orig_background = Image.open("planet/Background copy.png").resize((800,800))
    imgs = sorted([ fp for fp in glob(os.path.join("./planet/", "*.png")) if not _background(fp) ], key = lambda x: _image_number(x))
    print(len(imgs))

    fpath = os.path.join("./planet", _ensure_ext(os.path.basename(args.out), "mp4"))

    with imageio.get_writer(fpath, mode='I', fps=frames_per_second, quality = 9)  as w:
        for iter_i, img in tqdm(enumerate(imgs), total = len(imgs)):

            
            principle_i = (iter_i + (len(imgs)//2)) % len(imgs)
            blend_i     = iter_i

            t = iter_i / len(imgs)
            principle_t = principle_i / len(imgs)
            blend_t     = blend_i / len(imgs)

            foreground       = Image.open(imgs[principle_i])
            blend_foreground = Image.open(imgs[blend_i])

            blend_amt = min(smoothstep(0.3, 0.5, t), 1 - smoothstep(0.8, 1.0, t))
            
            
            composited = get_frame(foreground, orig_background, principle_t)
            mirror_frame = get_frame(blend_foreground, orig_background, blend_t)

            composited = Image.blend(composited, mirror_frame, blend_amt)


            w.append_data(np.asarray(composited))

def get_frame(foreground, orig_background, t):
    background = orig_background.copy()
    b = ImageEnhance.Brightness(background)
    background = b.enhance(1.0 + 0.0 * 0.33 * math.sin(2 * t * 2 * math.pi))

    #img = Image.composite(img, background)
    #background.paste(img, (0, 0), img)
    #print(background.size, foreground.size, background.mode, foreground.mode)
    composited = Image.alpha_composite(background, foreground)
    composited = draw_text_with_glow(composited, "TRIPTOGRAMS", 0.15, 100, (225,225,255), t, font_index = 2)
    composited = draw_text_with_glow(composited, args.msg, 0.85, 80, (225,225,255), t, font_index = 3)
    composited = draw_text_with_glow(composited, "12/10/21 @ 5 PM UTC", 0.90, 50, (225,225,255), t, font_index = 3)
    composited = composited.convert("RGB")

    return composited


def draw_centered_text(img, msg, y_frac, font_size, fill, font_index):
    d = ImageDraw.Draw(img)

    fnt = ImageFont.truetype(FONTS[font_index], font_size)

    w, h = d.textsize(msg, font = fnt)
    c = img.size[0] // 2
    x,y = int(c - w/2), (img.size[1] * y_frac) - h/2
    d.text((x, y), msg, font = fnt, fill = fill)  

def draw_text_with_glow(img, msg, y_frac, font_size, fill, t, font_index):
    
    #d = ImageDraw.Draw(img)
    #base = Image.new(img.mode, img.size, color = (0,0,0,0))
    #draw_centered_text(base, msg, y_frac, font_size, fill = (255,255,255,255))

    #glow = base.copy()
    #blur = ImageFilter.GaussianBlur(radius = 15)
    #glow = glow.filter(blur)

    txt = Image.new(img.mode, img.size, color = (0,0,0,0))
    draw_centered_text(txt, msg, y_frac, font_size, fill = (180,255,255,255), font_index = font_index)
    blur = ImageFilter.GaussianBlur(radius = 25)
    txt = txt.filter(blur) 
    draw_centered_text(txt, msg, y_frac, font_size, fill = (180,255,255,255), font_index = font_index)  
    blur = ImageFilter.GaussianBlur(radius = 15)
    txt = txt.filter(blur)   
    draw_centered_text(txt, msg, y_frac, font_size, fill = (255,255,255,255), font_index = font_index)        

    return Image.alpha_composite(img, txt)

    #print(glow.mode, base.mode)

    #return txt #Image.alpha_composite(glow, base)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--out", type = str)
    parser.add_argument("--msg", type = str)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    do_it(args)