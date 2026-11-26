from app.errors import log_error
import re
from datetime import date
from fastapi import HTTPException
from app.names import read_full_name
from typing import Annotated
from fastapi import Path

Id = Annotated[int, Path(gt=0)]


def check_text(data):
    try:
        for value in data.values():
            if isinstance(value, str) and any(
                (
                    ord(char) < 32 or 55296 <= ord(char) <= 57343 or ord(char) in (65534, 65535)
                    for char in value
                )
            ):
                raise HTTPException(422, "Текст содержит недопустимые символы")
    except Exception as error:
        log_error(error, "check_text")
        raise


def read_update(data):
    try:
        check_text(data)
        fields = {"title", "description", "teacher_id", "start_date", "end_date"}
        if set(data) - fields or any((value is None for value in data.values())):
            raise HTTPException(422, "Неверные поля карточки")
        values = {
            name: value.strip() if isinstance(value, str) and name != "password" else value
            for name, value in data.items()
        }
        try:
            for key in ("start_date", "end_date"):
                if key in values:
                    values[key] = date.fromisoformat(values[key])
            if "teacher_id" in values and (
                type(values["teacher_id"]) is not int or values["teacher_id"] <= 0
            ):
                raise ValueError()
            for key, minimum, maximum in [("title", 3, 200), ("description", 0, 5000)]:
                if key in values and (
                    not isinstance(values[key], str) or not minimum <= len(values[key]) <= maximum
                ):
                    raise ValueError()
        except (TypeError, ValueError):
            raise HTTPException(422, "Проверьте название, преподавателя и даты")
        return values
    except Exception as error:
        log_error(error, "read_update")
        raise


def read_olympiad(data):
    try:
        if not {"title", "teacher_id", "start_date", "end_date"}.issubset(data):
            raise HTTPException(422, "Заполните название, преподавателя и даты")
        values = read_update(data)
        if values["end_date"] < values["start_date"]:
            raise HTTPException(422, "Неверный порядок дат")
        if (
            not 2000 <= values["start_date"].year <= 2100
            or not 2000 <= values["end_date"].year <= 2100
        ):
            raise HTTPException(422, "Год должен быть от 2000 до 2100")
        return values
    except Exception as error:
        log_error(error, "read_olympiad")
        raise


def read_user(data):
    try:
        check_text(data)
        fields = {
            "username",
            "password",
            "full_name",
            "last_name",
            "first_name",
            "middle_name",
            "email",
            "role",
            "birth_date",
            "institution",
            "education_level",
            "course",
            "specialty",
        }
        required = {"username", "password", "email", "role"}
        if set(data) - fields or not required.issubset(data):
            raise HTTPException(422, "Проверьте поля пользователя")
        values = {
            name: value.strip() if isinstance(value, str) and name != "password" else value
            for name, value in data.items()
        }
        try:
            parts = {
                key: values.pop(key, None) for key in ("last_name", "first_name", "middle_name")
            }
            values["full_name"] = read_full_name(values.get("full_name"), **parts)
            for key, minimum, maximum in [
                ("username", 3, 50),
                ("password", 8, 128),
                ("full_name", 5, 150),
                ("email", 3, 254),
            ]:
                if not isinstance(values[key], str) or not minimum <= len(values[key]) <= maximum:
                    raise ValueError()
            if (
                not values["username"].isascii()
                or not values["username"].replace("_", "").isalnum()
            ):
                raise ValueError()
            if not values["password"].strip():
                raise ValueError()
            if not re.fullmatch("[^\\s@]+@[^\\s@]+\\.[^\\s@]+", values["email"]) or values[
                "role"
            ] not in ("teacher", "student"):
                raise ValueError()
            if "birth_date" in values:
                values["birth_date"] = date.fromisoformat(values["birth_date"])
                if not date(1900, 1, 1) <= values["birth_date"] < date.today():
                    raise ValueError()
            for key, maximum in [
                ("institution", 200),
                ("education_level", 100),
                ("specialty", 150),
            ]:
                if key in values and (
                    not isinstance(values[key], str) or len(values[key]) > maximum
                ):
                    raise ValueError()
            if "course" in values and (
                type(values["course"]) is not int or not 1 <= values["course"] <= 6
            ):
                raise ValueError()
            if values["role"] == "student" and (
                not all(
                    (
                        values.get(key)
                        for key in (
                            "birth_date",
                            "institution",
                            "education_level",
                            "course",
                            "specialty",
                        )
                    )
                )
            ):
                raise ValueError()
            if any(
                (
                    isinstance(value, str) and any((ord(char) < 32 for char in value))
                    for value in values.values()
                )
            ):
                raise ValueError()
        except (TypeError, ValueError):
            raise HTTPException(422, "Проверьте данные пользователя")
        return values
    except Exception as error:
        log_error(error, "read_user")
        raise
