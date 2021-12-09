import os, json
from glob import glob
from tqdm import tqdm
DRY_RUN = False
fps = glob("D:/triptograms/*.json")
for fp in tqdm(fps):
    print(fp)
    x = json.load(open(fp,"r"))
    #fp_num = os.path.basename(fp).split(".")[0]
    image_num = int(x["image"].split(".")[0])
    x["name"] = "Triptograms #{}".format(image_num+1)
    x["collection"]["family"] = "Triptograms"
    x["collection"]["name"] = "Triptograms"
    if not DRY_RUN:
        with open(fp, "w+") as f:
            json.dump(x,f)