from service.login.LoginService import AuthService

class AuthControlador:

    @staticmethod
    def login(datos: dict) -> tuple:
        return AuthService.login(datos)