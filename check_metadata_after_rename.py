import os, json, shutil, re
from glob import glob
from tqdm import tqdm

FLASHDRIVE = "D:/"
FLASHDRIVE_TARGET = "D:/triptograms"
RENAMING_FILE = os.path.join(FLASHDRIVE, "FILE_REMAPPINGS.1.json")
LOCAL_TRIPTOGRAMS = "./triptograms"

def _normalize(fp):
    return os.path.abspath(fp).replace("\\","/")


def _compare_attribute_dicts(A_dict, B_dict, A_fp, B_fp):
    differences = {}
    A_keys = set(list(A_dict))
    B_keys = set(list(B_dict))
    A_less_B = A_keys - B_keys
    for key in A_less_B:
        differences[key] = [A_dict[key],None]
    B_less_A = B_keys - A_keys
    for key in B_less_A:
        differences[key] = [None,B_dict[key]]
    AB = A_keys & B_keys
    for key in AB:
        if A_dict[key] != B_dict[key]:
            differences[key] = [A_dict[key],B_dict[key]]
    return differences

def do_it():

    with open(RENAMING_FILE, "r") as f:
        new_2_old = dict([ (_normalize(new), _normalize(old)) for (old,new) in json.load(f) ])
    #print(json.dumps(new_2_old, indent = 1))

    #print(list(new_2_old.items())[:5])

    flashdrive_json_fps = sorted([ fp for fp in glob(os.path.join(FLASHDRIVE_TARGET, "*.json")) if re.match(r"\d+\.json", os.path.basename(fp)) ],
        key = lambda fp: int(os.path.basename(fp).split(".")[0]))

    for flashdrive_json_fp in tqdm((flashdrive_json_fps)):

        with open(flashdrive_json_fp) as f:
            flashdrive_json_string = json.dumps(json.load(f)["attributes"],indent=1)

        old_json_fp = new_2_old.get(_normalize(flashdrive_json_fp))
        if old_json_fp is None:
            old_json_fp = flashdrive_json_fp

        local_json_fp = os.path.join(LOCAL_TRIPTOGRAMS, os.path.basename(old_json_fp))
        with open(local_json_fp, "r") as f:
            local_json_string = json.dumps(json.load(f)["attributes"],indent=1)

        if flashdrive_json_string != local_json_string:
            print(flashdrive_json_fp, "<>", local_json_fp)
            A_dict = { x["trait_type"] : x["value"] for x in json.load(open(flashdrive_json_fp,"r"))["attributes"] }
            B_dict = { x["trait_type"] : x["value"] for x in json.load(open(local_json_fp,"r"))["attributes"] }
            differences = _compare_attribute_dicts(A_dict = A_dict, B_dict = B_dict, A_fp = flashdrive_json_fp, B_fp = local_json_fp)
            print(json.dumps(differences, indent = 1))
            print("")

        with open(flashdrive_json_fp, "r") as f:
            fp_image_number = os.path.basename(flashdrive_json_fp).split(".")[0]
            image_number = json.load(f)["image"].split(".")[0]
            if fp_image_number != image_number:
                print(fp_image_number, "<>", image_number)


if __name__ == "__main__":
    do_it()