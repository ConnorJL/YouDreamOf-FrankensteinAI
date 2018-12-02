from flask import Flask, request, send_from_directory
from create_dream import create_dream

# set the project root directory as the static folder, you can set others.
application = Flask(__name__, static_url_path='')

@application.route('/')
def send_zip():
    data = {}
    data["dreamKeyword"] = request.args.get(u'dreamKeyword')
    data["numNPCTexts"] = int(request.args.get(u'numNPCTexts'))
    data["numObjects"] = int(request.args.get(u'numObjects'))
    data["numPeople"] = int(request.args.get(u"numPeople"))

    print(request.args)

    create_dream(data)

    return send_from_directory('.', data["dreamKeyword"]+".zip")

if __name__ == "__main__":
    application.run(host="0.0.0.0")