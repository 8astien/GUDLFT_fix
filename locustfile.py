from locust import HttpUser, TaskSet, task, between
from urllib.parse import quote


class WebsiteTasks(TaskSet):

    def on_start(self):
        # L'utilisateur se connecte au début de la session
        self.email = "john@simplylift.co"
        self.club_name = "Simply Lift"
        response = self.client.post("/showSummary", data={"email": self.email})
        if response.status_code != 200:
            print(f"Failed to log in with {self.email}")


    @task(2)
    def book_and_purchase(self):
        # L'utilisateur visite la page de réservation puis achète des places
        competition_name = "Fall Classic"
        competition_url = quote(competition_name)
        club_url = quote(self.club_name)
        with self.client.get(f"/book/{competition_url}/{club_url}", catch_response=True) as response:
            if response.status_code == 200:
                with self.client.post("/purchasePlaces", data={
                    "competition": competition_name,
                    "club": self.club_name,
                    "places": "1"
                }, catch_response=True) as purchase_response:
                    if purchase_response.status_code == 200:
                        purchase_response.success()
                    else:
                        purchase_response.failure(
                            f"Purchase failed with status {purchase_response.status_code}")
            else:
                response.failure(
                    f"Booking page failed with status {response.status_code}")

    @task(1)
    def logout(self):
        self.client.get("/logout")


class WebsiteUser(HttpUser):
    host = "http://localhost:5000"
    tasks = [WebsiteTasks]
    wait_time = between(1, 5)
