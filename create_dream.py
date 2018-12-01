import json
import subprocess
import os

def get_related_words(word):
    subprocess.call(["node", "google_trends.js", word])
    with open("google_trends.json", "r") as f:
        data = json.load(f)
    data = data["default"]["rankedList"][1]["rankedKeyword"]
    words = []
    for d in data:
     word = d["topic"]["title"]
     words.append(word)

    return words

def get_images(word, folder):
    if not os.path.exists(folder):
        os.mkdir(folder)

    subprocess.call(["python3", "download.py", "-s", word, "-d", folder, "-n", "20"])


def create_dream(file):
    with open(file, "r") as f:
        data = json.load(f)
    
print(get_related_words("Nicholas Cage"))

get_images("Nicolas Cage", "cage")