"""REST-сервис учёта олимпиад. Маршруты обеих версий используют одну базу."""
from contextlib import asynccontextmanager
from datetime import date
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile, BadZipFile
from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import extract, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import JWT_SECRET, STORAGE, engine, get_db
from app.models import Attachment, Olympiad, Participation, User
from app.schemas import (AccountUpdate, AttachmentRead, OlympiadCreate, OlympiadPage,
                         OlympiadRead, OlympiadUpdate, ProfileUpdate, ProtocolUpdate,
                         ResultUpdate, UserCreate, UserRead)
from app.auth import (create_token, get_current_user, hash_password, require_admin,
                      require_staff, verify_password)
from app.reports import RESULT_NAMES, make_report

router = APIRouter()
v1_router = APIRouter()
v2_router = APIRouter()
MAX_FILE_SIZE = 5 * 1024 * 1024
KINDS = ("regulation", "task", "certificate", "award")
EXTENSIONS = (".pdf", ".docx", ".xlsx", ".png", ".jpg", ".jpeg", ".txt")


def save(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Такая запись уже существует или нарушает связи данных")


def get_olympiad(db, olympiad_id, lock=False):
    query = db.query(Olympiad).filter(Olympiad.id == olympiad_id)
    if lock:
        query = query.with_for_update()
    item = query.first()
    if not item:
        raise HTTPException(404, "Олимпиада не найдена")
    return item


def check_owner(olympiad, user):
    if user.role != "admin" and olympiad.teacher_id != user.id:
        raise HTTPException(403, "Это олимпиада другого преподавателя")


def check_draft(olympiad):
    if olympiad.protocol_status != "draft":
        raise HTTPException(409, "Изменения доступны только при статусе draft")


def check_teacher(db, teacher_id):
    teacher = db.get(User, teacher_id)
    if not teacher or teacher.role != "teacher" or not teacher.is_active:
        raise HTTPException(422, "Ответственным должен быть действующий преподаватель")


@router.post("/auth/token", summary="Получить JWT-токен")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash) or not user.is_active:
        raise HTTPException(401, "Неверный логин или пароль",
                            headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": create_token(user), "token_type": "bearer"}


@router.get("/users/me", response_model=UserRead, summary="Посмотреть свой профиль")
def profile(user: User = Depends(get_current_user)):
    return user


@router.patch("/users/me", response_model=UserRead, summary="Изменить свой профиль")
def update_profile(data: ProfileUpdate, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    for name, value in data.model_dump(exclude_unset=True).items():
        setattr(user, name, str(value).lower() if name == "email" else value)
    save(db)
    return user


@router.get("/users", response_model=list[UserRead], summary="Список учетных записей (администратор)")
def users(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.post("/users", response_model=UserRead, status_code=201, summary="Создать студента или преподавателя")
def create_user(data: UserCreate, user: User = Depends(require_staff),
                db: Session = Depends(get_db)):
    if user.role == "teacher" and data.role != "student":
        raise HTTPException(403, "Преподаватель создаёт только студентов")
    values = data.model_dump(exclude={"password"})
    values["email"] = str(values["email"]).lower()
    item = User(**values, password_hash=hash_password(data.password), created_by=user.id)
    db.add(item)
    save(db)
    return item


@router.patch("/users/{user_id}", response_model=UserRead, summary="Редактировать учетную запись")
def update_user(user_id: int, data: AccountUpdate, user: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    item = db.get(User, user_id)
    if not item:
        raise HTTPException(404, "Пользователь не найден")
    if item.id == user.id and data.is_active is False:
        raise HTTPException(409, "Нельзя заблокировать собственную учетную запись")
    values = data.model_dump(exclude_unset=True)
    if "password" in values:
        item.password_hash = hash_password(values.pop("password"))
        item.token_version += 1
    if "is_active" in values:
        item.token_version += 1
    for name, value in values.items():
        setattr(item, name, str(value).lower() if name == "email" else value)
    save(db)
    return item


def filtered_query(db, year=None, search=None):
    query = db.query(Olympiad)
    if year:
        query = query.filter(extract("year", Olympiad.start_date) == year)
    if search:
        # autoescape не даёт символам % и _ превратиться в шаблон поиска.
        query = query.filter(Olympiad.title.icontains(search, autoescape=True))
    return query.order_by(Olympiad.start_date, Olympiad.id)


@v1_router.get("/olympiads", response_model=list[OlympiadRead], summary="Все олимпиады, фильтр по году")
def list_olympiads(year: int | None = Query(default=None, ge=2000, le=2100),
                   db: Session = Depends(get_db)):
    return filtered_query(db, year).all()


@v2_router.get("/olympiads", response_model=OlympiadPage, summary="Олимпиады: поиск, год, пагинация")
def list_olympiads_v2(year: int | None = Query(default=None, ge=2000, le=2100),
                      search: str | None = Query(default=None, max_length=100),
                      page: int = Query(default=1, ge=1),
                      page_size: int = Query(default=10, ge=1, le=100),
                      db: Session = Depends(get_db)):
    query = filtered_query(db, year, search)
    return {"items": query.offset((page - 1) * page_size).limit(page_size).all(),
            "total": query.count(), "page": page, "page_size": page_size}


@router.get("/olympiads/{olympiad_id}", response_model=OlympiadRead, summary="Карточка олимпиады")
def olympiad_detail(olympiad_id: int, db: Session = Depends(get_db)):
    return get_olympiad(db, olympiad_id)


@router.post("/olympiads", response_model=OlympiadRead, status_code=201, summary="Создать олимпиаду")
def create_olympiad(data: OlympiadCreate, user: User = Depends(require_admin),
                    db: Session = Depends(get_db)):
    check_teacher(db, data.teacher_id)
    item = Olympiad(**data.model_dump())
    db.add(item)
    save(db)
    return item


@router.patch("/olympiads/{olympiad_id}", response_model=OlympiadRead, summary="Изменить поля карточки")
def patch_olympiad(olympiad_id: int, data: OlympiadUpdate,
                   user: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id, lock=True)
    check_draft(item)
    values = data.model_dump(exclude_unset=True)
    if "teacher_id" in values:
        check_teacher(db, values["teacher_id"])
    start = values.get("start_date", item.start_date)
    end = values.get("end_date", item.end_date)
    if end < start:
        raise HTTPException(422, "Окончание не может быть раньше начала")
    for name, value in values.items():
        setattr(item, name, value)
    save(db)
    return item


@router.delete("/olympiads/{olympiad_id}", status_code=204, summary="Удалить пустую олимпиаду")
def delete_olympiad(olympiad_id: int, user: User = Depends(require_admin),
                    db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id, lock=True)
    check_draft(item)
    if db.query(Participation).filter_by(olympiad_id=item.id).first() or db.query(Attachment).filter_by(olympiad_id=item.id).first():
        raise HTTPException(409, "Сначала удалите записи участия и документы")
    db.delete(item)
    save(db)
    return Response(status_code=204)


def participation_data(item, student, show_result=True):
    return {"id": item.id, "olympiad_id": item.olympiad_id,
            "student_id": item.student_id, "full_name": student.full_name,
            "score": float(item.score) if item.score is not None and show_result else None,
            "result": item.result if show_result else None}


@router.post("/olympiads/{olympiad_id}/participations", status_code=201, summary="Записаться на олимпиаду")
def enroll(olympiad_id: int, user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    if user.role != "student":
        raise HTTPException(403, "Записываться может только студент")
    olympiad = get_olympiad(db, olympiad_id, lock=True)
    check_draft(olympiad)
    if olympiad.end_date < date.today():
        raise HTTPException(409, "Приём заявок завершён")
    item = Participation(olympiad_id=olympiad.id, student_id=user.id)
    db.add(item)
    save(db)
    return participation_data(item, user, False)


@router.get("/users/me/participations", summary="Свои заявки и опубликованные результаты")
def my_participations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Participation, Olympiad).join(Olympiad).filter(Participation.student_id == user.id).order_by(Participation.id).all()
    data = []
    for item, olympiad in rows:
        row = participation_data(item, user, olympiad.protocol_status == "published")
        row.update({"title": olympiad.title, "protocol_status": olympiad.protocol_status})
        data.append(row)
    return data


@router.get("/olympiads/{olympiad_id}/participations", summary="Заявки для ответственного преподавателя")
def list_participations(olympiad_id: int, user: User = Depends(require_staff),
                        db: Session = Depends(get_db)):
    olympiad = get_olympiad(db, olympiad_id)
    check_owner(olympiad, user)
    rows = db.query(Participation, User).join(User, User.id == Participation.student_id).filter(Participation.olympiad_id == olympiad_id).order_by(Participation.id).all()
    return [participation_data(item, student) for item, student in rows]


@router.put("/participations/{participation_id}/result", summary="Записать баллы и результат")
def update_result(participation_id: int, data: ResultUpdate,
                   user: User = Depends(require_staff), db: Session = Depends(get_db)):
    item = db.get(Participation, participation_id)
    if not item:
        raise HTTPException(404, "Заявка не найдена")
    olympiad = get_olympiad(db, item.olympiad_id, lock=True)
    check_owner(olympiad, user)
    check_draft(olympiad)
    item.score = data.score
    item.result = data.result
    save(db)
    return participation_data(item, db.get(User, item.student_id))


@router.delete("/participations/{participation_id}", status_code=204, summary="Удалить заявку до подготовки протокола")
def cancel(participation_id: int, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    item = db.get(Participation, participation_id)
    if not item:
        raise HTTPException(404, "Заявка не найдена")
    olympiad = get_olympiad(db, item.olympiad_id, lock=True)
    if user.role == "student":
        if item.student_id != user.id:
            raise HTTPException(403, "Это заявка другого студента")
    else:
        check_owner(olympiad, user)
    check_draft(olympiad)
    db.delete(item)
    save(db)
    return Response(status_code=204)


def protocol_rows(db, olympiad_id):
    return db.query(Participation, User).join(User, User.id == Participation.student_id).filter(Participation.olympiad_id == olympiad_id).order_by(Participation.score.desc().nullslast(), Participation.id).all()


def protocol_data(db, item):
    return {"olympiad_id": item.id, "title": item.title, "status": item.protocol_status,
            "participants": [participation_data(p, s) for p, s in protocol_rows(db, item.id)]}


@router.get("/protocols", response_model=list[OlympiadRead], summary="Состояния протоколов (служебный список)")
def list_protocols(user: User = Depends(require_staff), db: Session = Depends(get_db)):
    query = db.query(Olympiad)
    if user.role == "teacher":
        query = query.filter(Olympiad.teacher_id == user.id)
    return query.order_by(Olympiad.id).all()


@router.get("/olympiads/{olympiad_id}/protocol", summary="Опубликованный протокол (общедоступный)")
def public_protocol(olympiad_id: int, db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    if item.protocol_status != "published":
        raise HTTPException(404, "Протокол ещё не опубликован")
    return protocol_data(db, item)


@router.get("/olympiads/{olympiad_id}/protocol-draft", summary="Просмотреть служебный протокол")
def private_protocol(olympiad_id: int, user: User = Depends(require_staff),
                      db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    check_owner(item, user)
    return protocol_data(db, item)


@router.patch("/olympiads/{olympiad_id}/protocol", summary="Подготовить, отозвать или опубликовать протокол")
def set_protocol_status(olympiad_id: int, data: ProtocolUpdate,
                         user: User = Depends(require_staff), db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id, lock=True)
    check_owner(item, user)
    current = item.protocol_status
    if data.status == "published" and user.role != "admin":
        raise HTTPException(403, "Публикует только администратор")
    if (current, data.status) not in [("draft", "prepared"), ("prepared", "draft"), ("prepared", "published")]:
        raise HTTPException(409, "Недопустимый переход статуса протокола")
    if data.status == "prepared":
        if item.end_date > date.today():
            raise HTTPException(409, "Олимпиада ещё не завершена")
        query = db.query(Participation).filter_by(olympiad_id=item.id)
        if not query.count() or query.filter(or_(Participation.score.is_(None), Participation.result.is_(None))).count():
            raise HTTPException(409, "Укажите баллы и результат каждого участника")
    item.protocol_status = data.status
    save(db)
    return {"status": item.protocol_status}


@router.get("/olympiads/{olympiad_id}/reports/protocol", summary="Скачать протокол Word или Excel")
def export_protocol(olympiad_id: int, file_format: str = Query(default="docx", alias="format"),
                      user: User = Depends(require_staff), db: Session = Depends(get_db)):
    item = get_olympiad(db, olympiad_id)
    check_owner(item, user)
    rows = []
    for number, (part, student) in enumerate(protocol_rows(db, item.id), 1):
        rows.append([number, student.full_name, float(part.score) if part.score is not None else "—",
                     RESULT_NAMES.get(part.result, "Не определён")])
    title = f"Протокол: {item.title}. Статус: {item.protocol_status}"
    return make_report(title, ["№", "ФИО", "Баллы", "Результат"], rows, file_format, f"protocol_{item.id}")


@router.get("/reports/annual", summary="Годовой отчёт по опубликованным результатам")
def annual_report(year: int = Query(ge=2000, le=2100),
                   file_format: str = Query(default="xlsx", alias="format"),
                   user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(Olympiad, Participation, User).join(Participation, Participation.olympiad_id == Olympiad.id).join(User, User.id == Participation.student_id).filter(extract("year", Olympiad.start_date) == year, Olympiad.protocol_status == "published").order_by(Olympiad.start_date, Olympiad.id, Participation.id).all()
    data = [[o.title, o.start_date.isoformat(), s.full_name, float(p.score), RESULT_NAMES[p.result]] for o, p, s in rows]
    return make_report(f"Участие студентов в олимпиадах за {year} год. Записей участия: {len(data)}",
                       ["Олимпиада", "Дата", "ФИО", "Баллы", "Результат"], data,
                       file_format, f"annual_{year}")


def validate_file(filename, content):
    extension = Path(filename).suffix.lower()
    if extension not in EXTENSIONS or not content:
        raise HTTPException(422, "Нужен непустой PDF, DOCX, XLSX, PNG, JPG или TXT")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "Размер файла превышает 5 МБ")
    valid = True
    if extension == ".pdf":
        valid = content.startswith(b"%PDF-")
    elif extension == ".png":
        valid = content.startswith(b"\x89PNG\r\n\x1a\n")
    elif extension in (".jpg", ".jpeg"):
        valid = content.startswith(b"\xff\xd8\xff")
    elif extension in (".docx", ".xlsx"):
        try:
            with ZipFile(BytesIO(content)) as archive:
                expected = "word/document.xml" if extension == ".docx" else "xl/workbook.xml"
                valid = expected in archive.namelist() and sum(i.file_size for i in archive.infolist()) <= 20 * 1024 * 1024
        except BadZipFile:
            valid = False
    elif extension == ".txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            valid = False
    if not valid:
        raise HTTPException(422, "Содержимое файла не соответствует расширению")
    return extension


def store_file(db, olympiad_id, kind, title, filename, content):
    if kind not in KINDS or not 1 <= len(title.strip()) <= 150:
        raise HTTPException(422, "Проверьте тип и название документа")
    filename = filename.replace("\\", "/").split("/")[-1]
    if len(filename) > 200:
        raise HTTPException(422, "Слишком длинное имя файла")
    extension = validate_file(filename, content)
    STORAGE.mkdir(parents=True, exist_ok=True)
    stored_name = uuid4().hex + extension
    (STORAGE / stored_name).write_bytes(content)
    item = Attachment(olympiad_id=olympiad_id)
    db.add(item)
    item.kind, item.title = kind, title.strip()
    item.original_name, item.stored_name = filename, stored_name
    try:
        save(db)
    except Exception:
        (STORAGE / stored_name).unlink(missing_ok=True)
        raise
    return item


def get_attachment(db, attachment_id):
    item = db.get(Attachment, attachment_id)
    if not item:
        raise HTTPException(404, "Документ не найден")
    return item


@router.get("/olympiads/{olympiad_id}/attachments", response_model=list[AttachmentRead], summary="Положение и бланки; задания прошлых лет")
def list_files(olympiad_id: int, db: Session = Depends(get_db)):
    olympiad = get_olympiad(db, olympiad_id)
    query = db.query(Attachment).filter_by(olympiad_id=olympiad.id)
    if olympiad.start_date.year >= date.today().year:
        query = query.filter(Attachment.kind != "task")
    return query.order_by(Attachment.id).all()


@router.get("/attachments/{attachment_id}", summary="Скачать общедоступный документ")
def download(attachment_id: int, db: Session = Depends(get_db)):
    item = get_attachment(db, attachment_id)
    olympiad = get_olympiad(db, item.olympiad_id)
    if item.kind == "task" and olympiad.start_date.year >= date.today().year:
        raise HTTPException(404, "Доступны задания только прошлых лет")
    path = STORAGE / item.stored_name
    if not path.is_file():
        raise HTTPException(404, "Файл отсутствует в хранилище")
    return FileResponse(path, filename=item.original_name, media_type="application/octet-stream",
                         headers={"X-Content-Type-Options": "nosniff"})


@router.get("/olympiads/{olympiad_id}/attachments/manage", response_model=list[AttachmentRead], summary="Все файлы ответственного преподавателя")
def manage_files(olympiad_id: int, user: User = Depends(require_staff), db: Session = Depends(get_db)):
    olympiad = get_olympiad(db, olympiad_id)
    check_owner(olympiad, user)
    return db.query(Attachment).filter_by(olympiad_id=olympiad_id).order_by(Attachment.id).all()


@router.post("/olympiads/{olympiad_id}/attachments", response_model=AttachmentRead, status_code=201, summary="Прикрепить файл")
def upload(olympiad_id: int, kind: str = Form(), title: str = Form(), file: UploadFile = File(),
            user: User = Depends(require_staff), db: Session = Depends(get_db)):
    check_owner(get_olympiad(db, olympiad_id), user)
    content = file.file.read(MAX_FILE_SIZE + 1)
    return store_file(db, olympiad_id, kind, title, file.filename or "", content)


@router.delete("/attachments/{attachment_id}", status_code=204, summary="Удалить документ")
def delete_file(attachment_id: int, user: User = Depends(require_staff), db: Session = Depends(get_db)):
    item = get_attachment(db, attachment_id)
    check_owner(get_olympiad(db, item.olympiad_id), user)
    path = STORAGE / item.stored_name
    db.delete(item)
    save(db)
    path.unlink(missing_ok=True)
    return Response(status_code=204)


@asynccontextmanager
async def lifespan(app):
    if len(JWT_SECRET) < 32 or JWT_SECRET == "PUT_RANDOM_SECRET_HERE":
        raise RuntimeError("Задайте JWT_SECRET длиной от 32 символов в .env")
    # Таблицы создаются отдельной командой python init_db.py.
    with engine.connect():
        pass
    yield


app = FastAPI(title="Учёт олимпиад", lifespan=lifespan)
api_v1 = FastAPI(title="Олимпиады v1", version="1.0")
api_v2 = FastAPI(title="Олимпиады v2", version="2.0")
api_v1.include_router(v1_router)
api_v1.include_router(router)
api_v2.include_router(v2_router)
api_v2.include_router(router)
app.mount("/api/v1", api_v1)
app.mount("/api/v2", api_v2)


@app.get("/")
def index():
    return {"message": "Сервис олимпиад", "docs": "/api/v1/docs", "docs_v2": "/api/v2/docs"}
