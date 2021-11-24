from argparse import ArgumentParser
import sys, os, shutil, re
import time
from glob import glob
from collections import defaultdict
from tqdm import tqdm
import ffmpeg
from PIL import Image

FLASHDRIVE = "D:/"

def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--shader", type = str, default = "triptograms")
    parser.add_argument("--dry_run", type = str, choices = ("y","n"))
    return parser.parse_args()

def confirm_ok_delete_target(target):
    msg1 = "This will DELETE the contents of '{}'".format(target)
    msg2 = "If this OK? (THINK CAREFULLY!) y/n"
    print(msg1)
    response = input(msg2)
    if response.lower() not in ("y","n"):
        print("Unknown response: '{}'".format(response))
    elif response.lower() == "n":
        print("Ok, see ya!")
        sys.exit()
    else:
        pass

def do_it(args):

    # Cleanup
    FLASHDRIVE_TARGET = os.path.join(FLASHDRIVE, args.shader)
    os.makedirs(FLASHDRIVE_TARGET, exist_ok = True)

    metadata_json_fps = [ x for x in glob(os.path.join(args.shader, "*.json")) if re.match(r"\d+\.json", os.path.basename(x)) ]

    print('Found {} items'.format(len(metadata_json_fps)))

    retries = defaultdict(lambda: 0)
    all_files = []
    for metadata_json_fp in metadata_json_fps:

        image_number = int(os.path.basename(metadata_json_fp).split(".")[0])
        
        image_fname = "{}.cover.gif".format(image_number)
        src_image = os.path.join(args.shader, image_fname)

        animation_fname = "{}.mp4".format(image_number)
        src_animation = os.path.join(args.shader, animation_fname)

        metadata_fname ="{}.json".format(image_number)
        src_metadata  = os.path.join(args.shader, metadata_fname)

        files = [ src_image, src_animation, src_metadata ]

        all_files.extend(files)

    all_files_bak = all_files.copy()

    with tqdm(total = len(all_files)) as pbar:
        while len(all_files) > 0:

            fp = all_files.pop()

            flashdrive_fp = os.path.join(FLASHDRIVE_TARGET, os.path.basename(fp))
            if args.dry_run == "n":
                try:
                    if not os.path.exists(flashdrive_fp):
                        shutil.copy2(fp, flashdrive_fp)
                        pbar.update(1)
                    else:
                        pbar.update(1)
                except:
                    time.sleep(0.5)
                    retries[fp] += 1
                    if retries[fp] < 20:
                        all_files.insert(0, fp)
                    else:
                        print("Exceeded 20 retries for '{}'".format(fp))
            else:
                print("{}->{}".format(fp, flashdrive_fp))
        
    missing = []
    print("Checking that all files were copied.")
    for fp in tqdm(all_files_bak):
        flashdrive_fp = os.path.join(FLASHDRIVE_TARGET, os.path.basename(fp))
        if not os.path.exists(FLASHDRIVE):
            while True:
                print("Could not find flashdrive.  Retrying.")
                time.sleep(0.5)
                if os.path.exists(FLASHDRIVE):
                    print("Found. continuing.")
                    break
        if not os.path.exists(flashdrive_fp):
            missing.append(flashdrive_fp)
    
    if len(missing) > 0:
        print("Found {} missing files".format(len(missing)))

    # untested
    empty_files = []
    print("Checking for any empty files out of {} files".format(len(all_files_bak)))
    for fp in tqdm(all_files_bak):
        if os.stat(fp).st_size == 0:
            empty_files.append(fp)

    if len(empty_files) > 0:
        print("Found {} empty files (probably error in copying file)".format(len(empty_files)))
        print("\n".join(empty_files))
    
    if len(missing) == 0 and len(empty_files) == 0:
        print("All {} files found.".format(len(all_files_bak)))

    # untested
    corrupt_mp4s = []
    mp4_fps = glob(os.path.join(FLASHDRIVE_TARGET, "*.mp4"))
    print("Verifying {} mp4s".format(len(mp4_fps)))
    for mp4_fp in tqdm(mp4_fps):
        try:
            (
                ffmpeg
                .input(mp4_fp)
                .output("null", f="null")
                .run()
            )
        except ffmpeg._run.Error:
            corrupt_mp4s.append(mp4_fp)
        else:
            pass

    if len(corrupt_mp4s) > 0:
        print("Found {} corrupt mp4s".format(len(corrupt_mp4s)))
        print("\n".join(corrupt_mp4s))

    # Untested
    corrupt_gifs = []
    gif_fps = glob(os.path.join(FLASHDRIVE_TARGET, "*.gif"))
    print("Verifying {} gifs".format(len(gif_fps)))
    for gif_fp in gif_fps:
        try:
            im = Image.load(gif_fp)
            for i in range(im.n_frames):
                im.seek(i)
                im.verify() #I perform also verify, don't know if he sees other types o defects
                im.close() #reload is necessary in my case
                im = Image.load(gif_fp) 
                im.transpose(Image.FLIP_LEFT_RIGHT)
            im.close()
        except: 
            corrupt_gifs.append(gif_fp)
    
    if len(corrupt_gifs) > 0:
        print("Found {} corrupt gifs".format(len(corrupt_gifs)))
        print("\n".join(corrupt_gifs))

if __name__ == "__main__":
    args = parse_args()
    do_it(args)


