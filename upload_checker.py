import os, json
import urllib.request
from argparse import ArgumentParser
from glob import glob
from tqdm import tqdm
import http.server
import socketserver
PORT = 8000

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="D:/", **kwargs)

    def _set_JSON_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()        

    def do_GET(self):
        if self.path == "/":
            self.path = "image_upload_checker.html"
        elif self.path == "/data":
            self._set_JSON_headers()
            self.wfile.write(json.dumps(DATAS, indent = 1))
            return DATAS
        else:
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--json_dir", type = str)
    return parser.parse_args()

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

def scrape_arweave_url(arweave_url):
    # TODO: failure cases
    arweave_json          = request_arweave_json(arweave_url)
    metadata_json         = request_metadata_json(arweave_json)
    arweave_image_url     = get_image_url(metadata_json)
    local_image_url       = get_local_image_url(metadata_json)
    NFT_info = {
        "arweave_image_url": arweave_image_url,
        "local_image_url": local_image_url,
        "metadata": metadata_json
    }
    return NFT_info

DATAS = []

def do_it(args):
    
    # Get all the data from the arweave URLs
    arweave_urls = glob(os.path.join(args.json_dir, "*.txt"))
    for arweave_urls in tqdm(arweave_urls, desc = "Scraping arweave URLs for data..."):
        DATAS.append(scrape_arweave_url(arweave_urls))


    

if __name__ == "__main__":
    args = parse_args()
    do_it(args)