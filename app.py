from flask import Flask, render_template, request, redirect, session
import requests
import json
import mtg_parser
import re
from unidecode import unidecode
from mtgsdk import Card

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


@app.route('/uniqueness', methods=["POST", "GET"])
def uniqueness():
    if request.method == "POST":
        session.clear()
        url = request.form['url'].strip()
        commander, your_deck, error = get_your_deck(url)
        if error != None:
            return render_template("uniqueness.html", error=error)
        average_deck, error = get_average_deck(commander)
        if error != None:
            return render_template("uniqueness.html", error=error)
        edhrec_list, error = get_edhrec_list(commander)
        (
            unique_average_count,
            unique_average_list,
            overlap_average_count,
            overlap_average_list,
        ) = get_card_counts(your_deck, average_deck)
        (
            unique_edhrec_count,
            unique_edhrec_list,
            overlap_edhrec_count,
            overlap_edhrec_list,
        ) = get_card_counts(your_deck, edhrec_list)
        session['unique_average_list'] = unique_average_list
        session['unique_edhrec_list'] = unique_edhrec_list
        session['overlap_average_list'] = overlap_average_list
        session['overlap_edhrec_list'] = overlap_edhrec_list
        return render_template("uniqueness_results.html", 
                               unique_average_count=unique_average_count,
                               overlap_average_count=overlap_average_count,
                               unique_edhrec_count=unique_edhrec_count,
                               overlap_edhrec_count=overlap_edhrec_count
                               )

    else:
        return render_template("uniqueness.html")


@app.route('/uniqueness_results')
def uniqueness_results():
    render_template("uniqueness_results.html")


@app.route("/view_lists")
def view_lists():
    unique_average_list = session.get('unique_average_list', [])
    unique_edhrec_list = session.get('unique_edhrec_list', [])
    overlap_average_list = session.get('overlap_average_list', [])
    overlap_edhrec_list = session.get('overlap_edhrec_list', [])
    return render_template("view_lists.html",
                           unique_average_list=unique_average_list,
                           unique_edhrec_list=unique_edhrec_list,
                           overlap_average_list=overlap_average_list,
                           overlap_edhrec_list=overlap_edhrec_list)


@app.route('/comparisons', methods=["POST", "GET"])
def comparisons():
    if request.method == "POST":
        session.clear()
        form_submission = request.form['urls']
        urls = form_submission.split("\r\n")
        masterlist, suggestions, error = comparison_test(urls)
        if error != None:
            return render_template("comparisons.html", error=error)
        
        for decklist in masterlist:
            decklist['budget'] = f"{decklist['budget']:.2f}"
            decklist['saltscore'] = f"{decklist['saltscore']:.2f}"
            decklist['saltiestvalue'] = f"{decklist['saltiestvalue']:.2f}"
            decklist['mv'] = f"{decklist['mv']:.2f}"
        
        budgets = []
        for decklist in masterlist:
            budgetlist = []
            for deck_card in sorted(decklist['decklist'], key=lambda d: d['price'], reverse=True):
                if deck_card['price'] >= 4.99:
                    budgetlist.append(f"{deck_card['quantity']} {deck_card['cardname']} ${deck_card['price']:.2f}")
            budgets.append({'name': decklist['deckname'], 'budget': decklist['budget'], 'cardlist': budgetlist})
        
        salt = []
        for decklist in masterlist:
            saltlist = []
            for deck_card in sorted(decklist['decklist'], key=lambda d: d['salt'], reverse=True):
                if deck_card['salt'] >= .75:
                    saltlist.append(f"{deck_card['quantity']} {deck_card['cardname']} Salt Score: {deck_card['salt']:.2f}")
            salt.append({'name': decklist['deckname'], 'saltscore': decklist['saltscore'], 'saltlist': saltlist})

        cedh = []
        for decklist in masterlist:
            cedhlist = []
            for deck_card in decklist['decklist']:
                if deck_card['cedh'] == True:
                    cedhlist.append(deck_card['cardname'])
            cedh.append({'name': decklist['deckname'], 'cedhcount': decklist['cedhcount'], 'cedhlist': cedhlist})

        session['budgets'] = budgets
        session['salt'] = salt
        session['cedh'] = cedh

        return render_template("comparison_results.html", masterlist=masterlist, suggestions=suggestions)
    else:
        return render_template("comparisons.html")
    

@app.route('/comparison_results')
def comparison_results():
    render_template("comparison_results.html")


