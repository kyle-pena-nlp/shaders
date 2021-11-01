import os, re, json

def get_shader_text(shader_fp):
    if shader_fp is None:
        return open("./example_shader.glsl", "r").read()
    else:
        return open(shader_fp, "r").read()

def remove_ext(shader_fname):
    fname = os.path.basename(shader_fname)
    dirpath = os.path.dirname(shader_fname)
    root,*_ = fname.rsplit(".",1)
    return os.path.join(dirpath, root)

def ensure_ext(shader_fname, new_ext):
    fname = os.path.basename(shader_fname)
    dirpath = os.path.dirname(shader_fname)
    return os.path.join(dirpath, ".".join([remove_ext(fname), new_ext]))

def to_url(fpath):
    return "file:///" + os.path.abspath(fpath)

def to_out_path(fpath, postfix):
    first,*_ = fpath.rsplit(".",1)
    return "-".join([first, postfix])

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

def _traits_to_dict(traits_arr):
    results = {}
    for i in range(len(traits_arr)):
        if i % 2 == 0:
            name = traits_arr[i].lstrip("-")
            results[name] = traits_arr[i+1]
    return results

def parse_traits_file(traits_fpath):
    with open(traits_fpath, "r") as f:
        return json.load(f)