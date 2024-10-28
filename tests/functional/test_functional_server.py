# tests/functional/test_functional_server.py

import pytest
from server import app, loadClubs, loadCompetitions
from flask import url_for
import datetime

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_functional_user_login_and_book_place(client):
    """
    Scénario :
    1. L'utilisateur se connecte.
    2. L'utilisateur réserve une place dans une compétition future.
    3. Vérifie si le nombre de points est déduit et le nombre de places est mis à jour dans la réponse.
    """
    clubs = loadClubs()
    competitions = loadCompetitions()
    club = clubs[0]
    # Trouver une compétition future
    competition = None
    for comp in competitions:
        competition_date = datetime.datetime.strptime(comp['date'], "%Y-%m-%d %H:%M:%S")
        if competition_date > datetime.datetime.now():
            competition = comp
            break
    assert competition is not None, "Aucune compétition future trouvée pour le test"

    original_club_points = int(club['points'])
    original_competition_places = int(competition['numberOfPlaces'])

    # Connexion
    login_response = client.post('/showSummary', data={'email': club['email']})
    assert login_response.status_code == 200
    assert bytes(club['name'], 'utf-8') in login_response.data

    # Réservation
    places_to_book = 3
    data = {
        'competition': competition['name'],
        'club': club['name'],
        'places': str(places_to_book)
    }
    booking_response = client.post('/purchasePlaces', data=data)
    assert booking_response.status_code == 200
    assert bytes(f'Great-booking complete! {places_to_book} places purchased', 'utf-8') in booking_response.data

    # Vérification que les points et les places ont été mis à jour dans la réponse
    updated_club_points = original_club_points - places_to_book
    updated_competition_places = original_competition_places - places_to_book

    # Vérification des points du club dans la réponse
    assert bytes(f'Points available: {updated_club_points}', 'utf-8') in booking_response.data

    # Vérification du nombre de places de la compétition dans la réponse
    assert bytes(f"Number of Places: {updated_competition_places}", 'utf-8') in booking_response.data

def test_functional_invalid_booking(client):
    """
    Scénario :
    1. L'utilisateur se connecte.
    2. L'utilisateur tente de réserver plus de places que le maximum autorisé.
    3. Vérifie qu'un message d'erreur s'affiche et que les points ne sont pas déduits.
    """
    clubs = loadClubs()
    competitions = loadCompetitions()
    club = clubs[0]
    # Trouver une compétition future
    competition = None
    for comp in competitions:
        competition_date = datetime.datetime.strptime(comp['date'], "%Y-%m-%d %H:%M:%S")
        if competition_date > datetime.datetime.now():
            competition = comp
            break
    assert competition is not None, "Aucune compétition future trouvée pour le test"

    original_club_points = int(club['points'])
    original_competition_places = int(competition['numberOfPlaces'])

    # Connexion
    login_response = client.post('/showSummary', data={'email': club['email']})
    assert login_response.status_code == 200

    # Tentative de réservation trop élevée
    data = {
        'competition': competition['name'],
        'club': club['name'],
        'places': '13'  # Plus que le maximum autorisé de 12
    }
    booking_response = client.post('/purchasePlaces', data=data)
    assert booking_response.status_code == 200  # L'application retourne 200 avec un message d'erreur
    assert b'You cannot book more than 12 places in one competition.' in booking_response.data

    # Vérification que les points et les places n'ont pas été modifiés dans la réponse
    assert bytes(f'Points available: {original_club_points}', 'utf-8') in booking_response.data
    assert bytes(f"Number of Places: {original_competition_places}", 'utf-8') in booking_response.data

def test_functional_logout_and_redirect(client):
    """
    Scénario :
    1. L'utilisateur se connecte.
    2. L'utilisateur se déconnecte.
    3. Vérifie que l'utilisateur est redirigé vers la page d'accueil après la déconnexion.
    """
    clubs = loadClubs()
    club = clubs[0]

    # Connexion
    login_response = client.post('/showSummary', data={'email': club['email']})
    assert login_response.status_code == 200

    # Déconnexion
    logout_response = client.get('/logout')
    assert logout_response.status_code == 302
    assert logout_response.headers['Location'] == url_for('index')