@app.route("/view_budget")
def view_budget():
    budgets = session.get('budgets', [])
    return render_template("view_budget.html", budgets=budgets)


@app.route("/view_salt")
def view_salt():
    salt = session.get('salt', [])
    return render_template("view_salt.html", salt=salt)


@app.route("/view_cedh")
def view_cedh():
    cedh = session.get('cedh', [])
    return render_template("view_cedh.html", cedh=cedh)


def get_your_deck(url):
    error = None
    try:
        cards = mtg_parser.parse_deck(url)
    except KeyError:
        error = "Could not find your decklist"
        return None, None, error
    
    commander_list = []
    decklist = []

    try:
        for card in cards:
            commander_match = re.search(r".* \[commander\]$", str(card))
            if commander_match:
                name = re.sub(r" \[commander\]$", "", unidecode(str(card)))
                name = re.sub(r" \d+$", "", name)
                name = re.sub(r" \(\w\w\w\w?\w?\)$", "", name)
                name = re.sub(r"^\d+x* ", "", name)
                commander_list.append(name)
            maybeboard = re.search(r".*\[.*maybeboard.*\]$", str(card))
            sideboard = re.search(r".*\[.*sideboard.*\]$", str(card))
            if maybeboard == None and sideboard == None:
                cardname = re.sub(r"^\d+x* ", "", unidecode(str(card)))
                cardname = re.sub(r" \[.*\]$", "", cardname)
                cardname = re.sub(r" \(\w\w\w\w?\w?\).*$", "", cardname)
                decklist.append(cardname)
    except (KeyError, TypeError):
        error = "Could not find your decklist"
        return None, None, error

    if len(commander_list) == 0:
        error = "Your decklist does not have a commander selected"
        return None, None, error

    return commander_list, decklist, error


def get_average_deck(commander):
    error = None
    dashed_commander, reverse_dashed_commander, error = convert_to_dashes(commander)
    try:
        url = f"https://json.edhrec.com/pages/average-decks/{dashed_commander}.json"
        response = requests.get(url)
        if response.status_code != 200:
            error = "Your commander was not found on edhREC's average decklist page."
        file = json.loads(response.text)
        deck = file["deck"]
    except KeyError:
        url = f"https://json.edhrec.com/pages/average-decks/{reverse_dashed_commander}.json"
        response = requests.get(url)
        if response.status_code != 200:
            error = "Your commander was not found on edhREC's average decklist page."
        file = json.loads(response.text)
        deck = file["deck"]
    average_decklist = []
    for card in deck:
        card = re.sub(r"^\d+ ", "", card)
        average_decklist.append(card)
    return average_decklist, error


def get_edhrec_list(commander):
    error = None
    dashed_commander, reverse_dashed_commander, error = convert_to_dashes(commander)
    try:
        url = f"https://json.edhrec.com/pages/commanders/{dashed_commander}.json"
        response = requests.get(url)
        if response.status_code != 200:
            error = "Your commander was not found on the commander page for edhREC"
        file = json.loads(response.text)
        decklist = file["container"]["json_dict"]["cardlists"]
    except KeyError:
        url = (
            f"https://json.edhrec.com/pages/commanders/{reverse_dashed_commander}.json"
        )
        response = requests.get(url)
        if response.status_code != 200:
            error = "Your commander was not found on the commander page for edhREC"
        file = json.loads(response.text)
        decklist = file["container"]["json_dict"]["cardlists"]
    edhrec_cards = []
    for cardview in decklist:
        for card in cardview["cardviews"]:
            edhrec_cards.append(card["name"])
    return edhrec_cards, error


def convert_to_dashes(commander):
    dashed_commander = []
    for card in sorted(commander):
        card = re.sub(r" // .*$", "", unidecode(card.lower()))
        card = re.sub(r"-", " ", card)
        card = re.sub(r" ", "_", card)
        card = re.sub(r"\W", "", card)
        card = re.sub(r"_", "-", card)
        dashed_commander.append(card)
    if len(dashed_commander) == 0:
        error = "The decklist does not have a commander selected"
        return None, None, error
    elif len(dashed_commander) == 1:
        return dashed_commander[0], None, None
    else:
        return (
            f"{dashed_commander[0]}-{dashed_commander[1]}",
            f"{dashed_commander[1]}-{dashed_commander[0]}",
            None
        )
    

