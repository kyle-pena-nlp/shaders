import numpy as np
import re, sys
from argparse import ArgumentParser
import json
import os, random
import multiprocessing
import shutil
from tqdm import tqdm
import math

from pyselenium import export
from common import parse_freqs, parse_trait_name, \
    parse_traits, templatize, wrap_in_html_shell, parse_num_seconds, to_url, \
    get_shader_text, remove_ext

# TODO: proper seeding for reproduciblity (will random.seed cut it for true repro?)
# TODO: real parsing of loop time
# TODO: mp4 quality setting
# TODO: total elapsed time code
# TODO: algorithm for unique trait combinations observing prob distribution
# TODO: more shader traits



def _generate_random_trait_values(value_array, name_array, offset, N, traits, override_traits):
    """
        The recursive part of a pseudo-random algorithm for assigning traits "randomly", but uniquely
    """

    if len(traits) == 0 or N == 0:
        return

    # Grab the next trait
    trait_name,trait = traits.pop()

    # If the trait is overridden, shim in a dictionary saying use the override value 100% of the time
    if trait_name in override_traits:
        name = override_traits[trait_name]
        value,_ = trait[name]
        trait = { name: (value,1.) }
    
    # Process the names of the traits in a random order
    names = list(trait)
    random.shuffle(names)

    start_ = 0

    # For each trait value's name
    for name_idx, name in enumerate(names):

        # Get the value and frequency of the trait value
        value, freq = trait[name]

        # Renormalize the frequency based on the sum of this and the remaining choices (Will always be 1.0 on last choice)
        freq_support = sum(trait[names[idx]][1] for idx in range(len(names)) if idx >= name_idx)
        freq = freq / freq_support

        # Determine how long of a run to devote to this value
        E_n = (N - start_) * freq
        n, frac = int(E_n), E_n-int(E_n)
        if random.random() < frac:
            n += 1
        n = min(n, N - start_)

        # If it's the last item, always fill out the rest of the subarray
        if name == names[-1]:
            n = N - start_

        # Assign the run to this value
        for i in range(start_, start_ + n):
            value_array[offset+i][trait_name] = value
            name_array[offset+i][trait_name] = name

        _generate_random_trait_values(value_array, name_array, offset + start_, n, traits.copy(), override_traits)

        # Update the starting point of the array
        start_ += n

        # Treat this run as a subarray and recurse with the next trait

def generate_random_trait_values(N, traits, override_traits):
    """
        A pseudo-random algorithm for assigning traits "randomly", but uniquely.
        For each trait, assigns runs within an array of length proportional to frequency
        Then, for each run, treat this as a subarray and recurse using the next trait in the list
        Randomize the order of the traits and the order of the items in the traits
        If a frequency implies a non-integer run length, 
        decide stochastically whether to +1 based on the fractional part of the length
    """

    # Process the traits in a random order
    traits = list(traits.items())
    random.shuffle(traits)

    # This is where the randomly selected traits will be stored
    value_array = [ dict() for _ in range(N) ]
    name_array  = [ dict() for _ in range(N) ]

    # For each position in the array, select 'random' traits
    _generate_random_trait_values(value_array, name_array, 0, N, traits, override_traits)

    # TODO: shuffle

    return value_array, name_array


def generate(N, shader, name, override_traits):

    traits          = parse_traits(shader)      # { TRAIT : { NAME: (OPTION, FREQUENCY) } }
    string_template = templatize(shader)        # string with template args

    out_dir = name

    os.makedirs(os.path.join(".", out_dir), exist_ok = True)

    trait_values_array, trait_names_array = generate_random_trait_values(N, traits, override_traits)

    for i, trait_values in enumerate(trait_values_array):

        template_parameters = trait_values
        shader_text = string_template.format(**template_parameters)
        with open(os.path.join(".", out_dir, "{}.glsl".format(i+1)), "w+") as f:
            f.write(shader_text)

        trait_value_names = trait_names_array[i]
        with open(os.path.join(".", out_dir, "{}.json".format(i+1)), "w+") as f:
            f.write(json.dumps(trait_value_names, indent = 1))

        html_text = wrap_in_html_shell(shader_text)
        html_fpath = os.path.join(".", out_dir, "{}.html".format(i+1))
        with open(html_fpath, "w+") as f:
            f.write(html_text)

        yield html_fpath, shader_text



def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--shader", type = str, required = False, default = None)
    parser.add_argument("--N", type = int, required = False, default = 10)
    parser.add_argument("--seed", type = int, required = False, default = 42)
    parser.add_argument("--parallel", type = int, required = False, default = 1)
    #parser.add_argument("--traits_file", type = str, required = False, default = None)
    args = parser.parse_args()
    override_traits = {}
    #args, traits = parser.parse_known_args()
    #traits = _traits_to_dict(traits)
    return args, override_traits



def execute(args):
    html_fpath, genned_shader_text = args
    print("Generating from {}".format(html_fpath))
    
    export(url = to_url(html_fpath), x = 300, y = 300,
        frames_per_second = 20, 
        num_seconds = parse_num_seconds(genned_shader_text),
        out = html_fpath,
        out_format = "mp4")  
    
    """
    export(url = to_url(html_fpath), x = 800, y = 600,
        frames_per_second = 25, 
        num_seconds = parse_num_seconds(genned_shader_text),
        out = to_out_path(html_fpath, postfix = "twitter"),
        out_format = "mp4") 
    """



if __name__ == "__main__":

    args, traits = parse_args()

    name = os.path.basename(remove_ext(args.shader)) if args.shader is not None else "EXAMPLE"

    shader_text = get_shader_text(args.shader)

    random.seed(args.seed)
    
    results = generate(args.N, shader_text, name, traits)

    if args.parallel > 0:
        pool = multiprocessing.Pool()
        pool.map(execute, results)
    else:
        for result in tqdm(results, total = args.N):
            execute(result)

    print("Done.")

