import http.server
import socketserver
import os
PORT = 8000
DIRECTORY = "./" # ="D:/"

from argparse import ArgumentParser

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/":
            self.path = "image_viewer.html"
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--shader", type = str, default = "triptograms")
    return parser.parse_args()

def start_an_image_server(directory):
    handler = MyHttpRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    httpd.serve_forever()

if __name__ == "__main__":
    args = parse_args()
    start_an_image_server(args.shader)