def get_card_counts(yours, edhrec):
    unique_count = 0
    overlap_count = 0
    unique_list = []
    overlap_list = []
    for card in yours:
        if card in edhrec:
            overlap_count += 1
            overlap_list.append(card)
        else:
            unique_count += 1
            unique_list.append(card)

    return unique_count, unique_list, overlap_count, overlap_list


def comparison_test(deck_urls):
    masterlist, error = get_list(deck_urls)
    if len(deck_urls) == 0:
        error = "No URL submitted"
    if error != None:
        return None, None, error
    masterlist = deck_analysis(masterlist)
    masterlist = cedhtest(masterlist)
    suggestions = []
    imbalanced = False

    if len(masterlist) > 1:
        sorted_decks = sorted(masterlist, key=lambda d: d['budget'])
        if sorted_decks[-1]['budget'] - sorted_decks[0]['budget'] >= 250:
            imbalanced = True
            nosuggestion = True
            if sorted_decks[-1]['budget'] - sorted_decks[-2]['budget'] >= 125:
                nosuggestion = False
                suggestions.append(f"{sorted_decks[-1]['deckname']} could consider switching to a more budget deck")
            if sorted_decks[1]['budget'] - sorted_decks[0]['budget'] >= 125:
                nosuggestion = False
                suggestions.append(f"{sorted_decks[0]['deckname']} could consider switching to a more expensive deck")
            if nosuggestion == True:
                suggestions.append("Players could consider switching to decks with more similar budgets")
        
        sorted_decks = sorted(masterlist, key=lambda d: d['saltscore'])
        if sorted_decks[-1]['saltscore'] - sorted_decks[0]['saltscore'] >= 20:
            imbalanced = True
            nosuggestion = True
            if sorted_decks[-1]['saltscore'] - sorted_decks[-2]['saltscore'] >= 10:
                nosuggestion = False
                suggestions.append(f"{sorted_decks[-1]['deckname']} could consider switching to a deck with less stax, control, or combo potential")
            if sorted_decks[1]['saltscore'] - sorted_decks[0]['saltscore'] >= 10:
                nosuggestion = False
                suggestions.append(f"{sorted_decks[0]['deckname']} could consider switching to a deck with more stax, control, or combo potential")
            if nosuggestion == True:
                suggestions.append("Players could consider switching to decks that are have similar levels of stax, control, or combo potential")
                            
        sorted_decks = sorted(masterlist, key=lambda d: d['mv'])                
        if sorted_decks[-1]['mv'] - sorted_decks[0]['mv'] >= 1:
            imbalanced = True
            nosuggestion = True
            if sorted_decks[-1]['mv'] - sorted_decks[-2]['mv'] >= .5:
                nosuggestion = False
                suggestions.append(f"{sorted_decks[-1]['deckname']} could consider switching to a deck that is lower to the ground")
            if sorted_decks[1]['mv'] - sorted_decks[0]['mv'] >= .5:
                nosuggestion = False
                suggestions.append(f"{sorted_decks[0]['deckname']} could consider switching to a slower deck")
            if nosuggestion == True:
                suggestions.append("Players could consider switching to decks with more similar speeds")

        sorted_decks = sorted(masterlist, key=lambda d: d['cedhcount'])
        if sorted_decks[-1]['cedhcount'] - sorted_decks[0]['cedhcount'] >= 20:
            imbalanced = True
            nosuggestion = True
            if sorted_decks[-1]['cedhcount'] - sorted_decks[-2]['cedhcount'] >= 10:
                nosuggestion = False
                suggestions.append(f"{sorted_decks[-1]['deckname']} could consider switching to a more casual deck")
            if sorted_decks[1]['cedhcount'] - sorted_decks[0]['cedhcount'] >= 10:
                nosuggestion = False
                suggestions.append(f"{sorted_decks[0]['deckname']} could consider switching to a more competitive deck")
            if nosuggestion == True:
                suggestions.append("Players could consider switching to decks with more similar levels of competitive cards")
                                
        if imbalanced == False:
            suggestions.append("All decks seem balanced based on their budgets, salt scores, mana values, and number of competitive level cards")
    else:
        suggestions.append("Enter multiple decklists to see if they are balanced, or if the program detects any imbalances")
    return masterlist, suggestions, error


