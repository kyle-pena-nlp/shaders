import numpy as np
import re, sys
from argparse import ArgumentParser
import json
import os, random
import multiprocessing
import shutil
from tqdm import tqdm
import math
from collections import defaultdict

from pyselenium import export
from common import parse_freqs, parse_trait_name, \
    parse_traits, templatize, wrap_in_html_shell, parse_num_seconds, to_url, \
    get_shader_text, remove_ext, set_preprocessor_directive

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

def check_for_trait_uniqueness(trait_values_array):

    trait_uniqueness_set = set()

    non_unique_count = 0

    for trait_dict in trait_values_array:
        # put keys in trait_dict in canonical order
        trait_dict = { key: trait_dict[key] for key in sorted(trait_dict) }
        trait_dict_string = json.dumps(trait_dict)
        if trait_dict_string in trait_uniqueness_set:
            non_unique_count += 1
        else:
            trait_uniqueness_set.add(trait_dict_string)
    
    if non_unique_count:
        raise Exception("Generated images not unique - {} duplicates".format(non_unique_count))


def generate(args, shader, name, override_traits):

    N = args.N; x = args.x; y = args.y; fps = args.fps; format = args.format; compress = args.compress

    traits          = parse_traits(shader)      # { TRAIT : { NAME: (OPTION, FREQUENCY) } }
    string_template = templatize(shader)        # string with template args

    out_dir = name

    os.makedirs(os.path.join(".", out_dir), exist_ok = True)

    trait_values_array, trait_names_array = generate_random_trait_values(N, traits, override_traits)

    N = len(trait_values_array)
    TRAIT_COUNTS = defaultdict(lambda: defaultdict(lambda: 0))
    trait_keys = list(trait_names_array[0])
    for trait_name in trait_keys:
        for trait_name_set in trait_names_array:
            TRAIT_COUNTS[trait_name][trait_name_set[trait_name]] += (1/N)
    print(json.dumps(TRAIT_COUNTS, indent = 1))

    check_for_trait_uniqueness(trait_values_array)

    for i, trait_values in enumerate(trait_values_array):      

        template_parameters = trait_values
        shader_text = string_template.format(**template_parameters)
        shader_text = set_preprocessor_directive(shader_text, "JITTER_SALT",  "{:.1f}".format(i))
        
        with open(os.path.join(".", out_dir, "{}.glsl".format(i)), "w+") as f:
            f.write(shader_text)

        trait_value_names = trait_names_array[i]
        with open(os.path.join(".", out_dir, "{}.traits".format(i)), "w+") as f:
            f.write(json.dumps(trait_value_names, indent = 1))

        with open(os.path.join(".", out_dir, "{}.json".format(i)), "w+") as f:
            f.write(json.dumps(gen_metaplex_metadata(args, index = i, traits_dict = trait_value_names), indent = 1))

        html_text = wrap_in_html_shell(shader_text)
        html_fpath = os.path.join(".", out_dir, "{}.html".format(i))
        with open(html_fpath, "w+") as f:
            f.write(html_text)

        yield html_fpath, shader_text, x, y, fps, format, compress

def gen_metaplex_metadata(args, index, traits_dict):

    format = args.format

    shader_name = args.shader
    image_filename = "{}.{}".format(index, format)
    titleized_name = shader_name.title()
    symbol_name = re.sub(r"\s+", "", shader_name.upper())[:5]
    mime_type = "image/{}".format(format)

    attributes = []
    for trait_name in sorted(traits_dict):
        trait_value = traits_dict[trait_name]
        attributes.append({ "trait_type": trait_name, "value": trait_value })

    data = {
        "name": titleized_name,
        "symbol": symbol_name,
        "image": image_filename,
        "external_url": "https://www.bonkworld.art/",
        "properties": {
            "files": [{ "uri": image_filename, "type": mime_type }],
            "category": "image",
            "creators": [
                {
                    "address": "F7snYM4cE5RMbNXcuJTMwcKtxXNtXopJf9PNKXmSqNvv",
                    "share": 50
                }, 
                {
                    "address": "udhne2o5r2wFKKt4uCAF4LH3mX2LwmczuaAQw9PrJJr",
                    "share": 50
                },                            
            ]
        },
        "description": "Perfectly looping, color-rich math art for gazing deep and thinking big thoughts.",
        "seller_fee_basis_points": 500,
        "attributes": attributes,
        "collection": { "name": titleized_name, "family": "Bonk World" }
    }

    return data

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--shader", type = str, required = False, default = None)
    parser.add_argument("--N", type = int, required = False, default = 10)
    parser.add_argument("--seed", type = int, required = False, default = 42)
    parser.add_argument("--parallel", type = int, required = False, default = 1)
    parser.add_argument("--x", type = int, default = 300)
    parser.add_argument("--y", type = int, default = 300)
    parser.add_argument("--fps", type = int, default = 30)
    parser.add_argument("--format", default = "mp4", choices = ["mp4","gif","png"])
    parser.add_argument("--compress", default = False, type = bool)
    parser.add_argument("--wallet_address", type = str, default = None)
    #parser.add_argument("--traits_file", type = str, required = False, default = None)
    args = parser.parse_args()
    override_traits = {}
    #args, traits = parser.parse_known_args()
    #traits = _traits_to_dict(traits)
    return args, override_traits



def execute(args):
    html_fpath, genned_shader_text, x, y, fps, format, compress = args
    print("Generating from {}".format(html_fpath))
    
    export(url = to_url(html_fpath), x = x, y = y,
        frames_per_second = fps, 
        num_seconds = parse_num_seconds(genned_shader_text),
        out = html_fpath,
        out_format = format,
        compress = compress)  
    
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
    
    results = generate(args, shader_text, name, traits)

    if args.parallel > 0:
        pool = multiprocessing.Pool()
        pool.map(execute, results)
    else:
        for result in tqdm(results, total = args.N):
            execute(result)

    print("Done.")

