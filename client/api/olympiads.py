"""Простые запросы по образцу презентации о requests."""
import requests
from client.config import BASE_URL, TIMEOUT


def get_olympiads(year=None):
    return requests.get(f"{BASE_URL}/olympiads", params={"year": year} if year else {}, timeout=TIMEOUT)


def get_olympiad(olympiad_id):
    return requests.get(f"{BASE_URL}/olympiads/{olympiad_id}", timeout=TIMEOUT)


def get_protocol(olympiad_id):
    return requests.get(f"{BASE_URL}/olympiads/{olympiad_id}/protocol", timeout=TIMEOUT)


def get_attachments(olympiad_id):
    return requests.get(f"{BASE_URL}/olympiads/{olympiad_id}/attachments", timeout=TIMEOUT)


def create_olympiad(data, token):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.post(f"{BASE_URL}/olympiads", json=data, headers=headers, timeout=TIMEOUT)


def update_olympiad(olympiad_id, data, token):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.patch(f"{BASE_URL}/olympiads/{olympiad_id}", json=data, headers=headers, timeout=TIMEOUT)


def delete_olympiad(olympiad_id, token):
    return requests.delete(f"{BASE_URL}/olympiads/{olympiad_id}",
        headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)

