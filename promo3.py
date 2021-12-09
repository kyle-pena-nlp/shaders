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
from typing import List, Tuple, Dict

TEST_MODE = True

class FrameAtlas:

    def __init__(self, directory, dims, dtype, format = "gif"):
        self.directory = directory
        self.dims = dims
        self.dtype = dtype
        self.format = format
        self.indexing = {}
        self._init()
        self.cache = None
        self.filepaths = None
        self.N = None
        self.img_idxs_2_cache_idxs = None

    def _init_(self):
        self.filepaths = [ fp for fp in glob(os.path.join(self.directory, "*.{}".format(self.format))) if re.match(r"\d+\." + re.escape(self.format), os.path.basename(fp))]
        random.shuffle(self.filepaths)
        self.cache = np.zeros((self.length, self.dims[0], self.dims[1], 3), dtype = self.dtype)
        self.N = int(float(len(self.filepaths))**0.5)
        self.ij_to_i = np.asarray(list(range(len(self.filepaths)))[:(self.N**2)]).reshape(self.N,self.N)
    
    def update(self, np_img_idxs, t):

        # Per pixel, which image idx (per self.filepaths) 
        xs, ys = np.mod(np_img_idxs[:,0]), np.mod(np_img_idxs[:,1])
        np_img_idxs  = self.ij_2_i[xs, ys]

        flat_img_idxs = np_img_idxs.ravel()
        np_cache_idxs = self.img_idxs_2_cache_idxs[flat_img_idxs].reshape(*np_img_idxs.shape)
        




    def request_images(self, idxs : List[Tuple[int,int]]):
        pass

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

    # Pre-load all rendering data
    all_uv_frames, all_lighting_frames, all_normals_frames, all_image_idx_frames = [], [], [], []
    for t in tqdm(list(range(nframes))):
        for img in all:
            img.seek(t)
        all_uv_frames.append(np.asarray(uvs))
        all_lighting_frames.append(np.asarray(all_lighting_frames))
        all_normals_frames.append(np.asarray(normals))
        all_image_idx_frames.append(np.asarray(image_idxs))
    all_uv_frames = np.asarray(all_uv_frames)
    all_lighting_frames = np.asarray(all_lighting_frames)
    all_normals_frames = np.asarray(all_normals_frames)
    all_image_idx_frames = np.asarray(all_image_idx_frames)

    #Pre-load image atlas
    images_holder = {}
    images_atlas = [ fp for fp in glob(os.path.join("triptograms", "*.gif")) if re.match(r"\d+\.gif", os.path.basename(fp)) ]
    random.shuffle(images_atlas)

    # TODO: separate process to assemble giant image sheet.

    images_atlas = images_atlas * 5
    images_atlas = np.asarray(images_atlas)[:(70*70)].reshape(70,70)



    x,y,source_nframes = None,None,None

    with get_writer(frames_per_second = args.fps, out = "promo3.mp4", out_format = "mp4", compress = False) as writer:

        for t in tqdm(range(nframes)):

            for img in all:
                img.seek(t)
            np_uvs = np.asarray(uvs)

            # get light level per pixel
            light_level = np.asarray(lighting).astype(np.float) / 255

            # Find out which images are requested
            requested_images = set()
            np_img_idxs = np.asarray(image_idxs)
            x = x or np_img_idxs.shape[0]
            y = y or np_img_idxs.shape[1]

            # In progress: vectorization of image index normalization
            np_img_idxs = np_img_idxs.astype(np.float)
            zeros_mask = np_img_idxs[...,2] == 0
            np_img_idxs = np.stack([np_img_idxs[:,:,0] / np_img_idxs[:,:,2], np_img_idxs[:,:,1] / np_img_idxs[:,:,2]], axis = 2).astype(np.int)
            np_img_idxs[zeros_mask,:] = 0
            uq_img_idxs = set(zip(np_img_idxs[:,:,0].ravel(), np_img_idxs[:,:,1].ravel()))
            if TEST_MODE:
                requested_images.add((20,20))
            else:
                for uq_img_idx in uq_img_idxs:
                    requested_images.add(uq_img_idx)
            # Request them
            ensure_requested_images(images_holder, requested_images, images_atlas, t)

            scene = np.zeros((x, y, 3), dtype = np.dtype("uint8"))

            # TODO: vectorize this
            # Fill the frame with the requested images
            frame_cache = {}
            np_uvs = np.asarray(uvs)
            for i in range(np_uvs.shape[0]):
                for j in range(np_uvs.shape[1]):
                    img_i,img_j = np_img_idxs[i,j,:]
                    if TEST_MODE:
                        img_i, img_j = 20,20
                    if img_i == 0 and img_j == 0:
                        continue
                    if (img_i,img_j) not in frame_cache:
                        source_nframes = source_nframes or images_holder[(img_i,img_j)].n_frames
                        frame_cache[(img_i,img_j)] = np.asarray(images_holder[(img_i, img_j)].convert("RGB"))
                    img_u,img_v,_ = np_uvs[i,j] 
                    #print(np.amin(np_uvs), np.amax(np_uvs))
                    img_u,img_v = int(1.5*x*img_u/255), int(1.5*y*img_v/255)
                    #print(img_u, img_v)
                    
                    #print("shape", frame_cache[(img_i,img_j)].shape)
                    diffuse =frame_cache[(img_i,img_j)][img_u,img_v, :3]
                    # TODO: lighting compositing
                    
                    scene[i, j] = diffuse * light_level[i,j]

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