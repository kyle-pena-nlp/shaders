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

# TODO: proper seeding for reproduciblity (will random.seed cut it for true repro?)
# TODO: real parsing of loop time
# TODO: mp4 quality setting
# TODO: total elapsed time code
# TODO: algorithm for unique trait combinations observing prob distribution
# TODO: more shader traits

def is_trait_line(line):
    is_a_comment = line.strip().startswith("//")
    line = line.strip().lstrip("//").strip()
    return line.startswith("{") and line.endswith("}")

def is_define_line(line):
    return line.strip().lower().startswith("#define")

def parse_trait_name(line):
    return re.split(r"\s+", line.strip())[1]

def parse_freqs(line):
    line = line.strip().lstrip("//").strip()
    trait_freqs = eval(line)
    return trait_freqs

def parse_traits(shader):
    traits = {}
    lines = shader.splitlines()
    for (line,nextline) in zip(lines,lines[1:]):
        if is_trait_line(line) and is_define_line(nextline):
            name = parse_trait_name(nextline)
            freqs = parse_freqs(line)
            traits[name] = freqs
    return traits


def templatize(shader):
    traits = parse_traits(shader)
    template = shader.replace("{", "{{").replace("}", "}}")
    for trait in traits:
        pattern = r"#define\s+" + trait + "\s+.*"
        replacement = "#define " + trait + " {" + trait + "}"
        if template != re.sub(pattern, replacement, template):
            print("!")
        template = re.sub(pattern, replacement, template)
    return template
    
def wrap_in_html_shell(shader_text):
    with open("js_template.js", "r") as f:
        js_template = f.read()
    js = js_template.replace("#SHADER_PLACEHOLDER#", shader_text)
    with open("html_template.html", "r") as f:
        html_template = f.read()
    html =html_template.replace("#JS_PLACEHOLDER#", js)
    return html


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


    """
    for i in range(N):

        selected_values, selected_value_names = [], []
        for trait in traits:

            value_names = list(traits[trait])
            value_probabilities = [ traits[trait][name][1] for name in value_names ]

            selected_value_name = random.choices(value_names, weights = value_probabilities, k = 1)[0]
            selected_value_names.append(selected_value_name)

            if trait in override_traits:
                selected_value = override_traits[trait]
            else:
                selected_value      = traits[trait][selected_value_name][0]
            selected_values.append(selected_value)

        out_dir = name

        os.makedirs(os.path.join(".", out_dir), exist_ok = True)

        template_parameters = dict(zip(list(traits), selected_values))
        shader_text = string_template.format(**template_parameters)
        with open(os.path.join(".", out_dir, "{}.glsl".format(i+1)), "w+") as f:
            f.write(shader_text)

        with open(os.path.join(".", out_dir, "{}.json".format(i+1)), "w+") as f:
            f.write(json.dumps(selected_value_names, indent = 1))

        html_text = wrap_in_html_shell(shader_text)
        html_fpath = os.path.join(".", out_dir, "{}.html".format(i+1))
        with open(html_fpath, "w+") as f:
            f.write(html_text)

        yield html_fpath, shader_text
    """

def _traits_to_dict(traits_arr):
    results = {}
    for i in range(len(traits_arr)):
        if i % 2 == 0:
            name = traits_arr[i].lstrip("-")
            results[name] = traits_arr[i+1]
    return results

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--shader", type = str, required = False, default = None)
    parser.add_argument("--N", type = int, required = False, default = 10)
    parser.add_argument("--seed", type = int, required = False, default = 42)
    parser.add_argument("--parallel", type = int, required = False, default = 1)
    args, traits = parser.parse_known_args()
    traits = _traits_to_dict(traits)
    return args, traits

def get_shader_text(shader_fp):
    if shader_fp is None:
        return open("./example_shader.glsl", "r").read()
    else:
        return open(shader_fp, "r").read()

def remove_ext(shader_fname):
    root,*_ = shader_fname.rsplit(".",1)
    return root

def to_url(fpath):
    return "file:///" + os.path.abspath(fpath)

LOOP_TIME_PATTERN = r"#define\s+LOOP_TIME\s+(\d+\.)\s*"

def parse_num_seconds(shader):
    lines = shader.splitlines()
    for line in lines:
        pattern_match = re.match(LOOP_TIME_PATTERN, line)
        if pattern_match:
            loop_time = int(float(pattern_match.groups()[0]))
            #print("Parsed loop time is {} seconds".format(loop_time))
            return loop_time
    raise Exception("LOOP_TIME definition not found.")

def to_out_path(fpath, postfix):
    first,*_ = fpath.rsplit(".",1)
    return "-".join([first, postfix])

def execute(args):
    html_fpath, genned_shader_text = args
    print("Generating from {}".format(html_fpath))
    
    
    export(url = to_url(html_fpath), x = 300, y = 300,
        frames_per_second = 10, 
        num_seconds = parse_num_seconds(genned_shader_text),
        out = to_out_path(html_fpath, postfix = "twitter"),
        out_format = "png")  
    
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

