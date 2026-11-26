from app.errors import log_error
from getpass import getpass
import json
import requests
from client.api import accounts, olympiads
from client.config import BASE_URL


def show_response(response):
    try:
        print("Код ответа:", response.status_code)
        try:
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        except ValueError:
            print(response.text)
    except Exception as error:
        log_error(error, "show_response")
        raise


def main():
    try:
        print("Подключение к API:", BASE_URL)
        token = None
        while True:
            print(
                """
1 — олимпиады, 2 — карточка, 3 — протокол, 4 — документы"""
            )
            print(
                "5 — войти, 6 — профиль, 7 — мои результаты, 8 — записаться, 9 — обновить токен, 0 — выход"
            )
            try:
                choice = input("Команда: ").strip()
                if choice == "0":
                    break
                if choice == "1":
                    year = input("Год (Enter — все): ").strip()
                    show_response(olympiads.get_olympiads(int(year) if year else None))
                elif choice in ("2", "3", "4"):
                    olympiad_id = int(input("Номер олимпиады: "))
                    if choice == "2":
                        show_response(olympiads.get_olympiad(olympiad_id))
                    elif choice == "3":
                        show_response(olympiads.get_protocol(olympiad_id))
                    else:
                        show_response(olympiads.get_attachments(olympiad_id))
                elif choice == "5":
                    response = accounts.login(input("Логин: "), getpass("Пароль: "))
                    if response.ok:
                        token = response.json()["access_token"]
                        print("Вход выполнен")
                    else:
                        show_response(response)
                elif choice in ("6", "7", "8", "9"):
                    if not token:
                        print("Сначала выполните вход")
                    elif choice == "6":
                        show_response(accounts.get_profile(token))
                    elif choice == "7":
                        show_response(accounts.get_results(token))
                    elif choice == "9":
                        response = accounts.refresh_session(token)
                        if response.ok:
                            token = response.json()["access_token"]
                            print("Токен обновлён")
                        else:
                            show_response(response)
                    else:
                        show_response(accounts.enroll(int(input("Номер олимпиады: ")), token))
                else:
                    print("Неизвестная команда")
            except ValueError:
                print("Введите целое число")
            except requests.RequestException as error:
                print("Ошибка подключения:", error)
    except Exception as error:
        log_error(error, "main")
        raise


if __name__ == "__main__":
    main()
