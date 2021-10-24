import numpy as np
import re, sys
from argparse import ArgumentParser
import json
import os, random
from pyselenium import export
import multiprocessing


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

def generate(N, shader, name):

    traits          = parse_traits(shader)      # { TRAIT : { OPTION: FREQUENCY } }
    string_template = templatize(shader)        # string with template args
    for i in range(N):

        selected_values, selected_value_names = [], []
        for trait in traits:

            value_names = list(traits[trait])
            value_probabilities = [ traits[trait][name][1] for name in value_names ]

            selected_value_name = random.choices(value_names, weights = value_probabilities, k = 1)[0]
            selected_value_names.append(selected_value_name)

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

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--shader", type = str, required = False, default = None)
    parser.add_argument("--N", type = int, required = False, default = 10)
    parser.add_argument("--seed", type = int, required = False, default = 42)
    return parser.parse_args()

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

def parse_num_seconds(shader_text):
    return 10

def to_out_path(fpath, postfix):
    first,*_ = fpath.rsplit(".",1)
    return "-".join([first, postfix])

def execute(args):
    html_fpath, genned_shader_text = args
    print("Generating from {}".format(html_fpath))
    
    export(url = to_url(html_fpath), x = 250, y = 250,
        frames_per_second = 25, 
        num_seconds = parse_num_seconds(genned_shader_text),
        out = to_out_path(html_fpath, postfix = "twitter"),
        format = "gif")  

    export(url = to_url(html_fpath), x = 800, y = 600,
        frames_per_second = 25, 
        num_seconds = parse_num_seconds(genned_shader_text),
        out = to_out_path(html_fpath, postfix = "twitter"),
        format = "gif") 

if __name__ == "__main__":

    args = parse_args()

    name = os.path.basename(remove_ext(args.shader)) if args.shader is not None else "EXAMPLE"

    shader_text = get_shader_text(args.shader)

    random.seed(args.seed)
    
    results = generate(args.N, shader_text, name)

    pool = multiprocessing.Pool()

    pool.map(execute, results)

    print("Done.")

