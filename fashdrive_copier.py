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

    src_file_sizes = {}
    for metadata_json_fp in metadata_json_fps:

        image_number = int(os.path.basename(metadata_json_fp).split(".")[0])
        
        image_fname = "{}.gif".format(image_number)
        src_image = os.path.join(args.shader, image_fname)
        src_file_sizes[image_fname] = os.stat(src_image).st_size

        metadata_fname ="{}.json".format(image_number)
        src_metadata  = os.path.join(args.shader, metadata_fname)
        src_file_sizes[metadata_fname] = os.stat(src_metadata).st_size

        files = [ src_image, src_metadata ]

        all_files.extend(files)

    all_files_bak = all_files.copy()

    with tqdm(total = len(all_files)) as pbar:
        while len(all_files) > 0:

            fp = all_files.pop()

            flashdrive_fp = os.path.join(FLASHDRIVE_TARGET, os.path.basename(fp))
            if args.dry_run == "n":
                try:
                    file_not_copied = (not os.path.exists(flashdrive_fp)) or (os.stat(flashdrive_fp).st_size == 0)
                    if file_not_copied:
                        shutil.copy2(fp, flashdrive_fp)
                        if os.stat(flashdrive_fp).st_size == 0:
                            print("Bad copy for {}".format(flashdrive_fp))
                            raise Exception("Bad copy.")
                        else:
                            pbar.update(1)
                    else:
                        pbar.update(1)
                except Exception as exc:
                    time.sleep(0.5)
                    print("Retrying {}: ({}) - {}".format(flashdrive_fp, retries[fp]+1, str(exc)))
                    retries[fp] += 1
                    # re-enqueue
                    all_files.insert(0, fp)
            else:
                print("{}->{}".format(fp, flashdrive_fp))
        
    missing = []
    print("Checking that all files were copied.")
    for fp in tqdm(all_files_bak):
        flashdrive_fp = os.path.join(FLASHDRIVE_TARGET, os.path.basename(fp))
        if not os.path.exists(FLASHDRIVE):
            retries = 0
            while True:
                if retries > 20:
                    break
                print("Could not find flashdrive.  Retrying.")
                time.sleep(0.5)
                if os.path.exists(FLASHDRIVE):
                    print("Found. continuing.")
                    break
                retries += 1
        if not os.path.exists(flashdrive_fp):
            missing.append(flashdrive_fp)
    
    if len(missing) > 0:
        print("Found {} missing files".format(len(missing)))

    # Checking all files are same sizes
    print("Checking for mismatched file sizes.")
    mismatched_file_sizes = []
    for fp in tqdm(all_files_bak):
        flashdrive_fp = os.path.join(FLASHDRIVE_TARGET, os.path.basename(fp))
        retries = 0
        st_size = None
        while True:
            if flashdrive_fp in missing or retries > 20:
                break
            try:
                st_size = os.stat(flashdrive_fp).st_size
                break
            except:
                time.sleep(0.1)
                retries += 1
        orig_st_size = src_file_sizes[os.path.basename(fp)]
        if st_size != orig_st_size:
            mismatched_file_sizes.append(os.path.basename(fp))
    if len(mismatched_file_sizes) > 0:
        print("{} mismatched file sizes".format(len(mismatched_file_sizes)))
        print("\n".join(mismatched_file_sizes))

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


if __name__ == "__main__":
    args = parse_args()
    do_it(args)


