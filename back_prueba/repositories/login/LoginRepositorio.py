from psycopg.rows import dict_row

class AuthRepositorio:

    @staticmethod
    def obtener_usuario_por_email(cur, email: str) -> dict:
        cur.row_factory = dict_row
        cur.execute(
            """
            SELECT u.id, u.nombre, u.email, u.password_hash, u.sucursal_id, r.nombre as rol
            FROM usuarios u
            JOIN roles r ON u.rol_id = r.id
            WHERE u.email = %s AND u.activo = TRUE;
            """,
            (email,)
        )
        return cur.fetchone()
    @staticmethod
    def obtener_usuario_por_id(cur, usuario_id):
        cur.row_factory = dict_row
        cur.execute('''SELECT u.id,u.nombre,u.email,u.sucursal_id,r.nombre AS rol
            FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE u.id=%s AND u.activo=TRUE''', (usuario_id,))
        return cur.fetchone()
