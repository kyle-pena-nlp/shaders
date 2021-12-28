import os, shutil, re, json
from argparse import ArgumentParser
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pyselenium import get_writer
import numpy as np
from tqdm import tqdm
from glob import glob
import math
from fbm import FBM
import numpy as np

FONTS = [ "./MontserratMedium-nRxlJ.ttf", "./Infinium Guardian.ttf", "./Echo.ttf", "./ace_futurism.ttf" ]


def get_text_dims(img, msg, y_frac, font_size, fill, font_index):
    d = ImageDraw.Draw(img)

    fnt = ImageFont.truetype(FONTS[font_index], font_size)

    w, h = d.textsize(msg, font = fnt)

    return w,h,d,fnt

def draw_centered_text(img, msg, y_frac, font_size, fill, font_index):
    w,h,d,fnt = get_text_dims(img, msg, y_frac, font_size, fill, font_index)
    c = img.size[0] // 2
    x,y = int(c - w/2), (img.size[1] * y_frac) - h/2
    d.text((x, y), msg, font = fnt, fill = fill)  

def draw_text_after_text(img, msg, postfix, y_frac, font_size, fill, font_index):
    w,h,d,fnt = get_text_dims(img,msg,y_frac,font_size,fill,font_index)
    c = img.size[0]//2
    # let the font decide the kerning by being clever
    kerning = d.textsize(msg + postfix)[0] - (d.textsize(msg)[0] + d.textsize(postfix)[0])
    x,y = int(c + w/2 + kerning), (img.size[1] * y_frac) - h/2
    d.text((x,y), postfix, font = fnt, fill = fill)

def draw_text_with_glow(img, msg, y_frac, font_size, fill, font_index):
    
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
    parser.add_argument("--anim_seconds", default = 5, type = int)
    parser.add_argument("--frames_per_second", default = 30, type = int)
    parser.add_argument("--out", type = str, default = "welcome_to_bonk_world")
    parser.add_argument("--out_format", type = str, default = "mp4")
    parser.add_argument("--seed", type = int , default = 42)
    return parser.parse_args()

def ensure_ext(fname, ext):
    tokens = fname.split(".")
    if len(tokens) == 1:
        tokens = tokens + [ext]
    elif len(tokens) > 1 and len(tokens[-1]) <= 3:
        tokens[-1] = ext
    else:
        tokens = tokens + [ext]
    return ".".join(tokens)

