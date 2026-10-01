# Laboratorio - Configuración de Balanceadores de Carga

## Curso

Cloud Computing - Diseño y Desarrollo de Software

## Descripción

Este proyecto implementa un sistema de gestión de tareas utilizando Flask, Docker, MySQL y Nginx como balanceador de carga.

La aplicación se ejecuta mediante múltiples instancias de Flask y un balanceador Nginx que distribuye las solicitudes entre los diferentes servidores.

Además, se realizaron pruebas de persistencia de información utilizando MySQL y se implementaron diferentes ejercicios relacionados con balanceo de carga, disponibilidad, pruebas de rendimiento y enrutamiento mediante AWS Application Load Balancer.

---

## 1. Tecnologías utilizadas

- Python
- Flask
- MySQL
- Docker
- Docker Compose
- Nginx
- ApacheBench
- Amazon EC2
- AWS Application Load Balancer

---

## 2. Arquitectura local

La solución local está compuesta por:

```text
                    Cliente
                       |
                       v
                  Nginx :80
                       |
          +------------+------------+
          |            |            |
          v            v            v
       APP 1        APP 2        APP 3
       :5000        :5000        :5000
          |            |            |
          +------------+------------+
                       |
                       v
                     MySQL
                lab_balanceador
```

Las tres instancias Flask utilizan el mismo servidor MySQL para mantener la información compartida.

Esto permite que una tarea creada desde una instancia pueda ser consultada desde las demás instancias.

---

## 3. Funcionalidades de la aplicación

La aplicación denominada **TaskFlow** permite:

- Inicio de sesión.
- Visualización de tareas.
- Creación de tareas.
- Edición de tareas.
- Eliminación de tareas.
- Cambio del estado de las tareas.
- Persistencia de información en MySQL.
- Visualización de la instancia que respondió la solicitud.

La interfaz muestra el puerto de la instancia que atendió la solicitud, permitiendo observar el funcionamiento del balanceador.

---

## 4. Ejecución local

### 4.1 Requisitos

Se requiere tener instalado:

- Docker Desktop
- Git
- Windows PowerShell

### 4.2 Levantar el proyecto

Desde la carpeta del proyecto:

```powershell
cd C:\Users\LENOVO\lab-balanceador
```

Ejecutar:

```powershell
docker compose up -d --build
```

Verificar los contenedores:

```powershell
docker compose ps
```

La aplicación puede ser accedida mediante:

```text
http://localhost
```

---

## 5. Servicios Docker

El proyecto utiliza los siguientes servicios:

| Servicio   | Función                    |
|------------|----------------------------|
| `app1`     | Primera instancia Flask    |
| `app2`     | Segunda instancia Flask    |
| `app3`     | Tercera instancia Flask    |
| `nginx_lb` | Balanceador Nginx          |
| `mysql`    | Base de datos compartida   |

Las aplicaciones Flask utilizan internamente el puerto `5000`.

Nginx recibe las solicitudes mediante el puerto `80` y las distribuye entre las instancias disponibles.

---

## 6. Persistencia con MySQL

Se utiliza una base de datos denominada:

```text
lab_balanceador
```

La tabla principal es:

