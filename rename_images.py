import os, re, json, time, sys
from glob import glob
DRY_RUN = False
from tqdm import tqdm

FLASHDRIVE = "D:/"
FLASHDRIVE_TARGET = "D:/triptograms"

FILE_REMAPPINGS = []
PROPERTY_MAPPINGS = []
READ_FILES = []
WRITTEN_FILES = []

def _next_json_fname(fname):
    current = glob(os.path.join(FLASHDRIVE, fname + ".*.json"))
    if len(current) == 0:
        return fname + ".1.json"
    else:
        numbers = [ int(os.path.basename(fp).split(".")[1]) for fp in current ]
        return fname + "." + str(max(numbers)+1) + ".json"

def _write_log(fname, content):
    with open(os.path.join(FLASHDRIVE, _next_json_fname(fname)), "w+") as f:
        json.dump(content, f, indent = 1)

def get_number(fp):
    return int(os.path.basename(fp).split(".")[0])

def rename_json(i, image_number):
    # Rename JSON
    old_fp = os.path.join(FLASHDRIVE_TARGET, "{}.json".format(image_number))
    new_fp = os.path.join(FLASHDRIVE_TARGET, "{}.json".format(i))
    if old_fp != new_fp:
        while True:
            try:
                print("Rename {}->{}".format(old_fp, new_fp))
                os.rename(old_fp, new_fp)
                FILE_REMAPPINGS.append((old_fp, new_fp))
                break
            except:
                print("   Retry.")
                time.sleep(0.25)
                pass

def rename_json_fields(i):

    json_fp = os.path.join(FLASHDRIVE_TARGET, "{}.json".format(i))
    image_fname = "{}.gif".format(i)

    # re-read contents of JSON
    while True:
        try:
            with open(json_fp, "r") as f:
                print("Reading {}".format(json_fp))
                metadata_json = json.load(f)
                READ_FILES.append(json_fp)
                break
        except:
            print("   Retry.")
            time.sleep(0.25)
    
    # Re-map to new image filename
    PROPERTY_MAPPINGS.append(["image", metadata_json["image"], image_fname])
    metadata_json["image"] = image_fname

    PROPERTY_MAPPINGS.append(["properites.files[0].uri", metadata_json["properties"]["files"][0]["uri"], image_fname])
    metadata_json["properties"]["files"][0]["uri"] = image_fname

    # Write back to disk
    while True:
        try:
            print("Writing {}".format(json_fp))
            with open(json_fp, "w+") as f:
                json.dump(metadata_json, f, indent = 1)
                WRITTEN_FILES.append(json_fp)
                break
        except:
            print("   Retry")
            time.sleep(0.25)

def rename_gif(i, image_number):
    # Rename GIF
    old_fp = os.path.join(FLASHDRIVE_TARGET, "{}.gif".format(image_number))
    new_fp = os.path.join(FLASHDRIVE_TARGET, "{}.gif".format(i))
    
    if old_fp != new_fp:
        while True:
            try:
                print("Rename {}->{}".format(old_fp,new_fp))
                os.rename(old_fp, new_fp)    
                FILE_REMAPPINGS.append((old_fp, new_fp))                
                break
            except:
                print("   Retry")
                time.sleep(0.25)

def do_it():
    image_numbers = [ int(os.path.basename(fp).split(".")[0]) for fp in glob(os.path.join(FLASHDRIVE_TARGET, "*.json")) if re.match(r"\d+\.json", os.path.basename(fp)) ]    
    image_numbers = sorted(set(image_numbers))

    gaps = set(range(max(image_numbers))) - set(image_numbers)
    print(gaps)

    for i, image_number in tqdm(enumerate(image_numbers), total = len(image_numbers)):
        
        # Rename image_number.json to i.json
        rename_json(i, image_number)
        
        # Load up i.json and make sure its image references are i.json, write back to disk
        rename_json_fields(i)
        
        # Rename image_number.gif to i.gif
        rename_gif(i, image_number)

    _write_log("FILE_REMAPPINGS", FILE_REMAPPINGS)
    _write_log("PROPERTY_MAPPINGS", PROPERTY_MAPPINGS)
    _write_log("READ_FILES", READ_FILES)
    _write_log("WRITTEN_FILES", WRITTEN_FILES)

if __name__ == "__main__":
    do_it()