import glob
import json
import os
import random
import shutil
import subprocess
import six
import zipfile

import cv2 as cv
from google.cloud import language
from google.cloud.language import enums, types
from PIL import Image  # Image from PIL


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/connor/youdreamof.json"
MAX_ITERATIONS = 5
NUM_VOICES = 3
VOICE_SPLIT_LINE = "Sampled text is:"
AVG_LINE_LENGTH = 100

def id_to_speaker(id):
    if id == 1:
        return "shakespeare"
    if id == 2:
        return "skyrim"
    if id == 3:
        return "southpark"

def entities_text(text):
    """Detects entities in the text."""
    client = language.LanguageServiceClient()

    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')

    # Instantiates a plain text document.
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    # Detects entities in the document. You can also analyze HTML with:
    #   document.type == enums.Document.Type.HTML
    entities = client.analyze_entities(document).entities

    # entity types from enums.Entity.Type
    entity_type = ('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION',
                   'EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER')

    #for entity in entities:
    #    print('=' * 20)
    #    print(u'{:<16}: {}'.format('name', entity.name))
    #    print(u'{:<16}: {}'.format('type', entity_type[entity.type]))
    #    print(u'{:<16}: {}'.format('metadata', entity.metadata))
    #    print(u'{:<16}: {}'.format('salience', entity.salience))
    #    print(u'{:<16}: {}'.format('wikipedia_url',
    #          entity.metadata.get('wikipedia_url', '-')))

    return entities

def syntax_text(text):
    """Detects syntax in the text."""
    client = language.LanguageServiceClient()

    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')

    # Instantiates a plain text document.
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    # Detects syntax in the document. You can also analyze HTML with:
    #   document.type == enums.Document.Type.HTML
    tokens = client.analyze_syntax(document).tokens

    # part-of-speech tags from enums.PartOfSpeech.Tag
    pos_tag = ('UNKNOWN', 'ADJ', 'ADP', 'ADV', 'CONJ', 'DET', 'NOUN', 'NUM',
               'PRON', 'PRT', 'PUNCT', 'VERB', 'X', 'AFFIX')

    for token in tokens:
        print(u'{}: {}'.format(pos_tag[token.part_of_speech.tag],
                               token.text.content))

def get_related_words(word):
    subprocess.call(["node", "../google_trends.js", word])
    with open("google_trends.json", "r") as f:
        data = json.load(f)
    data = data["default"]["rankedList"][1]["rankedKeyword"]
    words = []
    for d in data:
     word = d["topic"]["title"]
     words.append(word)

    return set(words)

def get_images(word, folder):
    if not os.path.exists(folder):
        os.mkdir(folder)

    subprocess.call(["python3", "../download.py", "-s", word, "-d", folder, "-n", "10"])

def imgCrop(image, cropBox, boxScale=1):
    # Crop a PIL image with the provided box [x(left), y(upper), w(width), h(height)]

    # Calculate scale factors
    xDelta=max(cropBox[2]*(boxScale-1),0)
    yDelta=max(cropBox[3]*(boxScale-1),0)

    # Convert cv box to PIL box [left, upper, right, lower]
    PIL_box=[cropBox[0]-xDelta, cropBox[1]-yDelta, cropBox[0]+cropBox[2]+xDelta, cropBox[1]+cropBox[3]+yDelta]

    return image.crop(PIL_box)

