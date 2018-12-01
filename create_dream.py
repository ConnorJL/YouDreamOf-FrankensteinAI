import glob
import json
import os
import random
import subprocess
import six
import zipfile

import cv2 as cv
from google.cloud import language
from google.cloud.language import enums, types
from PIL import Image  # Image from PIL

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/connor/youdreamof.json"
MAX_ITERATIONS = 5

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

    for entity in entities:
        print('=' * 20)
        print(u'{:<16}: {}'.format('name', entity.name))
        print(u'{:<16}: {}'.format('type', entity_type[entity.type]))
        print(u'{:<16}: {}'.format('metadata', entity.metadata))
        print(u'{:<16}: {}'.format('salience', entity.salience))
        print(u'{:<16}: {}'.format('wikipedia_url',
              entity.metadata.get('wikipedia_url', '-')))

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

    subprocess.call(["python3", "download.py", "-s", word, "-d", folder, "-n", "10"])

def imgCrop(image, cropBox, boxScale=1):
    # Crop a PIL image with the provided box [x(left), y(upper), w(width), h(height)]

    # Calculate scale factors
    xDelta=max(cropBox[2]*(boxScale-1),0)
    yDelta=max(cropBox[3]*(boxScale-1),0)

    # Convert cv box to PIL box [left, upper, right, lower]
    PIL_box=[cropBox[0]-xDelta, cropBox[1]-yDelta, cropBox[0]+cropBox[2]+xDelta, cropBox[1]+cropBox[3]+yDelta]

    return image.crop(PIL_box)

def faceCrop(imagePattern, boxScale=1):
    face_cascade = cv.CascadeClassifier('haarcascade_frontalface_alt.xml')

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

def make_text(speaker, start, amount, file):
    subprocess.call(["python3", "tensorflow-char-rnn/sample.py", "--init_dir=" + os.path.join("tensorflow-char-rnn", speaker), "--start_text=" + start, "--length="+str(amount), ">", file])

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

def create_dream(data):
    # Takes in the dict from Unity, finishes by creatig a 'dream'.zip
    dream = data["dreamKeyword"]
    if not os.path.exists(dream):
        os.mkdir(dream)
    os.chdir(dream)
    words = get_related_words(data["dreamKeyword"])
    words.add(dream)

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
    while num_people < data["numPeople"] and num_iterations < MAX_ITERATIONS:
        word = random.sample(words, 1)[0]
        for new_word in get_related_words(word):
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
        num_iterations += 1

    print(entities)
    print("Num people: " + str(len(entities["PERSON"])))

    # Select number of people, items, etc
    people = random.sample(list(entities["PERSON"]), data["numPeople"])
    if dream in list(entities["PERSON"]) and not dream in people:
        people[:-1].append(dream)

    items = random.sample(list(entities["WORK_OF_ART"]+entities["CONSUMER_GOOD"]+entities["OTHER"]), data["numObjects"])

    for word in people:
        get_images(word, word)
        faceCrop(os.path.join(word, "*"))

    for word in items:
        get_images(word, word)
        get_images(word, word)


    # Style, modify and move images

    # Create image json
    out_data = {"data": []}
    for person in people:
        record = {"keyword": person, "type":1}
        if person == dream:
            record["dreamTarget"] = True
        else:
            record["dreamTarget"] = False

        files = [ f for f in os.listdir(os.path.join(person, "finished") ) if os.path.isfile(f) and not "crop" in f]
        files = random.sample(files, 5)

        faces = [ f for f in os.listdir(os.path.join(person, "finished") ) if os.path.isfile(f) and "crop" in f]
        faces = random.sample(faces, 5)

        record["generalImages"] = files
        record["faceImages"] = faces

        out_data["data"].append(record)

    for item in items:
        record = {"keyword": item, "type":0}
        if item == dream:
            record["dreamTarget"] = True
        else:
            record["dreamTarget"] = False

        files = [ f for f in os.listdir(os.path.join(person, "finished") ) if os.path.isfile(f)]
        files = random.sample(files, 5)

        record["generalImages"] = files

        out_data["data"].append(record)

    
    

    # Generate the texts needed
    # Call RNN
    # Analyze with Google
    # Postprocess

    # Write jsons



    #zipf = zipfile.ZipFile(os.path.join("..", dream + ".zip"), 'w', zipfile.ZIP_DEFLATED)
    #zipdir(".", zipf)
    #zipf.close()


#make_tileable("organic_border.png", "out5.png")
#data = json.load(open("sample.json", "r"))
#create_dream(data)
#print(get_related_words("Nicholas Cage"))

#get_images("Nicolas Cage", "cage")

#faceCrop('cage/*', boxScale=1)

#entities_text("Nicolas Kim Coppola (born January 7, 1964),[3] known professionally as Nicolas Cage, is an American actor, director and producer. During his early career, Cage starred in a variety of films such as Valley Girl (1983), Racing with the Moon (1984), Birdy (1984), Peggy Sue Got Married (1986), Raising Arizona (1987), Moonstruck (1987), Vampire's Kiss (1989), Wild at Heart (1990), Fire Birds (1990), Honeymoon in Vegas (1992), and Red Rock West (1993). ")

