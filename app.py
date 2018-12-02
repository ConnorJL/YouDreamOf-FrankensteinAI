from flask import Flask, request, send_from_directory
from create_dream import create_dream

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

@app.route('/')
def send_zip():
    data = {}
    data["dreamKeyword"] = request.args.get('dreanKeyword')
    data["numNPCTexts"] = request.args.get('numNPCTexts')
    data["numObjects"] = request.args.get('numObjects')
    data["numPeople"] = requests.args.get("numPeople")

    create_dream(data)

    return send_from_directory('.', data["dreamKeyword"]+".zip")

if __name__ == "__main__":
    app.run()