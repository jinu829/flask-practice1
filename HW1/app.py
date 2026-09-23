from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def printschoolinfo():
    return render_template("schoolinformation.html")

@app.route("/profile")
def hobby():
    hobby_list = ["게임", "음악 감상", "주식"]
    return render_template("hobbies.html", hobbies = hobby_list)

@app.route("/greet/<name>")
def greet(name):
    return render_template("greeting.html", name = name)

if __name__ == "__main__":
    app.run(debug=True)