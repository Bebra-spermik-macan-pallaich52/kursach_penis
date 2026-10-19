import requests
from client.config import BASE_URL, TIMEOUT


def login(username, password):
    return requests.post(f"{BASE_URL}/auth/token", data={"username": username, "password": password}, timeout=TIMEOUT)


def get_profile(token):
    return requests.get(f"{BASE_URL}/users/me", headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)


def get_results(token):
    return requests.get(f"{BASE_URL}/users/me/participations", headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)


def enroll(olympiad_id, token):
    return requests.post(f"{BASE_URL}/olympiads/{olympiad_id}/participations", headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)