```sql
CREATE TABLE tareas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(255) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'pendiente',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

La persistencia permite mantener las tareas independientemente de cuál de las tres instancias Flask atienda la solicitud.

Para acceder a MySQL desde Docker:

```powershell
docker compose exec mysql mysql -u lab_user -p lab_balanceador
```

Para verificar las tablas:

```sql
SHOW TABLES;
```

Para consultar las tareas:

```sql
SELECT * FROM tareas;
```

---

## 7. Ejercicio 1 - Weighted Round Robin

Se configuró Nginx utilizando pesos diferentes para cada instancia:

```nginx
upstream backend_pool {
    server app1:5000 weight=5;
    server app2:5000 weight=3;
    server app3:5000 weight=2;
}
```

Los pesos utilizados fueron:

| Instancia | Peso |
|-----------|------|
| APP1      | 5    |
| APP2      | 3    |
| APP3      | 2    |

Por lo tanto, APP1 recibe una mayor proporción de solicitudes que APP2 y APP3.

Se realizaron 100 solicitudes mediante el balanceador y se contabilizaron las respuestas de cada instancia.

---

## 8. Ejercicio 2 - Passive Health Checks

Se configuraron comprobaciones pasivas utilizando:

```nginx
upstream backend_pool {
    server app1:5000 max_fails=2 fail_timeout=15s;
    server app2:5000 max_fails=2 fail_timeout=15s;
    server app3:5000 max_fails=2 fail_timeout=15s;
}
```

Para comprobar el comportamiento del balanceador se detuvo temporalmente APP2:

```powershell
docker compose stop app2
```

Se realizaron 30 solicitudes mediante Nginx.

Resultado obtenido:

| Instancia | Solicitudes |
|-----------|-------------|
| APP 1     | 14          |
| APP 2     | 0           |
| APP 3     | 16          |

Se comprobó que APP2 dejó de recibir solicitudes mientras se encontraba detenida y que las demás instancias continuaron atendiendo las peticiones.

Finalmente, APP2 fue restaurada:

```powershell
docker compose start app2
```

---

## 9. Ejercicio 3 - Load Test

Se utilizó **ApacheBench** para realizar una prueba de carga con:

- Solicitudes: 1000
- Concurrencia: 50

### Prueba directa contra APP1

Resultado:

```text
Complete requests:    1000
Failed requests:      0
Time taken:           3.232 seconds
Requests per second:  309.37
```

Comando utilizado:

```powershell
docker run --rm --network lab-balanceador_default httpd:2.4-alpine ab -n 1000 -c 50 http://app1:5000/
```

### Prueba mediante Nginx

Resultado:

```text
Complete requests:    1000
Failed requests:      0
Time taken:           0.972 seconds
Requests per second:  1029.33
```

Comando utilizado:

```powershell
docker run --rm --network host httpd:2.4-alpine ab -n 1000 -c 50 http://127.0.0.1/
```

En la prueba realizada, el acceso mediante Nginx presentó un mayor número de solicitudes por segundo debido a la distribución de las solicitudes entre las instancias disponibles.

---

## 10. Ejercicio 4 - AWS Application Load Balancer

Se implementó un Application Load Balancer en AWS utilizando dos instancias EC2.

### Instancias

- `ec2-web`
- `ec2-api`

Ambas instancias utilizaron Amazon Linux 2023 y se configuraron para recibir tráfico HTTP por el puerto 80.

### Target Groups

Se crearon:

- `tg-web`
- `tg-api`

Configuración:

```text
tg-web -> ec2-web
tg-api -> ec2-api
```

### Regla de enrutamiento

El Application Load Balancer fue configurado para utilizar:

```text
/api/* -> tg-api
```

Mientras que la ruta predeterminada:

```text
/ -> tg-web
```

De esta manera, las solicitudes son dirigidas al servidor correspondiente según la ruta solicitada.

### Pruebas

| Solicitud | Resultado                |
|-----------|--------------------------|
| `/`       | Servidor WEB - EC2 1     |
| `/api/`   | Servidor API - EC2 2     |

Esto permitió comprobar el funcionamiento del enrutamiento basado en rutas mediante AWS Application Load Balancer.

---

## 11. Ejercicios completados

Los ejercicios completados corresponden a:

1. Configuración local con Docker y Nginx.
2. Weighted Round Robin.
3. Passive Health Checks.
4. Load Test con ApacheBench.
5. AWS Application Load Balancer con Path Routing.

---

## 12. Evidencias

Las evidencias del laboratorio incluyen:

- Aplicación TaskFlow funcionando.
- Inicio de sesión.
- Gestión de tareas.
- Persistencia de información en MySQL.
- Configuración de Weighted Round Robin.
- Resultados de las 100 solicitudes.
- Configuración de Passive Health Checks.
- Detención y recuperación de APP2.
- Resultados de ApacheBench.
- Instancias EC2 en AWS.
- Target Groups.
- Reglas del Application Load Balancer.
- Pruebas de las rutas `/` y `/api/`.

---

## 13. Limpieza de recursos AWS

Después de finalizar las pruebas se eliminaron los recursos temporales utilizados para el laboratorio, incluyendo las instancias EC2 y el Application Load Balancer, con el objetivo de evitar costos innecesarios.

---

## 14. Conclusiones

- Se implementó una arquitectura distribuida utilizando Docker, Flask y Nginx, comprobando que un balanceador puede distribuir solicitudes entre múltiples instancias de una aplicación.
- Mediante Weighted Round Robin, Passive Health Checks y pruebas de carga con ApacheBench se pudo comprobar el comportamiento del balanceador frente a diferentes escenarios de distribución, disponibilidad y rendimiento.
- La implementación de AWS Application Load Balancer permitió aplicar enrutamiento basado en rutas, enviando las solicitudes generales al servidor web y las solicitudes `/api/*` al servidor API.

---

## Autor
Adriana Chinchayhuara

Laboratorio desarrollado para el curso de Cloud Computing - Diseño y Desarrollo de Software.