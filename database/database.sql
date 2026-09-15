-- Crear el usuario exclusivo para la aplicación
CREATE USER admin_app WITH PASSWORD 'admin999';

-- Da privilegios sobre la base de datos a la aplicación
GRANT ALL PRIVILEGES ON DATABASE multi_sucursal TO app_user;