def write_cover(args):

    msg = "INCOMING TRANSMISSION"
    postfix = "..."
    font_size = 50
    font_index = 2
    total_frames = args.frames_per_second * args.anim_seconds
    fill = (255,255,255,255)
    y_frac = 0.5
    click_msg_font_size = 50
    click_msg_frac = 0.5
    click_msg_color = (200,255,200)

    fbms1 = np.clip(FBM(n = total_frames-1, hurst = 0.75, length = 1).fbm(), 0.0, 0.25)
    fbms2 = np.clip(FBM(n = total_frames-1, hurst = 0.75, length = 1).fbm(), 0.0, 0.25)

    with get_writer(frames_per_second = args.frames_per_second, out = os.path.join("./bonkworld_planet_frames", ensure_ext(args.out + ".cover", "gif")), out_format = "gif", compress = False, loop_gif=True) as writer:

        for i in tqdm(range(total_frames), total = total_frames):

            t = i / total_frames

            img = Image.new("RGBA", (800, 800), (0,0,0,255))        
            

            do_ellipses = False
            if (t*args.anim_seconds) % 1.0 < 0.5:
                do_ellipses = True

            do_click_message = False
            if t > 0.50:
                do_click_message = True

            for blur_radius in [30, 15, 5]:

                if not do_click_message:
                    draw_centered_text(img, msg = msg, y_frac = y_frac, font_size = font_size, fill = fill, font_index = font_index)
                    if do_ellipses:
                        draw_text_after_text(img, msg = msg, postfix = postfix, y_frac = y_frac, font_size = font_size, fill = fill, font_index = font_index)

                if do_click_message:
                    draw_centered_text(img, msg = "MESSAGE READY. CLICK TO OPEN.", y_frac = click_msg_frac, font_size = click_msg_font_size, fill = click_msg_color, font_index = font_index)
                
                b = ImageFilter.GaussianBlur(radius = blur_radius)
                img = img.filter(b)

            if not do_click_message:
                draw_centered_text(img, msg = msg, y_frac = y_frac, font_size = font_size, fill = fill, font_index = font_index)
                if do_ellipses:
                    draw_text_after_text(img, msg = msg, postfix = postfix, y_frac = y_frac, font_size = font_size, fill = fill, font_index = font_index)
            
            if do_click_message:
                draw_centered_text(img, msg = "MESSAGE READY. CLICK TO OPEN.", y_frac = click_msg_frac, font_size = click_msg_font_size, fill = click_msg_color, font_index = font_index)

            w1 = abs(1 - 2*t)
            w2 = 1 - w1
            N = len(fbms1)
            blend_amt = w1 * fbms1[(i+N//2)%(N)] + w2 * fbms2[-i]
            img = blend_static(img, blend_amt)

            img = img.convert("RGB").resize((400,400))

            writer.append_data(np.asarray(img))

def fbm_1d(t):
    pass


def blend_static(img, blend_amt):
    #static = Image.new(img.mode, img.size, (0,0,0,0))

    static = Image.fromarray((255*np.random.rand(200,200)).astype(int)).resize((800,800), Image.NEAREST).convert("RGBA")

    return Image.blend(img, static, blend_amt)

def strip_ext(fp):
    return os.path.basename(fp).rsplit(".",1)[0]

def get_bonkworld_planet_frames():
    fps  = [ fp for fp in glob(os.path.join("./bonkworld_planet_frames", "*.png")) if re.match(r"^.*#\d+$", strip_ext(os.path.basename(fp)))]
    print(len(fps))
    fps = sorted(fps, key = lambda x: int(os.path.basename(x).split(" ")[-1].split(".")[0].replace("#", "")) )
    return [ Image.open(fp) for fp in fps ]

def get_bonkworld_logo_no_planet():
    return Image.open("./bonkworld_planet_frames/bonkworld_logo.png")

def add_animation(writer, msg):

    bonk_world_logo_no_planet = get_bonkworld_logo_no_planet()
    planet_frames = get_bonkworld_planet_frames()
    background = Image.open("./bonkworld_planet_frames/Background.png")

    for i, planet_frame in tqdm(enumerate(planet_frames), total = len(planet_frames)):

        t = i / len(planet_frames)

        background_copy = background.copy()

        planet_frame = Image.alpha_composite(background_copy, planet_frame)

        frame = Image.alpha_composite(planet_frame, bonk_world_logo_no_planet)

        txt_img = Image.new("RGBA", frame.size, color = (0,0,0,0))
        draw_centered_text(txt_img, msg, y_frac = 0.85, font_size = 30, fill = (190,255,255), font_index = 1)
        b = ImageFilter.GaussianBlur(10)
        txt_img = txt_img.filter(b)
        draw_centered_text(txt_img, msg, y_frac = 0.85, font_size = 30, fill = (255,255,255), font_index = 1)


        frame = Image.alpha_composite(frame, txt_img)

        writer.append_data(np.asarray(frame))

def write_prompt(args):

    msg = "twitter.com/bonk_world"

    with get_writer(frames_per_second = args.frames_per_second, out = os.path.join("./bonkworld_planet_frames", ensure_ext(args.out + ".animation", "mp4")), out_format = "mp4", compress = False, loop_gif = True) as writer:
        add_animation(writer, msg)
        add_animation(writer, msg)
        add_animation(writer, msg)
        add_animation(writer, msg)

def do_it(args):
    np.random.seed(args.seed)

    #write_cover(args)

    write_prompt(args)

if __name__ == "__main__":
    args = parse_args()
    do_it(args)
