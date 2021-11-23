from PIL import Image
from argparse import ArgumentParser
from tqdm import tqdm
import os, time
import numpy as np
import math
from glob import glob
import re
import random
import matplotlib.pyplot as plt
import sys
from pyselenium import get_writer
from io import BytesIO

def do_it(args):

    random.seed(args.seed)

    # TODO: preload all frames of all images as numpy arrays?  (if possible and practical)
    # TODO: multiprocessing?

    directory = "bonkworld_uvs_promo"
    uvs = Image.open(os.path.join(directory, "bonkworld_uvs.png"))
    lighting = Image.open(os.path.join(directory, "bonkworld_lighting.png"))
    normals = Image.open(os.path.join(directory, 'bonkworld_normals.png'))
    image_idxs = Image.open(os.path.join(directory, "bonkworld_image_idxs.png"))
    all = [uvs, lighting, normals, image_idxs]

    nframes = uvs.n_frames

    print(nframes)

    images_holder = {}

    images_atlas = [ fp for fp in glob(os.path.join("triptograms", "*.png")) if re.match(r"\d+\.png", os.path.basename(fp)) ]
    random.shuffle(images_atlas)
    images_atlas = images_atlas * 5
    images_atlas = np.asarray(images_atlas)[:(70*70)].reshape(70,70)

    x,y,source_nframes = None,None,None

    with get_writer(frames_per_second = args.fps, out = "promo3.mp4", out_format = "mp4", compress = False) as writer:

        for t in tqdm(range(nframes)):
            for img in all:
                img.seek(t)
            np_uvs = np.asarray(uvs)

            # Find out which images are requested
            requested_images = set()
            np_img_idxs = np.asarray(image_idxs)
            x = x or np_img_idxs.shape[0]
            y = y or np_img_idxs.shape[1]

            # In progress: vectorization of image index normalization
            np_img_idxs = np_img_idxs.astype(np.float)
            np_img_idxs = np.concat([np_img_idxs[:,:,0] / np_img_idxs[:,:,2], np_img_idxs[:,:,1] / np_img_idxs[:,:,2]]).astype(np.int)
            uq_img_idxs = set(zip(np_img_idxs[:,:,0].ravel(), np_img_idxs[:,:,1].ravel()))
            for uq_img_idx in uq_img_idxs:
                requested_images.add(uq_img_idx)
            # TODO: vectorize this
            """
            for i in range(np_img_idxs.shape[0]):
                for j in range(np_img_idxs.shape[1]):
                    R,G,B = np_img_idxs[i,j,:]
                    if R == 0 and G == 0 and B == 0:
                        continue
                    img_i = int(round(R/B))
                    img_j = int(round(G/B))
                    requested_images.add((img_i, img_j))
            """
            # Request them
            ensure_requested_images(images_holder, requested_images, images_atlas, t)

            scene = np.zeros((x, y, 3), dtype = np.dtype("uint8"))

            # TODO: vectorize this
            # Fill the frame with the requested images
            frame_cache = {}
            np_uvs = np.asarray(uvs)
            for i in range(np_uvs.shape[0]):
                for j in range(np_uvs.shape[1]):
                    R,G,B = np_img_idxs[i,j,:]
                    if R == 0 and G == 0 and B == 0:
                        continue
                    img_i = int(round(R/B))
                    img_j = int(round(G/B))
                    if (img_i,img_j) not in frame_cache:
                        source_nframes = source_nframes or images_holder[(img_i,img_j)].n_frames
                        frame_cache[(img_i,img_j)] = np.asarray(images_holder[(img_i, img_j)])
                    img_u,img_v,_ = np_uvs[i,j] 
                    img_u,img_v = round(x*img_u/255), round(y*img_v/255)
                    diffuse =frame_cache[(img_i,img_j)][img_u,img_v, :3]
                    # TODO: lighting compositing
                    scene[i, j] = diffuse

            #plt.imshow(scene)
            #plt.show()
            #sys.exit()

            writer.append_data(scene)


def to_PNG_bytes(np_img):
    pil_img = Image.fromarray(np_img)
    with BytesIO() as b:
        # We save a little bit by dropping the alpha channel
        pil_img.save(b, format = "png")
        b.seek(0)
        return b.read()


def ensure_requested_images(images_holder, requested_images, images_atlas, t):
    for (i,j) in requested_images:
        if (i,j) not in images_holder:
            images_holder[(i,j)] = Image.open(images_atlas[(i,j)])

    marked_for_deletion = set()
    for (i,j) in images_holder:
        if (i,j) not in requested_images:
            marked_for_deletion.add((i,j))

    for (i,j) in marked_for_deletion:
        images_holder[(i,j)].close()
        del images_holder[(i,j)]

    for (i,j) in images_holder:
        n_frames = images_holder[(i,j)].n_frames
        images_holder[(i,j)].seek(t % n_frames)

  
    

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--fps",  type = int, default = 30)
    parser.add_argument("--seed", type = int, default = 42)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    do_it(args)