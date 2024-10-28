import html
import pytest
from flask import url_for
from server import app
from unittest.mock import patch
from datetime import datetime

# Données de test pour les tests unitaires
clubs_data = [
    {
        "name": "Test Club",
        "email": "testclub@example.com",
        "points": 20 
    }
]

competitions_data = [
    {
        "name": "Test Competition",
        "date": "2025-12-31 10:00:00",
        "numberOfPlaces": 25 
    }
]

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@pytest.fixture
def clubs():
    # Retourne une copie profonde pour éviter les modifications inattendues
    return [club.copy() for club in clubs_data]

@pytest.fixture
def competitions():
    # Retourne une copie profonde pour éviter les modifications inattendues
    return [competition.copy() for competition in competitions_data]

@pytest.fixture(autouse=True)
def setup_app(clubs, competitions):
    # Mock des fonctions loadClubs et loadCompetitions pour retourner les copies mutables
    with patch('server.loadClubs', return_value=clubs), \
         patch('server.loadCompetitions', return_value=competitions):
        yield

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_valid_login(client):
    response = client.post('/showSummary', data={'email': 'testclub@example.com'})
    assert response.status_code == 200
    assert b'Test Club' in response.data

def test_invalid_login(client):
    response = client.post('/showSummary', data={'email': 'invalid@example.com'})
    assert response.status_code == 200
    response_text = response.data.decode('utf-8')
    unescaped_text = html.unescape(response_text)
    assert "Sorry, that email wasn't found." in unescaped_text

def test_book_future_competition(client):
    # Connexion préalable
    client.post('/showSummary', data={'email': 'testclub@example.com'})
    response = client.get('/book/Test%20Competition/Test%20Club')
    assert response.status_code == 200
    assert b'How many places?' in response.data

def test_book_past_competition(client, competitions):
    # Modifier la date de la compétition pour qu'elle soit passée
    competitions[0]['date'] = '2000-01-01 10:00:00'
    # Connexion préalable
    client.post('/showSummary', data={'email': 'testclub@example.com'})
    response = client.get('/book/Test%20Competition/Test%20Club')
    assert response.status_code == 200
    assert b'You cannot book places for a competition that has already happened.' in response.data

def test_purchase_places_valid(client, clubs, competitions):
    # Connexion préalable
    client.post('/showSummary', data={'email': 'testclub@example.com'})
    data = {
        'competition': 'Test Competition',
        'club': 'Test Club',
        'places': '5'
    }
    response = client.post('/purchasePlaces', data=data)
    assert response.status_code == 200
    assert b'Great-booking complete! 5 places purchased' in response.data

    # Vérification de la mise à jour des données
    club = next(c for c in clubs if c['name'] == 'Test Club')
    competition = next(c for c in competitions if c['name'] == 'Test Competition')
    assert club['points'] == 15  # 20 - 5 places achetées
    assert competition['numberOfPlaces'] == 20  # 25 - 5 places achetées

def test_purchase_places_negative(client):
    # Connexion préalable
    client.post('/showSummary', data={'email': 'testclub@example.com'})
    data = {
        'competition': 'Test Competition',
        'club': 'Test Club',
        'places': '-1'
    }
    response = client.post('/purchasePlaces', data=data)
    assert response.status_code == 200
    assert b'Invalid number of places.' in response.data

def test_purchase_places_zero(client):
    # Connexion préalable
    client.post('/showSummary', data={'email': 'testclub@example.com'})
    data = {
        'competition': 'Test Competition',
        'club': 'Test Club',
        'places': '0'
    }
    response = client.post('/purchasePlaces', data=data)
    assert response.status_code == 200
    assert b'Invalid number of places.' in response.data

def test_purchase_places_over_limit(client):
    # Connexion préalable
    client.post('/showSummary', data={'email': 'testclub@example.com'})
    data = {
        'competition': 'Test Competition',
        'club': 'Test Club',
        'places': '13'
    }
    response = client.post('/purchasePlaces', data=data)
    assert response.status_code == 200
    assert b'You cannot book more than 12 places in one competition.' in response.data

def test_purchase_places_not_enough_points(client, clubs, competitions):
    club = clubs[0]
    club['points'] = 5  # Le club n'a que 5 points
    # Connexion préalable
    client.post('/showSummary', data={'email': 'testclub@example.com'})
    data = {
        'competition': 'Test Competition',
        'club': 'Test Club',
        'places': '6'  # Demande d'achat de 6 places
    }
    response = client.post('/purchasePlaces', data=data)
    assert response.status_code == 200
    assert b'Not enough points.' in response.data

def test_purchase_places_not_enough_competition_places(client, clubs, competitions):
    competition = competitions[0]
    competition['numberOfPlaces'] = 5  # Seulement 5 places disponibles
    # Connexion préalable
    client.post('/showSummary', data={'email': 'testclub@example.com'})
    data = {
        'competition': 'Test Competition',
        'club': 'Test Club',
        'places': '6'  # Demande d'achat de 6 places
    }
    response = client.post('/purchasePlaces', data=data)
    assert response.status_code == 200
    assert b'Not enough places available.' in response.data

def test_logout(client):
    response = client.get('/logout')
    assert response.status_code == 302
    assert response.headers['Location'] == url_for('index')
