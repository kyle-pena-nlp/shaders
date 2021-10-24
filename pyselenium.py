from argparse import ArgumentParser
import pygifsicle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import base64
import numpy as np
import imageio
from tqdm import tqdm
import os

# For Windows, install gifsicle and add it to your PATH
# Otherwise use apt-get or brew
from pygifsicle import optimize

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

def get_writer(frames_per_second, out, format):
    fpath = out
    print("Writing to '{}'".format(fpath))
    if format == "gif":
        return imageio.get_writer(fpath, mode='I', duration = (1/frames_per_second), subrectangles = True )
    elif format == "mp4":
        return imageio.get_writer(fpath, fps=frames_per_second)
    else:
        raise Exception("unknown format: {}".format(format))

def to_optimized_path(fpath):
    # assumes fpath has an extension
    dirname = os.path.dirname(fpath)
    fname = os.path.basename(fpath)
    name,ext = fname.rsplit(".")
    return os.path.join(dirname, ".".join(["-".join([name,"optimized"]), ext]))

def export(url, x, y, frames_per_second, num_seconds, out, format):
    chrome_options = Options()
    #chrome_options.add_argument("--window-size={},{}".format(x,y))
    with webdriver.Chrome(chrome_options=chrome_options) as driver:

        driver.get(url)
        
        # Wait until initialized
        wait_until_ready(driver)
        
        # Stop the animation
        driver.execute_script("stop()")

        out = replace_ext(out, format)

        with get_writer(frames_per_second=frames_per_second, out = out, format = format) as writer:
            for time in tqdm(np.linspace(0, num_seconds, num = frames_per_second * num_seconds, endpoint = False)):
                capture_script = "capture({},{},{}); return app.capture;".format(time,x,y)
                img_data = driver.execute_script(capture_script)
                #with open(r"canvas.png", 'wb') as f:
                decoded =base64.b64decode(img_data)
                png_img = imageio.imread(decoded, "png")
                writer.append_data(png_img)

            writer.close()
        
        if format == "gif":
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