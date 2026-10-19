from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user_create import UserCreate
from app.schemas.user_read import UserRead
from app.schemas.account_update import AccountUpdate
from app.security import hash_password, require_admin, require_staff
from app.services import save

router = APIRouter(prefix="/users", tags=["Учетные записи"])


@router.get("", response_model=list[UserRead], summary="Список учетных записей (администратор)")
def users(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.post("", response_model=UserRead, status_code=201, summary="Создать студента или преподавателя")
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


@router.patch("/{user_id}", response_model=UserRead, summary="Редактировать учетную запись")
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

