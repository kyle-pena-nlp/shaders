from io import BytesIO
import os, json, re
import urllib.request
from argparse import PARSER, ArgumentParser
from glob import glob
from tqdm import tqdm
import http.server
import socketserver
import time
import shutil

PORT = 8000
DIRECTORY = "./"

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):

    #def __init__(self, *args, **kwargs):
    #    print("Serving from directory", DIRECTORY)
    #    super().__init__(*args, directory=DIRECTORY, **kwargs)

    def _set_JSON_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self.path = "metadata_checker.html"
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        elif self.path == "/data":
            print("Request received")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(DATAS).encode(encoding="utf-8"))
        else:
            return super().do_GET()
        return

def parse_args():
    global DIRECTORY
    parser = ArgumentParser()
    parser.add_argument("--json_dir", type = str, default = "triptograms")
    parser.add_argument("--directory", type = str, default = "./")
    args = parser.parse_args()
    DIRECTORY = args.directory
    return args

def request_arweave_json(arweave_url_filepath):
    arweave_url = open(arweave_url_filepath, "r").read().strip()
    return json.loads(urllib.request.urlopen(arweave_url).read())

def request_metadata_json(arweave_json):
    metadata_json_url = arweave_json["some.property"]
    return json.loads(urllib.request.urlopen(metadata_json_url).read())

def get_image_url(metadata_json):
    return metadata_json["some.property"]

def get_local_image_url(metadata_json):
    image_number = int(metadata_json["name"].split(" ")[1][1:])
    return "http://localhost:{}/{}.png".format(PORT, image_number)

def scrape_metadata_urls(metadata_fp):
    retries = 0
    while retries < 10:
        try:
            content = json.load(open(metadata_fp, "r"))
            return content
        except:
            time.sleep(0.5)
            retries += 1
    raise Exception(metadata_fp)


def start_an_image_server():
    handler = MyHttpRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    httpd.serve_forever()

DATAS = []

def do_it(args):
    
    metadata_fps = [ x for x in  glob(os.path.join(DIRECTORY, args.json_dir, "*.json")) if re.match(r"\d+\.json", os.path.basename(x)) ]
    metadata_fps.sort(key = lambda fp: int(os.path.basename(fp).split(".")[0]))
    for metadata_fp in tqdm(metadata_fps, desc = "Scraping metadatas"):
        #print(".")
        DATAS.append(scrape_metadata_urls(metadata_fp))
    try:
        shutil.copy2("./metadata_checker.html", os.path.join(DIRECTORY, "./metadata_checker.html"))
    except shutil.SameFileError:
        pass
    os.chdir(args.directory)
    start_an_image_server()

if __name__ == "__main__":
    args = parse_args()
    do_it(args)