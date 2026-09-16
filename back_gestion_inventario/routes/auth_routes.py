from controllers import auth_controller as controller
from core.dependencies import Db, User
from dtos.schemas import Login, UsuarioResponse
from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login")
def login(payload: Login, db: Db):
    return controller.login(payload, db)


@router.get("/me", response_model=UsuarioResponse)
def me(user: User):
    return controller.me(user)