def get_list(deck_urls):
    error = None
    with open('quickpricing.json', 'r') as f:
        file = json.load(f)
        masterlist = []
        for url in deck_urls:
            url = url.strip()

        while '' in deck_urls:
            deck_urls.remove('')

        for url in deck_urls:
            decklist_cards = mtg_parser.parse_deck(url.strip())
            decklist = []
            commander_list = []
            try:
                for decklist_card in decklist_cards:
                    commander_match = re.search(r".* \[commander\]$", str(decklist_card))
                    if commander_match:
                        name = re.sub(r" \[commander\]$", "", str(decklist_card))
                        name = re.sub(r" \d+$", "", name)
                        name = re.sub(r" \(\w\w\w\w?\w?\)$", "", name)
                        name = re.sub(r"^\d+x* ", "", name)
                        commander_list.append(name)
                    maybeboard = re.search(r".*\[.*maybeboard.*\]$", str(decklist_card))
                    sideboard = re.search(r".*\[.*sideboard.*\]$", str(decklist_card))
                    if maybeboard == None and sideboard == None:
                        quantity = re.search(r"^(\d+)", str(decklist_card))
                        cardname = re.sub(r"^\d+x* ", "", str(decklist_card))
                        cardname = re.sub(r" \[.*\]$", "", cardname)
                        cardname = re.sub(r" \(\w\w\w\w?\w?\).*$", "", cardname)
                        decklist.append({'cardname': str(cardname), 'quantity': int(quantity.group())})
            except TypeError:
                error = "Could not find your decklist."
                return None, error

            if len(commander_list) == 0:
                error = "A decklist is missing a commander"
                return None, error
                
            elif len(commander_list) == 1:
                commander_name = commander_list[0]
            else:
                commander_name = f"{commander_list[0]} / {commander_list[1]}"

            budget = 0
            for card in decklist:
                uuids = []
                if card['cardname'] in ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest']:
                    uuids.append('None')
                else:
                    card_uuids = Card.where(name=card['cardname']).all()
                    for card_uuid in card_uuids:
                        if card_uuid.name == card['cardname']:
                            uuids.append(card_uuid.id)
                    if len(uuids) == 0:
                        for card_uuid in card_uuids:
                            uuids.append(card_uuid.id)
                prices = []
                if 'None' in uuids:
                    prices.append(0)
                else:
                    for id in uuids:
                        try:
                            price = file[id]['normal']
                            prices.append(price)
                        except KeyError:
                            pass
                        try:
                            price = file[id]['foil']
                            prices.append(price)
                        except  KeyError:
                            pass
                try:
                    card.update({'price': min(prices)})
                    budget += min(prices)
                except ValueError:
                    card.update({'price': 0})
            masterlist.append({'deckname': commander_name, 'commanderlist': commander_list, 'url': url, 'decklist': decklist, 'budget': budget})
        return masterlist, error


def deck_analysis(masterlist):
    with open('quickatomic.json', 'r') as f:
        file = json.load(f)
        for decklist in masterlist:
            deck_mv = 0
            cardcount = 0
            landcount = 0
            total_salt = 0
            saltiest_cardname = 'none'
            saltiest_card_value = 0
            for card in decklist['decklist']:
                cardname = card['cardname']
                quantity = card['quantity']
                try:
                    deck_mv += file[cardname]['manaValue']
                    cardcount += int(quantity)
                    if 'Land' in file[cardname]['types']:
                        landcount += int(quantity)
                except KeyError:
                    pass
                try:
                    salt = file[cardname]['edhrecSaltiness']
                except KeyError:
                    salt = 0
                card.update({'salt': salt})
                if salt > saltiest_card_value:
                    saltiest_card_value = salt
                    saltiest_cardname = cardname
                total_salt += (salt * int(quantity))
            decklist.update({'mv': float(deck_mv / (cardcount - landcount)), 'saltscore': total_salt, 'saltiestcard': saltiest_cardname, 'saltiestvalue': saltiest_card_value})
    return masterlist


def cedhtest(masterlist):
    cedh_url = 'https://www.moxfield.com/decks/0DDiZV77lkSqfVAm8eCllg'
    cedh_cards = mtg_parser.parse_deck(cedh_url)
    cedh_staples = []
    for cedh_card in cedh_cards:
        cedh_cardname = re.sub(r"^1 ", "", str(cedh_card))
        cedh_staples.append(cedh_cardname)
    
    for decklist in masterlist:
        overlap = 0
        for card in decklist['decklist']:
            quantity = card['quantity']
            cardname = card['cardname']
            if cardname in cedh_staples:
                card.update({'cedh': True})
                overlap += int(quantity)
            else:
                card.update({'cedh': False})
        decklist.update({'cedhcount': overlap})
    return masterlist


if __name__ == '__main__':
    app.run()