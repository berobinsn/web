from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = '1lgf8absm30yh31lasdfbt40311ubn'

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/mtg_projects')
def mtg_projects():
    return render_template("mtg_projects.html")

@app.route('/other_projects')
def other_projects():
    return render_template("other_projects.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

if __name__ == '__main__':
    app.run()