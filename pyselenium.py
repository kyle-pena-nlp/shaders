from argparse import ArgumentParser
import pygifsicle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import base64
import numpy as np
import imageio
from tqdm import tqdm
import os
from io import BytesIO
from apng import APNG, PNG
from PIL import Image
from PIL.Image import ADAPTIVE

# For Windows, install gifsicle and add it to your PATH
# Otherwise use apt-get or brew
from pygifsicle import optimize

COMPRESS = True

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--url", type = str, default = "file:///C:/git/SHADERS/EXAMPLE/1.html")
    parser.add_argument("--x", type=int, default = 300)
    parser.add_argument("--y", type=int, default = 300)
    parser.add_argument("--frames_per_second", type = int, default = 25)
    parser.add_argument("--num_seconds", type = int, default = 10)
    parser.add_argument("--out", type = str, default = "C:/git/SHADERS/EXAMPLE/1.gif")
    parser.add_argument("--format", type = str, choices = ["gif","mp4"])
    args = parser.parse_args()
    return args

def wait_until_ready(driver):
    while True:
        status = driver.execute_script("return app.status;")
        if status == "ready":
            print("Page is ready.")
            break


# TODO: PIL APNG writer

class APNGWriter:
    """
        A funny little wrapper around the APNG library
    """

    def __init__(self, fpath, fps):
        self.fpath = fpath
        self.fps = fps
        self.apng = APNG(num_plays = 0)
        self.saved = False

    def append_data(self, data):
        image_bytes = self._ensure_is_png_bytes(data)
        png = PNG.from_bytes(image_bytes)
        
        self.apng.append(png, delay = 1, delay_den = self.fps)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._maybe_save()
        else:
            raise exc_val

    def close(self):
        if not self.saved:
            self._maybe_save()

    def _maybe_save(self):
        if not self.saved:
            try:
                self.apng.save(self.fpath)
                self.saved = True
            except Exception as e:
                print("Saving apng failed.")
                raise e

    def _ensure_is_png_bytes(self, image):
        if type(image) == bytes:
            return image
        elif type(image) == np.ndarray:
            raise Exception("Was NDARRAY")
        else:
            raise Exception("Not bytes or a numpy array")

def get_writer(frames_per_second, out, out_format, compress):
    fpath = out
    print("Writing to '{}'".format(fpath))
    if out_format == "gif":
        return imageio.get_writer(fpath, mode='I', duration = (1/frames_per_second), subrectangles = True )
    elif out_format == "mp4":
        #quality = 8 if compress else 10
        # bitrate set for compatibility with twitter
        return imageio.get_writer(fpath, mode='I', fps=frames_per_second, quality = 9) # codec="H264", 
    elif out_format == "png":
        return APNGWriter(fpath, fps = frames_per_second)
        #return imageio.get_writer(fpath, mode = 'I', duration = (1/frames_per_second))
    else:
        raise Exception("Unknown format: '{}'".format(out_format))

def to_optimized_path(fpath):
    # assumes fpath has an extension
    dirname = os.path.dirname(fpath)
    fname = os.path.basename(fpath)
    name,ext = fname.rsplit(".")
    return os.path.join(dirname, ".".join(["-".join([name,"optimized"]), ext]))

def get_canvas_image_bytes(time, x, y, driver):
    # Interact with the HTML page to get the png bytes from it
    capture_script = "capture({},{},{}); return app.capture;".format(time,x,y)
    img_data = driver.execute_script(capture_script)
    image_bytes  = base64.b64decode(img_data)
    return image_bytes

def bytes_to_PIL(image_bytes):
    png_img = imageio.imread(image_bytes, "png")
    PIL_img = Image.fromarray(png_img, mode = "RGBA")
    return PIL_img

def get_palette(img):
    if type(img) == bytes:
        PIL_img = bytes_to_PIL(img)
    else:
        PIL_img = img
    quantized = PIL_img.convert("RGB").convert(palette = ADAPTIVE, colors = 256)
    return quantized.palette

def palettize(PIL_img, palette, adaptive = False):
    if adaptive:
        palette = get_palette(PIL_img)
    return PIL_img.convert("RGB").convert(palette = palette, dither = "FLOYDSTEINBERG")


def convert_img(image_bytes, out_format, palette, compress):
    
    if out_format in ("gif",):
        PIL_img = bytes_to_PIL(image_bytes)
        palettized = palettize(PIL_img, palette, adaptive= True)
        return np.asarray(palettized) # todo: convert to PIL?
    elif out_format in ("mp4",):
        return imageio.imread(image_bytes, "png")
    elif out_format in ("png",):
        if compress:
            PIL_img = bytes_to_PIL(image_bytes)
            palettized = palettize(PIL_img, palette)
            with BytesIO() as b:
                palettized.save(b, format = "png", optimize = True, quality = 85)
                b.seek(0)
                return b.read()
        else:
            #PIL_img = bytes_to_PIL(image_bytes)
            #palettized = palettize(PIL_img, palette)
            #with BytesIO() as b:
            #    palettized.save(b, format = "png", optimize = True, quality = 85)
            #    b.seek(0)
            #    return b.read()            
            
            return image_bytes
            
            #PIL_img = bytes_to_PIL(image_bytes)
            #with BytesIO() as b:
            #    # We save a little bit by dropping the alpha channel
            #    PIL_img.convert("RGB").save(b, format = "png", optimize = True)
            #    b.seek(0)
            #    return b.read()
    else:
        raise Exception("Unknown format: '{}'".format(out_format))

def export(url, x, y, frames_per_second, num_seconds, out, out_format, compress):
    
    chrome_options = Options()

    # Disable CORS so we can load the png compression shim for canvas toDataURI without bundling it into the main HTML file

    with webdriver.Chrome(chrome_options=chrome_options) as driver:

        driver.get(url)
        
        # Wait until initialized
        wait_until_ready(driver)
        
        # Stop the animation
        driver.execute_script("stop()")

        out = replace_ext(out, out_format)

        with get_writer(frames_per_second=frames_per_second, out = out, out_format = out_format, compress = compress) as writer:

            times = np.linspace(0, num_seconds, num = frames_per_second * num_seconds, endpoint = False)
            
            palette = None

            for i, time in enumerate(tqdm(times, leave = False)):

                image_bytes = get_canvas_image_bytes(time, x, y, driver)

                if i == 0:
                    palette = get_palette(image_bytes)

                png_img = convert_img(image_bytes, out_format, palette, compress)

                writer.append_data(png_img)

            writer.close()
        
        if format == "gif" and compress:
            print("Optimizing gif.")
            optimized_out = to_optimized_path(out)
            pygifsicle.optimize(out, destination = optimized_out, colors = 256)

        driver.close()

    print("Done.")
            

def replace_ext(fpath, new_ext):
    dirname = os.path.dirname(fpath)
    fname = os.path.basename(fpath)
    if "." in fname:
        fname,*_ext = fname.rsplit(".",1)
    return os.path.join(dirname, ".".join([fname, new_ext]))

if __name__ == "__main__":
    args = parse_args()
    export(url = args.url, x = args.x, y = args.y, frames_per_second = args.frames_per_second, num_seconds = args.num_seconds, out=args.out, format = args.format)


"""
var canvas = document.getElementById("canvas");
var dataURL = canvas.toDataURL("image/png");
var newTab = window.open('about:blank','image from canvas');
newTab.document.write("<img src='" + dataURL + "' alt='from canvas'/>");

"""