from flask import Flask, request, send_from_directory
from create_dream import create_dream

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

@app.route('/create')
def create_dream():
    dream =request.args.get("dreamKeyword")
    numNPCTexts = request.args.get("numNPCTexts")
    numObjects = request.args.get("numObjects")
    numPeople = request.args.get("numPeople")
    data = {"dreamKeyword":dream, "numNPCTexts": numNPCTexts, "numObjects": numObjects, "numPeople" : numPeople}
    create_dream(data)
    return send_from_directory(dream + ".zip")

@app.route('/')
def test():
    return send_from_directory(".","test.zip")

if __name__ == "__main__":
    app.run(host='0.0.0.0')