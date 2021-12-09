import os, json
from glob import glob
fps = glob("D:/triptograms/*.json")
for fp in fps:
   x = json.load(open(fp,"r"))
   name_image_num = str(int(x["name"].split("#")[1]) - 1)
   fp_num = os.path.basename(fp).split(".")[0]
   image_num = x["image"].split(".")[0]
   file_num = x["properties"]["files"][0]["uri"].split(".")[0]
   if fp_num != image_num or fp_num != file_num or image_num != file_num:
      print(fp_num,image_num,file_num)
   if fp_num != name_image_num:
      print(fp_num, name_image_num)