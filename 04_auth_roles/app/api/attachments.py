from app.errors import log_error
from app.database import fetch_all, fetch_one
import asyncio
from app.validation import Id
from datetime import date
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile, BadZipFile
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from psycopg import AsyncConnection
from app.config import MAX_FILE_SIZE, STORAGE
from app.database import get_db, execute
from app.models.attachment import Attachment
from app.models.user import User
from app.schemas.attachment_read import AttachmentRead
from app.schemas.api_model import has_invalid_text
from app.security import require_staff
from app.records import insert_attachment, update_fields
from app.services import check_owner, get_olympiad, save

router = APIRouter(tags=["Документы и бланки"])
KINDS = ("regulation", "task", "certificate", "award")
EXTENSIONS = (".pdf", ".docx", ".xlsx", ".png", ".jpg", ".jpeg", ".txt")


def validate_file(filename, content):
    try:
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
                    valid = (
                        expected in archive.namelist()
                        and sum((i.file_size for i in archive.infolist())) <= 20 * 1024 * 1024
                    )
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
    except Exception as error:
        log_error(error, "validate_file")
        raise


async def store_file(db, olympiad_id, kind, title, filename, content, item=None):
    try:
        if any((has_invalid_text(value) for value in (kind, title, filename))):
            raise HTTPException(422, "Текст содержит недопустимые управляющие символы")
        if kind not in KINDS or not 1 <= len(title.strip()) <= 150:
            raise HTTPException(422, "Проверьте тип и название документа")
        filename = filename.replace("\\", "/").split("/")[-1]
        if len(filename) > 200:
            raise HTTPException(422, "Слишком длинное имя файла")
        extension = await asyncio.to_thread(validate_file, filename, content)
        await asyncio.to_thread(STORAGE.mkdir, parents=True, exist_ok=True)
        stored_name = uuid4().hex + extension
        await asyncio.to_thread((STORAGE / stored_name).write_bytes, content)
        old_name = item.stored_name if item else None
        values = {
            "kind": kind,
            "title": title.strip(),
            "original_name": filename,
            "stored_name": stored_name,
        }
        try:
            if item is None:
                item = await insert_attachment(db, Attachment(olympiad_id=olympiad_id, **values))
            else:
                await update_fields(db, "attachments", item.id, values)
            await save(db)
        except Exception:
            await asyncio.to_thread((STORAGE / stored_name).unlink, missing_ok=True)
            raise
        if old_name:
            await asyncio.to_thread((STORAGE / old_name).unlink, missing_ok=True)
        return await get_attachment(db, item.id)
    except Exception as error:
        log_error(error, "store_file")
        raise


async def get_attachment(db, attachment_id):
    try:
        row = await fetch_one(db, "SELECT * FROM attachments WHERE id = %s", (attachment_id,))
        if not row:
            raise HTTPException(404, "Документ не найден")
        return Attachment(**row)
    except Exception as error:
        log_error(error, "get_attachment")
        raise


@router.get(
    "/olympiads/{olympiad_id}/attachments",
    response_model=list[AttachmentRead],
    summary="Положение и бланки; задания прошлых лет",
)
async def list_files(olympiad_id: Id, db: AsyncConnection = Depends(get_db)):
    try:
        olympiad = await get_olympiad(db, olympiad_id)
        if olympiad.start_date.year >= date.today().year:
            return await fetch_all(
                db,
                "SELECT id, olympiad_id, kind, title, original_name FROM attachments WHERE olympiad_id = %s AND kind <> 'task' ORDER BY id",
                (olympiad.id,),
            )
        return await fetch_all(
            db,
            "SELECT id, olympiad_id, kind, title, original_name FROM attachments WHERE olympiad_id = %s ORDER BY id",
            (olympiad.id,),
        )
    except Exception as error:
        log_error(error, "list_files")
        raise


@router.get(
    "/attachments/{attachment_id}",
    response_class=FileResponse,
    responses={
        200: {
            "content": {
                "application/octet-stream": {"schema": {"type": "string", "format": "binary"}}
            }
        }
    },
    summary="Скачать общедоступный документ",
)
async def download(attachment_id: Id, db: AsyncConnection = Depends(get_db)):
    try:
        item = await get_attachment(db, attachment_id)
        olympiad = await get_olympiad(db, item.olympiad_id)
        if item.kind == "task" and olympiad.start_date.year >= date.today().year:
            raise HTTPException(404, "Доступны задания только прошлых лет")
        path = STORAGE / item.stored_name
        if not await asyncio.to_thread(path.is_file):
            raise HTTPException(404, "Файл отсутствует в хранилище")
        return FileResponse(
            path,
            filename=item.original_name,
            media_type="application/octet-stream",
            headers={"X-Content-Type-Options": "nosniff"},
        )
    except Exception as error:
        log_error(error, "download")
        raise


@router.get(
    "/olympiads/{olympiad_id}/attachments/manage",
    response_model=list[AttachmentRead],
    summary="Все файлы ответственного преподавателя",
)
async def manage_files(
    olympiad_id: Id, user: User = Depends(require_staff), db: AsyncConnection = Depends(get_db)
):
    try:
        olympiad = await get_olympiad(db, olympiad_id)
        check_owner(olympiad, user)
        return await fetch_all(
            db,
            "SELECT id, olympiad_id, kind, title, original_name FROM attachments WHERE olympiad_id = %s ORDER BY id",
            (olympiad_id,),
        )
    except Exception as error:
        log_error(error, "manage_files")
        raise


@router.post(
    "/olympiads/{olympiad_id}/attachments",
    response_model=AttachmentRead,
    status_code=201,
    summary="Прикрепить файл",
)
async def upload(
    olympiad_id: Id,
    kind: str = Form(),
    title: str = Form(),
    file: UploadFile = File(),
    user: User = Depends(require_staff),
    db: AsyncConnection = Depends(get_db),
):
    try:
        check_owner(await get_olympiad(db, olympiad_id), user)
        content = await file.read(MAX_FILE_SIZE + 1)
        return await store_file(db, olympiad_id, kind, title, file.filename or "", content)
    except Exception as error:
        log_error(error, "upload")
        raise


@router.put(
    "/attachments/{attachment_id}",
    response_model=AttachmentRead,
    summary="Заменить файл или название",
)
async def replace(
    attachment_id: Id,
    kind: str = Form(),
    title: str = Form(),
    file: UploadFile = File(),
    user: User = Depends(require_staff),
    db: AsyncConnection = Depends(get_db),
):
    try:
        item = await get_attachment(db, attachment_id)
        check_owner(await get_olympiad(db, item.olympiad_id), user)
        return await store_file(
            db,
            item.olympiad_id,
            kind,
            title,
            file.filename or "",
            await file.read(MAX_FILE_SIZE + 1),
            item,
        )
    except Exception as error:
        log_error(error, "replace")
        raise


@router.delete("/attachments/{attachment_id}", status_code=204, summary="Удалить документ")
async def delete_file(
    attachment_id: Id, user: User = Depends(require_staff), db: AsyncConnection = Depends(get_db)
):
    try:
        item = await get_attachment(db, attachment_id)
        check_owner(await get_olympiad(db, item.olympiad_id), user)
        path = STORAGE / item.stored_name
        await execute(db, "DELETE FROM attachments WHERE id = %s", (item.id,))
        await save(db)
        await asyncio.to_thread(path.unlink, missing_ok=True)
        return Response(status_code=204)
    except Exception as error:
        log_error(error, "delete_file")
        raise
