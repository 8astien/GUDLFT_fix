import datetime
import json
from flask import Flask,render_template,request,redirect,flash,url_for, abort


def loadClubs():
    with open('clubs.json') as c:
         listOfClubs = json.load(c)['clubs']
         return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
         listOfCompetitions = json.load(comps)['competitions']
         return listOfCompetitions


app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/showSummary', methods=['POST'])
def showSummary():
    try:
        club = [club for club in clubs if club['email'] == request.form['email']][0]
        return render_template('welcome.html', club=club, competitions=competitions)
    except IndexError:
        abort(401, description="Email not found, please ensure your email is valid.")


@app.route('/book/<competition>/<club>')
def book(competition, club):
    foundClub = [c for c in clubs if c['name'] == club][0]
    foundCompetition = [c for c in competitions if c['name'] == competition][0]

    # Vérification si la compétition est passée
    competition_date = datetime.datetime.strptime(foundCompetition['date'], "%Y-%m-%d %H:%M:%S")
    if competition_date < datetime.datetime.now():
        flash("You cannot book places for a competition that has already happened.")
        return render_template('welcome.html', club=foundClub, competitions=competitions)

    # Si la compétition est valide, on peut afficher la page de réservation
    return render_template('booking.html', club=foundClub, competition=foundCompetition)

@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    competition = [c for c in competitions if c['name'] == request.form['competition']][0]
    club = [c for c in clubs if c['name'] == request.form['club']][0]
    placesRequired = int(request.form['places'])

    # Limite de 12 places par réservation
    if placesRequired > 12:
        abort(401, description="You cannot book more than 12 places at a time.")

    # Vérification des points disponibles et des places restantes pour la compétition
    if placesRequired > int(club['points']):
        abort(401, description="Not enough points. Please verify your available points.")
    if placesRequired > int(competition['numberOfPlaces']):
        abort(401, description="Not enough places available in the competition.")

    # Mise à jour des places et des points
    competition['numberOfPlaces'] = int(competition['numberOfPlaces']) - placesRequired
    club['points'] = int(club['points']) - placesRequired
    
    flash(f'Booking complete, {placesRequired} places bought')
    return render_template('welcome.html', club=club, competitions=competitions)

# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))