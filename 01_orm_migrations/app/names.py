from app.errors import log_error


def make_full_name(last_name, first_name, middle_name=None):
    try:
        if not isinstance(last_name, str) or not isinstance(first_name, str):
            raise ValueError("Укажите фамилию и имя")
        if middle_name is not None and (not isinstance(middle_name, str)):
            raise ValueError("Отчество должно быть строкой")
        last_name, first_name = (last_name.strip(), first_name.strip())
        if not last_name or not first_name:
            raise ValueError("Фамилия и имя не могут быть пустыми")
        parts = [last_name, first_name]
        if middle_name and middle_name.strip():
            parts.append(middle_name.strip())
        value = " ".join(parts)
        if not 5 <= len(value) <= 150:
            raise ValueError("ФИО должно содержать от 5 до 150 символов")
        if any(
            (
                ord(char) < 32 or 55296 <= ord(char) <= 57343 or ord(char) in (65534, 65535)
                for char in value
            )
        ):
            raise ValueError("ФИО содержит недопустимые символы")
        return value
    except Exception as error:
        log_error(error, "make_full_name")
        raise


def read_full_name(full_name=None, last_name=None, first_name=None, middle_name=None):
    try:
        if any((value is not None for value in (last_name, first_name, middle_name))):
            result = make_full_name(last_name, first_name, middle_name)
            if full_name is not None and full_name.strip() != result:
                raise ValueError("ФИО не совпадает с указанными частями имени")
            return result
        if not isinstance(full_name, str):
            raise ValueError("Укажите ФИО или фамилию и имя отдельно")
        parts = full_name.strip().split(maxsplit=2)
        if len(parts) < 2:
            raise ValueError("В ФИО нужны фамилия и имя")
        return make_full_name(parts[0], parts[1], parts[2] if len(parts) == 3 else None)
    except Exception as error:
        log_error(error, "read_full_name")
        raise
