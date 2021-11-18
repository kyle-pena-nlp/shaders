import os
import random
import math
from argparse import ArgumentParser
import numpy as np
from tqdm import tqdm
import imageio
from PIL import Image, ImageFont, ImageDraw
from PIL.ImageDraw import Draw
from pyselenium import get_writer
import matplotlib.pyplot as plt
from common import ensure_ext


def get_img_paths(args):
    img_fpaths = [ os.path.join(args.shader, "{}.png".format(idx)) for idx in range(args.image_range[0], args.image_range[1] + 1) ]
    random.shuffle(img_fpaths)
    return img_fpaths

def make_black_img(img):
    black_img = img.copy()
    black_img.paste( (0,0,0), [0,0,black_img.size[0],black_img.size[1]])
    return black_img

def make_white_img(img):
    white_img = img.copy()
    white_img.paste( (255,255,255), [0,0,white_img.size[0],white_img.size[1]])
    return white_img  

def get_reverse_mask_img(args, img):

    msg = args.shader.upper()

    black_img = make_black_img(img)

    mask_img = Image.new('L', img.size)
    
    draw_centered_text(mask_img, msg, 51, 255)

    return Image.composite(img, black_img, mask_img)

def draw_centered_text(img, msg, font_size, fill):
    d = ImageDraw.Draw(img)
    
    fnt = ImageFont.truetype("./MontserratMedium-nRxlJ.ttf", font_size)

    w, h = d.textsize(msg, font = fnt)
    c = img.size[0] // 2
    x,y = int(c - w/2), (img.size[1] * 0.5) - h/2
    d.text((x, y), msg, font = fnt, fill = fill)  

def add_text_msg(args, writer, dims, msg, duration_seconds, font_size):

    frames = max(1,int(args.fps * duration_seconds))

    background = Image.new("RGBA", dims, color = (255,255,255,255))
    
    draw_centered_text(background, msg, font_size, 0)

    for i in range(frames):
        writer.append_data(np.asarray(background))



def do_it(args):

    random.seed(args.seed)
    img_fpaths = get_img_paths(args)
    total_frames = args.anim_seconds * args.fps
    out = ensure_ext(os.path.join(args.shader + "_promo", args.out),  "mp4")

    with get_writer(frames_per_second = args.fps, out = out, out_format = "mp4", compress = False) as writer:

        img_seq_no = 0
        current_frame = 0

        progress = tqdm(total = total_frames)

        #add_text_msg(args, writer, (400,400), "About that 11/12 mint...", 2, 25)
        #add_text_msg(args, writer, (400,400), "Gate.io locked our account for 'Security Reasons'...", 2, 15)
        #add_text_msg(args, writer, (400,400), "Until our account is unlocked we can't mint.", 2, 15)
        #add_text_msg(args, writer, (400,400), "They won't tell us *when* or *if* it will unlock :(", 2, 15)
        #add_text_msg(args, writer, (400,400), "If you're mad like we are...", 2, 30)
        #add_text_msg(args, writer, (400,400), "Tell gate.io", 2, 40)
        #add_text_msg(args, writer, (400,400), "erm...", 2, 25)
        #add_text_msg(args, writer, (400,400), "Look at this!", 0.5, 25)

        while current_frame < total_frames: 
            
            t_frac = (current_frame/total_frames)
            frame_duration_in_seconds = args.starting_frame_duration_seconds - (smoothstep(0, 1, t_frac)) * (args.starting_frame_duration_seconds - args.ending_frame_duration_seconds)
            frame_duration = max(1,int(frame_duration_in_seconds * args.fps))

            frame_duration = min(frame_duration, total_frames - (current_frame))

            current_img_fpath = img_fpaths[img_seq_no]
            current_img = Image.open(current_img_fpath)
            

            for i in range(frame_duration):
                frame = (current_frame + i) % current_img.n_frames
                current_img.seek(frame)

                t = current_frame

                fade_t0 = 0.75 * total_frames
                fade_t1 = 1.00 * total_frames
                fade_blend_amt = smoothstep(fade_t0, fade_t1, t)
                faded_img = Image.blend(current_img, make_white_img(current_img), fade_blend_amt)

                text_t0 = 0.25 * total_frames
                text_t1 = 0.40 * total_frames
                
                text_blend_amt = smoothstep(text_t0, text_t1, t)
                reverse_mask_img = get_reverse_mask_img(args, faded_img)
                composited_img = Image.blend(faded_img, reverse_mask_img, text_blend_amt)

                fadeout_t0 = 0.90 * total_frames
                fadeout_t1 = 1.00 * total_frames
                fadeout_blend_amt = smoothstep(fadeout_t0, fadeout_t1, t)
                final_img = Image.blend(composited_img, make_white_img(current_img), fadeout_blend_amt)

                writer.append_data(np.asarray(final_img))
            
            current_frame += frame_duration
            img_seq_no += 1
            progress.update(frame_duration)
        
        add_text_msg(args, writer, current_img.size, "MINTING SOON", 2, 40)
        #add_text_msg(args, writer, current_img.size, "MINTING 11/??/21", 2, 40)
        #add_text_msg(args, writer, current_img.size, "0.5 SOL", 2, 51)
        #add_text_msg(args, writer, current_img.size, "probably nothing...", 1, 30)
        #add_text_msg(args, writer, current_img.size, ";)", 0.10, 30)
        #add_text_msg(args, writer, current_img.size, ":o", 0.10, 30)

        progress.close()

    print("Done.")

def smoothstep(start, end, t):
    if t < start:
        return 0.0
    elif t > end:
        return 1.0
    else:
        t = (t - start) / (end - start)
        #return 3 * (t**2.0) - 2 * (t**3.0) # smoothstep
        return 6*(t**5.0) - 15*(t**4.0) + 10*(t**3.0) # Ken Perlin's smootherstep

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--shader", type = str, default = "triptograms")
    parser.add_argument("--out", type = str)
    parser.add_argument("--anim_seconds", type = int, default = 10)
    parser.add_argument("--seed", type = int, default = 42)
    parser.add_argument("--image_range", nargs = 2, type = int, default = [0,999])
    parser.add_argument("--fps", type = int, default = 30)
    parser.add_argument("--dims", type = int, nargs = 2, default = [600,600])
    parser.add_argument("--starting_frame_duration_seconds", type = float, default = (1/1))
    parser.add_argument("--ending_frame_duration_seconds", type = float, default = (1/30))
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    do_it(args)