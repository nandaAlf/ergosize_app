## Ergosize App
# 🌟 Descripción del Proyecto
Ergosizeees una aplicación Django para la gestión y análisis de datos antropométricos. Proporciona una API REST completa con autenticación JWT, configuración CORS y base de datos PostgreSQL para un manejo eficiente de datos.

# 🚀 Despliegue Local
Prerrequisitos
Python 3.8+
PostgreSQL 12+
pip
virtualenv (recomendado)

1. Clonar el repositorio
bash
$ git clone <url-del-repositorio>
$ cd ergosize_app

2. Configurar entorno virtual
bash
-- Crear entorno virtual
$ python -m venv venv
 -- Activar entorno virtual
 Windows:
$ venv\Scripts\activate
Linux/Mac:
$ source venv/bin/activate

3. Instalar dependencias
bash
$ pip install -r requirements.txt

4. Configurar Base de Datos PostgreSQL
sql
-- Crear base de datos
CREATE DATABASE Ergosizes;

-- Opcional: Crear usuario específico (recomendado)
CREATE USER ergosize_user WITH PASSWORD 'tu_password_seguro';
GRANT ALL PRIVILEGES ON DATABASE ergosizes TO ergosize_user;

5. Configurar Variables de Entorno
Crear archivo .env en la raíz del proyecto:

# Entorno
ENVIRONMENT=local
DEBUG=True 

# Base de Datos PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=Ergosizes
DB_USER=postgres
DB_PASSWORD=tu_password_postgres
DB_HOST=localhost
DB_PORT=5432

# Seguridad
SECRET_KEY=tu_clave_secreta_generada_aqui

# Hosts permitidos
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# CORS (Para HTTP con React - vite)
CORS_ALLOWED_ORIGINS=http://localhost:5173

# Configuración de Email (MailTrap)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password

Aplicar migraciones (en la raíz del proyecto al nivel del archivo manage.py)
bash
$ python manage.py makemigrations
$ python manage.py migrate
-- Crear superusuario
bash
$ python manage.py createsuperuser

Opcional: Restaurar copia de seguridad
Si tienes un backup de la base de datos:
bash
-- Restaurar desde dump SQL
psql -U postgres -d ergosizes -f ruta/al/backup.sql
-- O usando pg_restore para backups binarios
pg_restore -U postgres -d ergosizes ruta/al/backup.dump
-- O usando pg_Admi o algun otro

Ejecutar servidor de desarrollo
bash
python manage.py runserver
La aplicación estará disponible en: http://localhost:8000

# 🌐 URLs Importantes
API: http://localhost:8000/api/
Admin: http://localhost:8000/admin/

#📦 Despliegue en Producción
Para despliegue en producción, crear un archivo .env:
# .env (Producción)
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=tu-clave-super-secreta-y-larga-aqui-generar-con-openssl

ALLOWED_HOSTS=tu-dominioBackend.com,...,
CORS_ALLOWED_ORIGINS=https://tu-dominioFrontend.com,...,

# Base de Datos PostgreSQL (Render, Railway, AWS, etc.)
DB_NAME=myapp_prod
DB_USER=usuario_prod
DB_PASSWORD=password_complejo_prod
DB_HOST=tu-host-produccion
DB_PORT=5432

# Email real (SendGrid, AWS SES, etc.)
EMAIL_HOST_USER=tu_email_real
EMAIL_HOST_PASSWORD=tu_password_email_real
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=no-reply@tu-dominio.com

# 📝 Licencia
Este proyecto es para uso académico/investigación.