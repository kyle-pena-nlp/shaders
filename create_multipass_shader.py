from argparse import ArgumentParser

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--main", type = str)
    parser.add_argument("--A", type = str, default = None)
    parser.add_argument("--B", type = str, default = None)
    parser.add_argument("--C", type = str, default = None)
    return parser.parse_args()

def get_js_template():
    return open("./multipass_js_template.js", "r").read()

def get_main_shader(args):
    with open(args.main, "r") as f:
        return f.read()

def get_buffer_shader(args, buffer):
    buffer = getattr(args, buffer)
    if buffer is None:
        return ""
    else:
        with open(buffer, "r") as f:
            return f.read()

def replace_js_template_placeholders(js_template, args):
    js_template = js_template.replace("#SHADER_PLACEHOLDER#", get_main_shader(args))
    js_template = js_template.replace("#SHADER_PLACEHOLDER_A#", get_buffer_shader(args, "A"))
    js_template = js_template.replace("#SHADER_PLACEHOLDER_B#", get_buffer_shader(args, "B"))
    js_template = js_template.replace("#SHADER_PLACEHOLDER_C#", get_buffer_shader(args, "C"))

def get_js(args):
    js_template = get_js_template()
    js = replace_js_template_placeholders(js_template, args)
    return js

def get_html_template(args):
    with open("./html_template", "r") as f:
        return f.read()

def get_html(args, js):
    html_template = get_html_template(args)
    return html_template.replace("#JS_PLACEHOLDER#", js)

def do_it(args):
    js = get_js(args)
    html = get_html(args, js)


if __name__ == "__main__":
    args = parse_args()
    do_it(args)