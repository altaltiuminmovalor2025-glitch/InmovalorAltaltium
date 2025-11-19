# Imagen base oficial de MySQL
FROM mysql:8.0

# Variables de entorno: nombre de base, usuario y contraseña
ENV MYSQL_DATABASE=djangodb
ENV MYSQL_ROOT_PASSWORD=1234
ENV MYSQL_USER=diana
ENV MYSQL_PASSWORD=1234

# Expone el puerto por defecto de MySQL
EXPOSE 3306

# (opcional) copia un archivo de inicialización
# COPY init.sql /docker-entrypoint-initdb.d/
