import numpy as np
import re, sys
from argparse import ArgumentParser
import json
import os, random
import multiprocessing
import shutil
from tqdm import tqdm
import math
import tempfile

from pyselenium import export
from common import parse_num_seconds, parse_traits, parse_traits_file, remove_ext, \
    get_shader_text, templatize, \
    wrap_in_html_shell, to_url, \
    parse_num_seconds, ensure_ext

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--shader", type = str, required = False, default = None)
    parser.add_argument("--traits_file", type = str)
    parser.add_argument("--out", type = str)
    parser.add_argument("--x", type = int)
    parser.add_argument("--y", type = int)
    parser.add_argument("--frames_per_second", type = int)
    parser.add_argument("--format", type = str, choices = ["mp4","png","gif"])
    parser.add_argument("--compress", type = bool, default = False)
    args = parser.parse_args()
    return args

def replace_with_values(raw_shader_text, traits):
    reference_traits = parse_traits(raw_shader_text)
    return { trait_name: reference_traits[trait_name][traits[trait_name]][0] for trait_name in traits }

if __name__ == "__main__":

    args = parse_args()

    traits = parse_traits_file(args.traits_file)

    name = os.path.basename(remove_ext(args.shader)) if args.shader is not None else "EXAMPLE"

    raw_shader_text = get_shader_text(args.shader)

    num_seconds = parse_num_seconds(raw_shader_text)

    template = templatize(raw_shader_text)    

    shader_text = template.format(**replace_with_values(raw_shader_text, traits))

    html = wrap_in_html_shell(shader_text)

    html_fpath = ensure_ext(args.out, "html")

    with open(html_fpath, "w+") as html_f:
        html_f.write(html)

    url = to_url(html_fpath)

    export(url = url, 
        x = args.x, 
        y = args.y, 
        frames_per_second = args.frames_per_second, 
        num_seconds = num_seconds, 
        out = args.out, 
        out_format = args.format,
        compress = args.compress)

    print("Done.")

