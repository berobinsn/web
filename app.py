from flask import Flask, render_template, request, redirect, session
import requests
import json

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

@app.route('/talion', methods=["POST", "GET"])
def talion():
    if request.method == "POST":
        error = None
        try:
            quantity = int(request.form['quantity'])
        except:
            error = 'Invalid quantity'
            return render_template("talion.html", error=error)

        if quantity < 1:
            error = 'Invalid quantity'
            return render_template("talion.html", error=error)
        if quantity > 25000:
            error = 'Invalid quantity'
            return render_template("talion.html", error=error)
                
        edhrec_url = 'https://json.edhrec.com/pages/top/year.json'
        edhrec_response = requests.get(edhrec_url)
        edhrec_file = json.loads(edhrec_response.text)
        cardlist = edhrec_file['cardlist']
        top_cards = []

        i = 0
        while len(top_cards) < quantity:
            try:
                top_cards.append(f"{cardlist[i]['cards'][0]['name']} // {cardlist[i]['cards'][1]['name']}")
            except KeyError:
                top_cards.append(cardlist[i]['name'])     
            i += 1

        results = []
        with open('quickatomic.json', 'r') as f:
            file = json.load(f)
            values = []
            for card in top_cards:
                try:
                    mv = file[card]['manaValue']
                    values.append(int(mv))
                    if 'Creature' in file[card]['types'] or 'Vehicle' in file['data'][card]['types']:
                        try:
                            power = int(file[card]['power'])
                            if power != mv:
                                values.append(power)
                        except ValueError:
                            pass
                        try:
                            toughness = int(file[card]['toughness'])
                            if toughness != mv and toughness != power:
                                values.append(toughness)
                        except ValueError:
                            pass
                except KeyError:
                    pass
            for number in range(max(values) + 1):
                results.append({'number': number, 'count': values.count(number), 'percentage': f"{values.count(number)/len(values)*100: .2f}"})

        return render_template("talion_results.html", quantity=f"{quantity:,}", results=results)
    else:
        return render_template("talion.html")

@app.route('/talion_results')
def talion_results():
    return render_template("talion_results.html")

if __name__ == '__main__':
    app.run()