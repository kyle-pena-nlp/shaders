import os
from argparse import ArgumentParser
import numpy as np
import random
from PIL import Image
from PIL import ImageChops
from pyselenium import get_writer
from tqdm import tqdm
import matplotlib.pyplot as plt
from PIL import ImageDraw, ImageFont
import math

DEBUG = False


def create_promo_animation(args):

    out = os.path.join(args.dir, "PROMO1.mp4")

    fn_grid = fill_image_fn_grid(args)    
    image_holder = {}

    image_dims = args.image_dims + [3]
    promo_image = Image.fromarray(np.zeros(image_dims, dtype=int), mode = "RGB")
    fade_color = Image.fromarray(np.zeros(image_dims, dtype=int), mode = "RGB")


    with get_writer(frames_per_second = args.fps, out = out, out_format = "mp4", compress = False) as writer:

        images_holder = {}
        for t in tqdm(np.linspace(0, args.anim_seconds, num = args.anim_seconds * args.fps)):
            worldspace_viewport = get_viewport(args, t)
            images_holder = request_images(images_holder, worldspace_viewport, fn_grid)
            fill_promo_image(args, images_holder, promo_image, worldspace_viewport, t)

            #paint_text(promo_image, t)
            promo_image = create_fade(args, promo_image, fade_color, t)

            if DEBUG:
                plt.imshow(promo_image)
                plt.show()
                break

            writer.append_data(np.asarray(promo_image))

# https://www.fontspace.com/collection/my-font-selections-cnrdeoe
fnt_outline = ImageFont.truetype("./RademosRegular-9YGrK.ttf", 110)

msg = "TRIPTOGRAMS"

def create_fade(args, promo_image, fade_color, t):
    intro_fade = 1.0 - smoothstep(0.00 * args.anim_seconds, 0.1 * args.anim_seconds, t)
    outro_fade = smoothstep(0.95 * args.anim_seconds, 1.00 * args.anim_seconds, t)
    fade = max(intro_fade,outro_fade)
    return Image.blend(promo_image, fade_color, fade)


def paint_text(promo_image, t):
    d = ImageDraw.Draw(promo_image)

    r = 5
    for angle in np.linspace(0,2*math.pi,30):
        off_x = r * math.cos(angle)
        off_y = r * math.cos(angle)
        paint_text_color_size(d, promo_image, size = 100, offset = ( off_x, off_y), color = (0,0,0))      
    paint_text_color_size(d, promo_image, size = 100, color = (125,0,0))


def paint_text_color_size(d, promo_image, size, color, offset = (0,0)):

    fnt = ImageFont.truetype("./RademosRegular-9YGrK.ttf", size)

    w, h = d.textsize(msg, font = fnt)
    c = promo_image.size[0] // 2

    x,y = int(c - w/2), (promo_image.size[1] * 0.2) - h/2

    x += offset[0]
    y += offset[1]

    d.text((x, y), msg, font = fnt, fill = color)

def fill_promo_image(args, images_holder, promo_image, worldspace_viewport, t):
    
    #(x0,y0),(x1,y1) = worldspace_viewport
    
    for (i,j) in images_holder:
        img = get_frame(images_holder[(i,j)],args,t).convert("RGB")
        a,b = world_2_image(args,worldspace_viewport, (i,j))
        c,d = world_2_image(args,worldspace_viewport, (i+1,j+1))
        a,b,c,d = map(int, (a,b,c,d))
        box = (a,b,c,d)

        img = img.resize((c-a,d-b))

        promo_image.paste(img, box = box)

def get_frame(img, args, t):
    frame = int(args.fps * t)
    frame = frame % img.n_frames
    if (frame < img.tell()):
        img.seek(0)
    try:
        img.seek(frame)
    except EOFError:
        img.seek(0)
    return img

def world_2_image(args, worldspace_viewport, pt):
    # The point to transform into image space
    wx,wy = pt
    (wx0,wy0),(wx1,wy1) = worldspace_viewport
    pct_x, pct_y = (wx - wx0) / (wx1 - wx0), (wy - wy0) / (wy1 - wy0)
    xdim,ydim = args.image_dims
    return pct_x * xdim, pct_y * ydim



def get_viewport(args, t):
    origin = get_origin(args, t)
    zoom   = get_zoom(args, t), get_zoom(args, t)
    return (origin[0] - zoom[0]/2, origin[1] - zoom[1]/2), (origin[0] + zoom[0] / 2, origin[1] + zoom[1] / 2)


def get_origin(args, t):
    # TODO: pathing
    x = args.img_grid[0] // 2 + 5.0*(t/args.anim_seconds)
    y = args.img_grid[1] // 2 
    return (x,y)

STARTING_TILES = 2
FINAL_TILES = 10

def smoothstep(start, end, t):
    if t < start:
        return 0.0
    elif t > end:
        return 1.0
    else:
        t = (t - start) / (end - start)
        #return 3 * (t**2.0) - 2 * (t**3.0) # smoothstep
        return 6*(t**5.0) - 15*(t**4.0) + 10*(t**3.0) # Ken Perlin's smootherstep

def get_zoom(args, t):
    # TODO: pathing
    return STARTING_TILES + (FINAL_TILES - STARTING_TILES) * smoothstep(0.0, 0.6*args.anim_seconds, t)

def request_images(images_holder, worldspace_viewport, fn_grid):
    #print("worldspace_viewport", worldspace_viewport)
    requested_imgs = set()
    (x0,y0),(x1,y1) = worldspace_viewport
    x0N, y0N, x1N, y1N = map(int, (x0,y0,x1,y1))
    for x in range(x0N, x1N +1):
        for y in range(y0N, y1N + 1):
            requested_imgs.add((x,y))
            if (x,y) not in images_holder:
                fname = fn_grid[x,y]
                images_holder[(x,y)] = get_image(fname)
    
    # Delete unrequested videos
    for image_to_vacate in (set(images_holder) - requested_imgs):
        images_holder[image_to_vacate].close()
        del images_holder[image_to_vacate]

    return images_holder

def get_image(fpath):
    return Image.open(fpath)

def get_image_fn_list(args):
    min_img, max_img = args.img_range
    for img_number in range(min_img, max_img+1):
        fpath = os.path.join(args.dir, "{}.{}".format(img_number,args.img_format))
        if not os.path.exists(fpath):
            raise Exception("{} DNE".format(fpath))
        yield fpath

def fill_image_fn_grid(args):
    image_fn_list = list(get_image_fn_list(args))
    image_grid = (100,100)
    fn_grid = np.zeros(image_grid[0]*image_grid[1], dtype=object)

    i = 0
    while i < len(fn_grid):
        random.shuffle(image_fn_list)
        fn_grid[i:i+len(image_fn_list)] = image_fn_list
        i += len(image_fn_list)

    return fn_grid.reshape(*image_grid)

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--dir", required = False, default = "./triptograms")
    parser.add_argument("--img_range", nargs=2, default = [0,99], type = int)
    parser.add_argument("--img_format", type= str, default = "png")
    parser.add_argument("--img_grid", nargs = 2, default = [20,20], type = int)
    parser.add_argument("--anim_seconds", type = int, default = 20)
    parser.add_argument("--fps", type = int, default = 30)
    parser.add_argument("--image_dims", nargs=2, type = int, default = [800,800])
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    create_promo_animation(args)