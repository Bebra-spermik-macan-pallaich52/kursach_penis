from app.errors import log_error
import requests
from client.config import BASE_URL, TIMEOUT


def login(username, password):
    try:
        return requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": username, "password": password},
            timeout=TIMEOUT,
        )
    except Exception as error:
        log_error(error, "login")
        raise


def get_profile(token):
    try:
        return requests.get(
            f"{BASE_URL}/users/me", headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT
        )
    except Exception as error:
        log_error(error, "get_profile")
        raise


def get_results(token):
    try:
        return requests.get(
            f"{BASE_URL}/users/me/participations",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )
    except Exception as error:
        log_error(error, "get_results")
        raise


def enroll(olympiad_id, token):
    try:
        return requests.post(
            f"{BASE_URL}/olympiads/{olympiad_id}/participations",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )
    except Exception as error:
        log_error(error, "enroll")
        raise


def refresh_session(token):
    try:
        return requests.post(
            f"{BASE_URL}/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )
    except Exception as error:
        log_error(error, "refresh_session")
        raise
