import datetime
import json
from flask import Flask, render_template, request, redirect, flash, url_for, abort

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/showSummary', methods=['POST'])
def showSummary():
    clubs = loadClubs()
    competitions = loadCompetitions()
    try:
        club = [club for club in clubs if club['email'] == request.form['email']][0]
        return render_template('welcome.html', club=club, competitions=competitions, clubs=clubs)
    except IndexError:
        flash("Sorry, that email wasn't found.")
        return render_template('index.html')

@app.route('/book/<competition>/<club>')
def book(competition, club):
    clubs = loadClubs()
    competitions = loadCompetitions()
    try:
        foundClub = [c for c in clubs if c['name'] == club][0]
        foundCompetition = [c for c in competitions if c['name'] == competition][0]
    except IndexError:
        flash("Something went wrong-please try again")
        return render_template('welcome.html', club=foundClub, competitions=competitions, clubs=clubs)

    competition_date = datetime.datetime.strptime(foundCompetition['date'], "%Y-%m-%d %H:%M:%S")
    if competition_date < datetime.datetime.now():
        flash("You cannot book places for a competition that has already happened.")
        return render_template('welcome.html', club=foundClub, competitions=competitions, clubs=clubs)

    return render_template('booking.html', club=foundClub, competition=foundCompetition)

@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    clubs = loadClubs()
    competitions = loadCompetitions()
    try:
        competition = [c for c in competitions if c['name'] == request.form['competition']][0]
        club = [c for c in clubs if c['name'] == request.form['club']][0]
    except IndexError:
        flash("Something went wrong-please try again")
        return render_template('welcome.html', club=club, competitions=competitions, clubs=clubs)
    placesRequired = int(request.form['places'])

    # Vérification des places et des points
    if placesRequired <= 0:
        flash("Invalid number of places.")
        return render_template('welcome.html', club=club, competitions=competitions, clubs=clubs)
    if placesRequired > 12:
        flash("You cannot book more than 12 places in one competition.")
        return render_template('welcome.html', club=club, competitions=competitions, clubs=clubs)
    if placesRequired > int(competition['numberOfPlaces']):
        flash("Not enough places available.")
        return render_template('welcome.html', club=club, competitions=competitions, clubs=clubs)
    if placesRequired > int(club['points']):
        flash("Not enough points.")
        return render_template('welcome.html', club=club, competitions=competitions, clubs=clubs)

    # Mise à jour des places et des points (en mémoire uniquement)
    competition['numberOfPlaces'] = int(competition['numberOfPlaces']) - placesRequired
    club['points'] = int(club['points']) - placesRequired

    flash(f'Great-booking complete! {placesRequired} places purchased')
    return render_template('welcome.html', club=club, competitions=competitions, clubs=clubs)

@app.route('/logout')
def logout():
    return redirect(url_for('index'))
