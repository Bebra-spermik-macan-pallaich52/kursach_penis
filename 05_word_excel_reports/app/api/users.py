from app.errors import log_error
from app.database import fetch_all
import asyncio
from app.validation import Id
from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection
from app.database import get_db, execute
from app.models.user import User
from app.schemas.user_create import UserCreate
from app.schemas.user_read import UserRead
from app.schemas.account_update import AccountUpdate
from app.security import hash_password, require_admin, require_staff
from app.records import insert_user, update_fields
from app.services import get_user, save

router = APIRouter(prefix="/users", tags=["Учетные записи"])


@router.get("", response_model=list[UserRead], summary="Список учетных записей (администратор)")
async def users(user: User = Depends(require_admin), db: AsyncConnection = Depends(get_db)):
    try:
        return await fetch_all(
            db,
            "SELECT id, username, full_name, email, role, birth_date, institution, education_level, course, specialty, is_active FROM users ORDER BY id",
        )
    except Exception as error:
        log_error(error, "users")
        raise


@router.post(
    "", response_model=UserRead, status_code=201, summary="Создать студента или преподавателя"
)
async def create_user(
    data: UserCreate, user: User = Depends(require_staff), db: AsyncConnection = Depends(get_db)
):
    try:
        if user.role == "teacher" and data.role != "student":
            raise HTTPException(403, "Преподаватель создаёт только студентов")
        values = data.model_dump(exclude={"password"})
        values["email"] = str(values["email"]).lower()
        item = User(
            **values,
            password_hash=await asyncio.to_thread(hash_password, data.password),
            created_by=user.id
        )
        await insert_user(db, item)
        await save(db)
        return item
    except Exception as error:
        log_error(error, "create_user")
        raise


@router.patch("/{user_id}", response_model=UserRead, summary="Редактировать учетную запись")
async def update_user(
    user_id: Id,
    data: AccountUpdate,
    user: User = Depends(require_admin),
    db: AsyncConnection = Depends(get_db),
):
    try:
        item = await get_user(db, user_id)
        if item.id == user.id and data.is_active is False:
            raise HTTPException(409, "Нельзя заблокировать собственную учетную запись")
        values = data.model_dump(exclude_unset=True)
        revoke_tokens = "password" in values or "is_active" in values
        if "password" in values:
            values["password_hash"] = await asyncio.to_thread(hash_password, values.pop("password"))
        if "email" in values:
            values["email"] = str(values["email"]).lower()
        await update_fields(db, "users", user_id, values)
        if revoke_tokens:
            await execute(
                db, "UPDATE users SET token_version = token_version + 1 WHERE id = %s", (user_id,)
            )
        await save(db)
        return await get_user(db, user_id)
    except Exception as error:
        log_error(error, "update_user")
        raise
