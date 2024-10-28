# tests/integration/test_integration_server.py

import pytest
import html
from server import app, loadClubs, loadCompetitions
import datetime

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_integration_valid_login(client):
    # Utilise les données réelles du fichier clubs.json
    clubs = loadClubs()
    valid_email = clubs[0]['email']
    response = client.post('/showSummary', data={'email': valid_email})
    assert response.status_code == 200
    assert bytes(clubs[0]['name'], 'utf-8') in response.data

def test_integration_invalid_login(client):
    response = client.post('/showSummary', data={'email': 'invalid@example.com'})
    assert response.status_code == 200
    response_text = response.data.decode('utf-8')
    unescaped_text = html.unescape(response_text)
    assert "Sorry, that email wasn't found." in unescaped_text
    
def test_integration_purchase_places(client):
    # Utilise les données réelles des fichiers JSON
    clubs = loadClubs()
    competitions = loadCompetitions()
    club = clubs[0]
    competition = competitions[0]

    # Connexion préalable
    client.post('/showSummary', data={'email': club['email']})

    data = {
        'competition': competition['name'],
        'club': club['name'],
        'places': '1'
    }
    response = client.post('/purchasePlaces', data=data)
    assert response.status_code == 200
    assert b'Great-booking complete! 1 places purchased' in response.data

def test_integration_book_competition(client):
    # Test de la réservation d'une compétition future
    competitions = loadCompetitions()
    # Trouver une compétition future
    future_competition = None
    for comp in competitions:
        competition_date = datetime.datetime.strptime(comp['date'], "%Y-%m-%d %H:%M:%S")
        if competition_date > datetime.datetime.now():
            future_competition = comp
            break

    assert future_competition is not None, "No future competition found for testing"

    clubs = loadClubs()
    club = clubs[0]

    # Connexion préalable
    client.post('/showSummary', data={'email': club['email']})

    competition_name_encoded = future_competition['name'].replace(' ', '%20')
    club_name_encoded = club['name'].replace(' ', '%20')

    response = client.get(f"/book/{competition_name_encoded}/{club_name_encoded}")
    assert response.status_code == 200
    assert b'How many places?' in response.data

def test_integration_book_past_competition(client):
    # Test de la réservation d'une compétition passée
    competitions = loadCompetitions()
    # Trouver une compétition passée
    past_competition = None
    for comp in competitions:
        competition_date = datetime.datetime.strptime(comp['date'], "%Y-%m-%d %H:%M:%S")
        if competition_date < datetime.datetime.now():
            past_competition = comp
            break

    assert past_competition is not None, "No past competition found for testing"

    clubs = loadClubs()
    club = clubs[0]

    # Connexion préalable
    client.post('/showSummary', data={'email': club['email']})

    competition_name_encoded = past_competition['name'].replace(' ', '%20')
    club_name_encoded = club['name'].replace(' ', '%20')

    response = client.get(f"/book/{competition_name_encoded}/{club_name_encoded}")
    assert response.status_code == 200
    assert b'You cannot book places for a competition that has already happened.' in response.data
