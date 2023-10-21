from unidecode import unidecode
import re
import requests
import json
import mtg_parser

'''url = f"https://json.edhrec.com/pages/average-decks/anafenza-kin-tree-spirit.json"
response = requests.get(url)
if response.status_code != 200:
    error = "Your commander was not found on edhREC's average decklist page."
file = json.loads(response.text)
deck = file["deck"]
for card in deck:
    print(card)'''



'''def main():
    url = "https://archidekt.com/decks/649546/anafenza_kintree_spirit_edh_11_counters"
    commander, your_deck, error = get_your_deck(url)
    print("List Fetched")
    if error != None:
        print(error)
    average_deck, error = get_average_deck(commander)
    print("Average Deck Info Fetched")
    if error != None:
        print(error)
    edhrec_list, error = get_edhrec_list(commander)
    print("edhREC Info Fetched")
    (
        unique_average_count,
        unique_average_list,
        overlap_average_count,
        overlap_average_list,
    ) = get_card_counts(your_deck, average_deck)
    print("Average Deck Comparisons Made")
    (
        unique_edhrec_count,
        unique_edhrec_list,
        overlap_edhrec_count,
        overlap_edhrec_list,
    ) = get_card_counts(your_deck, edhrec_list)
    print("edhREC Comparisons Made")
    print("Unique edhREC Count: ", unique_edhrec_count)
    print()
    print("Unique Average Count: ", unique_average_count)
    print()
    print("Overlap edhREC Count: ", overlap_edhrec_count)
    print()
    print("Unique edhREC Count: ", overlap_average_count)
    print()


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
                cardname = re.sub(r" // .*", "", cardname)
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

    print()
    for card in average_decklist:
        print(card)

    return average_decklist, error


def get_edhrec_list(commander):
    error = None
    dashed_commander, reverse_dashed_commander, error = convert_to_dashes(commander)
    try:
        url = f"https://json.edhrec.com/pages/commanders/{dashed_commander}.json"
        response = requests.get(url)
        if response.status_code != 200:
            error = "Your commander was not found on the commander page for edhREC"
        print(response.text)
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

if __name__ == "__main__":
    main()'''

url = 'https://archidekt.com/decks/649546/anafenza_kintree_spirit_edh_11_counters'
cards = mtg_parser.parse_deck(url)
for card in cards:
    print(str(card))
