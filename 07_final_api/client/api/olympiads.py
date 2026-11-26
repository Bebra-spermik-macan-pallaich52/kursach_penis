from app.errors import log_error
import requests
from client.config import BASE_URL, TIMEOUT


def get_olympiads(year=None):
    try:
        return requests.get(
            f"{BASE_URL}/olympiads", params={"year": year} if year else {}, timeout=TIMEOUT
        )
    except Exception as error:
        log_error(error, "get_olympiads")
        raise


def get_olympiad(olympiad_id):
    try:
        return requests.get(f"{BASE_URL}/olympiads/{olympiad_id}", timeout=TIMEOUT)
    except Exception as error:
        log_error(error, "get_olympiad")
        raise


def get_protocol(olympiad_id):
    try:
        return requests.get(f"{BASE_URL}/olympiads/{olympiad_id}/protocol", timeout=TIMEOUT)
    except Exception as error:
        log_error(error, "get_protocol")
        raise


def get_attachments(olympiad_id):
    try:
        return requests.get(f"{BASE_URL}/olympiads/{olympiad_id}/attachments", timeout=TIMEOUT)
    except Exception as error:
        log_error(error, "get_attachments")
        raise


def create_olympiad(data, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        return requests.post(f"{BASE_URL}/olympiads", json=data, headers=headers, timeout=TIMEOUT)
    except Exception as error:
        log_error(error, "create_olympiad")
        raise


def update_olympiad(olympiad_id, data, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        return requests.patch(
            f"{BASE_URL}/olympiads/{olympiad_id}", json=data, headers=headers, timeout=TIMEOUT
        )
    except Exception as error:
        log_error(error, "update_olympiad")
        raise


def delete_olympiad(olympiad_id, token):
    try:
        return requests.delete(
            f"{BASE_URL}/olympiads/{olympiad_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )
    except Exception as error:
        log_error(error, "delete_olympiad")
        raise
