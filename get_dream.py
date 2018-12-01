import os
import json
import requests
import shutil
import subprocess
import zipfile

MAGIC_URL = "http://10.148.132.40:8888/create"
UNITY_DIRECTORY = "assets"
with open("dream.json") as f:
    data = json.load(f)

dream = data["dreamKeyword"]

r = requests.get(MAGIC_URL, stream=True, data=data)

if r.status_code == 200:
    with open(dream + ".zip", 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)

with zipfile.ZipFile(dream+".zip", 'r') as zip_ref:
    zip_ref.extractall(UNITY_DIRECTORY)

os.remove(dream + ".zip")