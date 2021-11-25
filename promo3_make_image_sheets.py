import re, os, random
from argparse import ArgumentParser
from glob import glob
import numpy as np
from PIL import Image
import imageio

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--shader", type = str, default = "triptograms")
    parser.add_argument("--grid_size", type = int, default = 70)
    parser.add_argument("--seed", type = int, default = 42)
    parser.add_argument("--frames", type = int, default = 400)
    return parser.parse_args()

def do_it(args):
    random.seed(args.seed)
    png_fps = [ fp for fp in glob(os.path.join(args.shader, "*.png")) if re.match(r"\d+\.png", os.path.basename(fp)) ]
    random.shuffle(png_fps)
    png_fps = png_fps[:(args.grid_size*args.grid_size)]
    open_png_images = [ Image.open(fp) for fp in png_fps ]
    height, width = open_png_images[0].size
    channels = 3
    
    #with imageio.get_writer("uvs_sheet")
    # This won't work either... resulting image will be too big
    # todo: find a solution tomorrow.  maybe the first approach was the right approach.
    for t in range(args.frames):
        np_imgs = []

        for i in range(len(open_png_images)):
            open_png_images[i].seek(t % open_png_images[i].n_frames)
            np_imgs.append(np.asarray(open_png_images[i]))

        np_imgs = np.asarray(np_imgs)
        images_grid = np_imgs.reshape(args.grid_size, args.grid_size, height, width, 3)\
            .swapaxes(1,2)\
            .reshape(args.grid_size * height, args.grid_size * width, channels)



if __name__ == "__main__":
    args = parse_args()
    do_it(args)