def faceCrop(imagePattern, boxScale=1):
    face_cascade = cv.CascadeClassifier('../haarcascade_frontalface_alt.xml')

    imgList=glob.glob(imagePattern)
    if len(imgList)<=0:
        print('No Images Found')
        return

    for img in imgList:
        try:
            pil_im=Image.open(img)
            cv_im = cv.imread(img)
            gray = cv.cvtColor(cv_im, cv.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            for i, (x,y,w,h) in enumerate(faces):
                croppedImage=imgCrop(pil_im, (x,y,w,h),boxScale=boxScale)
                fname,ext=os.path.splitext(img)
                croppedImage.save(fname+'_crop'+str(i)+ext)
        except:
            continue

def make_tileable(foreground, background):
    background = Image.open(background).resize((512, 512))
    foreground = Image.open(foreground).resize((512, 512))

    background.paste(foreground, (0, 0), foreground)
    name = background.split(".")[0]
    background.save(name + "_combined.png")

def make_text(speaker, start, amount):
    speaker = id_to_speaker(speaker)
    subprocess.call(["python3", "tensorflow-char-rnn/sample.py", "--init_dir=" + os.path.join("tensorflow-char-rnn", speaker), "--start_text=" + start, "--length="+str(amount), ">", speaker+".tmp"])
    with open(speaker+".tmp", "r") as f:
        lines = f.read().split(VOICE_SPLIT_LINE[-1])
    return lines

def process_text(lines, our_entities):
    # Replace names with ours
    entities_extract = entities_text(lines)
    entity_type = ('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION',
                   'EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER')

    entities = {}
    for e_t in entity_type:
        entities[e_t] = set()

    for entity in entities_extract:
        name = entity.name
        t = entities[entity_type[entity.type]].add(name)

    for t in entity_type:
        if len(our_entities[t]) == 0:
            continue
        for thing in entities[t]:
            if(len(our_entities[t]) == 0):
                lines.replace(entity, "")
            else:
                try:
                    lines.replace(entity, random.sample(list(our_entities[t]), 1))
                except:
                    pass

    return lines


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

def create_dream(data):
    # Takes in the dict from Unity, finishes by creatig a 'dream'.zip
    dream = data["dreamKeyword"].replace("/", "")
    if not os.path.exists(dream):
        os.mkdir(dream)
    os.chdir(dream)
    words_dirty = get_related_words(data["dreamKeyword"])
    words = set()
    for word in words_dirty:
        word = word.replace("/", "")
        if len(word) > 40:
            word = word[:40]
        words.add(word)
    
    words.add(dream)
    print("Got first words: " + str(words) +"\n")

    # Understand our words with google
    words_s = " ".join(words)
    entities_extract = entities_text(words_s)
    entity_type = ('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION',
                   'EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER')

    entities = {}
    for e_t in entity_type:
        entities[e_t] = set()

    for entity in entities_extract:
        name = entity.name
        t = entities[entity_type[entity.type]].add(name)

    # See if we have enough entities/persons
    # If not enough, expand things further if necessary and keep going
    num_people = len(entities["PERSON"])
    num_iterations = 0
    while num_people < data["numPeople"]:
        word = random.sample(words, 1)[0]
        for new_word in get_related_words(word):
            new_word = new_word.replace("/", "")
            if len(new_word) > 40:
                new_word = new_word[:40]
            words.add(new_word)

        # Understand our words with google
        words_s = " ".join(words)
        entities_extract = entities_text(words_s)
        entity_type = ('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION',
                    'EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER')

        for entity in entities_extract:
            name = entity.name
            t = entities[entity_type[entity.type]].add(name)

        num_people = len(entities["PERSON"])

    num_iterations = 0
    num_objects = len(entities["WORK_OF_ART"].union(entities["CONSUMER_GOOD"].union(entities["OTHER"])))

    while num_objects < data["numObjects"]:
        word = random.sample(words, 1)[0]
        for new_word in get_related_words(word):
            new_word = new_word.replace("/", "")
            words.add(new_word)

        # Understand our words with google
        words_s = " ".join(words)
        entities_extract = entities_text(words_s)
        entity_type = ('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION',
                    'EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER')

        for entity in entities_extract:
            name = entity.name
            t = entities[entity_type[entity.type]].add(name)

        num_objects = len(entities["WORK_OF_ART"].union(entities["CONSUMER_GOOD"].union(entities["OTHER"])))
        num_iterations += 1

    print(entities)
    print("Num people: " + str(len(entities["PERSON"])))

    # Select number of people, items, etc
    people = random.sample(list(entities["PERSON"]), data["numPeople"])
    if dream in list(entities["PERSON"]) and not dream in people:
        people[:-1].append(dream)

    items = random.sample(list(entities["WORK_OF_ART"].union(entities["CONSUMER_GOOD"].union(entities["OTHER"]))), data["numObjects"])

    for word in people:
        get_images(word, word)
        faceCrop(os.path.join(word+"/*"))

    for word in items:
        get_images(word, word)


    # Style, modify and move images

    # Create image json
    if not os.path.exists("out"):
        os.mkdir("out")

    out_data = {"data": []}
    for person in people:
        record = {"keyword": person, "type":1}
        if person == dream:
            record["dreamTarget"] = True
        else:
            record["dreamTarget"] = False

        files = [ f for f in os.listdir(person ) if os.path.isfile(os.path.join(person, f)) and not "crop" in f]
        try:
            files = random.sample(files, 5)
        except:
            files = [ f for f in os.listdir(person ) if os.path.isfile(os.path.join(person, f)) and not "crop" in f]

        true_files = []
        for f in files:
            try:
                shutil.move(os.path.join(person, f), os.path.join("out", f))
                true_files.append(f)
            except:
                continue
            


        faces = [ f for f in os.listdir(person) if os.path.isfile(os.path.join(person, f)) and "crop" in f]
        try:
            faces = random.sample(faces, 5)
        except:
            faces = [ f for f in os.listdir(person) if os.path.isfile(os.path.join(person, f)) and "crop" in f]

        true_faces = []
        for f in faces:
            try:
                shutil.move(os.path.join(person, f), os.path.join("out", f))
                true_faces.append(f)
            except:
                continue


        record["generalImages"] = true_files
        record["faceImages"] = true_faces

        out_data["data"].append(record)

    for item in items:
        record = {"keyword": item, "type":0}
        if item == dream:
            record["dreamTarget"] = True
        else:
            record["dreamTarget"] = False

        files = [ f for f in os.listdir(item ) if os.path.isfile(os.path.join(item, f))]
        try:
            files = random.sample(files, 5)
        except:
            files = [ f for f in os.listdir(item ) if os.path.isfile(os.path.join(item, f))]

        true_files = []
        for f in files:
            try:
                shutil.move(os.path.join(item, f), os.path.join("out", f))
                true_files.append(f)
            except:
                continue
            

        record["generalImages"] = true_files

        out_data["data"].append(record)

    print("Generating text")
    # Generate the texts needed
    # Call RNN
    for i in range(data["numNPCTexts"]):
        voice = random.randint(1, NUM_VOICES)
        #lines = make_text(voice, "Hello ", random.randint(int(0.75*AVG_LINE_LENGTH), int(1.5*AVG_LINE_LENGTH)))
        lines = "Test"
        lines = process_text(lines, entities)
        print("Processed: " + lines)
        record = {"keyword": lines, "type": 3, "dreamTarget": False, "generalImages": [], "faceImages": [], "speechStyle": voice}

        out_data["data"].append(record)


    with open("out/data.json", "w") as f:
        json.dump(out_data, f)

    zipf = zipfile.ZipFile(os.path.join("..", dream + ".zip"), 'w', zipfile.ZIP_DEFLATED)
    os.chdir("out")
    zipdir(".", zipf)
    zipf.close()
    os.chdir("../..")


#make_tileable("organic_border.png", "out5.png")
data = json.load(open("sample.json", "r"))
create_dream(data)
#print(get_related_words("Nicholas Cage"))

#get_images("Nicolas Cage", "cage")

#faceCrop('cage/*', boxScale=1)

#entities_text("Nicolas Kim Coppola (born January 7, 1964),[3] known professionally as Nicolas Cage, is an American actor, director and producer. During his early career, Cage starred in a variety of films such as Valley Girl (1983), Racing with the Moon (1984), Birdy (1984), Peggy Sue Got Married (1986), Raising Arizona (1987), Moonstruck (1987), Vampire's Kiss (1989), Wild at Heart (1990), Fire Birds (1990), Honeymoon in Vegas (1992), and Red Rock West (1993). ")

