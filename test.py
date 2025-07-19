from flask import Flask, request

app = Flask(__name__)

@app.route("/result", methods=["POST"])
def result():
    data = request.get_json()
    print("Final Result from ESP8266:", data)
    return "Received", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
