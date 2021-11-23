from argparse import ArgumentParser
import os, re
from glob import glob
from tqdm import tqdm
from pyselenium import get_writer, export
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import multiprocessing

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--shader", type = str, default= "triptograms")
    parser.add_argument("--fps", type = int, default = 2)
    return parser.parse_args()



def get_image_number(trait_filepath):
    return int(os.path.basename(trait_filepath).split(".")[0])

def to_url(fpath):
    return "file:///" + os.path.abspath(fpath)    

def get_temp_png_fpath(image_number):
    return "{}.temp.png".format(image_number)    

def yield_1_fps_png_frames(args, image_number):
    out_fpath = os.path.join(args.shader, get_temp_png_fpath(image_number))
    html_fpath = os.path.join(args.shader, "{}.html".format(image_number))
    png_fpath = os.path.join(args.shader, "{}.png".format(image_number))
    x,y = Image.open(png_fpath).size # rumour has it, Image.open is lazy and doesn't actually load all the image data
    url = to_url(html_fpath)
    export(url, x, y, frames_per_second = args.fps, num_seconds = 10, out = out_fpath, out_format = "png", compress = False)
    with Image.open(out_fpath) as img:
        for i in range(img.n_frames):
            img.seek(i)
            yield np.asarray(img)

def make_gif_frame(np_frame, image_number):
    img = Image.fromarray(np_frame)
    frosted_reverse_mask = make_text_reverse_mask(img, image_number, 0.10)
    opaque_reverse_mask  = make_text_reverse_mask(img, image_number, 0.00)
    cover_color = make_blank_image_like(img, (25,25,25))
    frosted = Image.composite(img, cover_color, frosted_reverse_mask)
    whitened_img = Image.blend(make_blank_image_like(img, (255,255,255)), img, 0.25)
    opaque = Image.composite(whitened_img, cover_color, opaque_reverse_mask)
    gaussian_filter = ImageFilter.GaussianBlur(radius = 5)
    glow = opaque.filter(gaussian_filter)
    opaque = Image.blend(opaque, glow, 0.5)
    left = 0
    right = img.size[0]
    upper = int(0.3 * img.size[1])
    lower = int(0.65 * img.size[1])
    box = [left,upper,right,lower]
    frosted.paste(opaque.crop(box), box)
    return frosted.resize((250,250))

def make_blank_image_like(img, color):
    blank_img = img.copy()
    blank_img.paste( color, [0,0,blank_img.size[0],blank_img.size[1]])
    return blank_img

def make_text_reverse_mask(img, image_number, pct_transparency):
    p = int(255*pct_transparency)
    mask_img = make_blank_image_like(img, color = (p,p,p)).convert("L")
    draw_text_at_y_pct(mask_img, "TRIPTOGRAM", 55, 255, 0.4)
    draw_text_at_y_pct(mask_img, "#{:03}".format(image_number+1), 60, 255, 0.53)
    return mask_img

def draw_text_at_y_pct(img, msg, font_size, fill, y_pct):
    d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype("./MontserratMedium-nRxlJ.ttf", font_size)
    w, h = d.textsize(msg, font = fnt)
    c = img.size[0] // 2
    x,y = int(c - w/2), (img.size[1] * y_pct) - (h/2)
    d.text((x, y), msg, font = fnt, fill = fill)      

def execute(params):
    args, trait_file = params
    image_number = get_image_number(trait_file)
    out_fpath = os.path.join(args.shader, "{}.cover.gif".format(image_number))
    with get_writer(frames_per_second = args.fps, out = out_fpath, out_format = "gif", compress = False) as gif_writer:
        frames = list(yield_1_fps_png_frames(args, image_number))
        os.remove(os.path.join(args.shader, get_temp_png_fpath(image_number)))
        for np_frame in frames:
            gif_frame = make_gif_frame(np_frame, image_number)
            gif_writer.append_data(np.asarray(gif_frame))
    return True
        

def do_it(args):
    params = [ (args,fp) for fp in glob(os.path.join(args.shader, "*.traits")) if re.match(r"\d+\.traits", os.path.basename(fp)) ] 
    pool = multiprocessing.Pool()
    for _ in (pool.map(execute, params)):
        pass

if __name__ == "__main__":
    args = parse_args()
    do_it(args)


