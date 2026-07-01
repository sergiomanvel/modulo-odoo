# Despliegue en VPS Ubuntu con Docker — Service Quote Manager (Odoo 17.0)

Guía para probar el proyecto en un **VPS Ubuntu con Docker**, pensada para
equipos que **no pueden ejecutar Docker Desktop en local** (p. ej. CPU sin
SLAT / SecondLevelAddressTranslationExtensions = False). En un VPS Linux, Docker
usa el kernel nativo y ese requisito no aplica.

> No modifica el módulo `service_quote_manager`. Reutiliza el
> `docker-compose.yml` de la raíz del proyecto. Complementa a
> `service_quote_manager/INSTALL_TESTING.md`.

---

## 1. Requisitos mínimos del VPS

| Recurso | Mínimo | Recomendado |
|---|---|---|
| SO | Ubuntu 22.04 LTS | Ubuntu 22.04 / 24.04 LTS |
| CPU | 1 vCPU | 2 vCPU |
| RAM | 2 GB (+2 GB swap) | 4 GB |
| Disco | 15 GB | 25 GB SSD |
| Red | IP pública + puerto 22 (SSH) | + poder abrir/cerrar 8069 temporalmente |
| Acceso | usuario con `sudo` | — |

> Con 2 GB de RAM, **añade swap** (ver §9) para evitar que el kernel mate el
> proceso de Odoo durante la instalación.

Proveedores válidos: Hetzner, DigitalOcean, Contabo, OVH, AWS Lightsail, etc.

---

## 2. Instalar Docker y Docker Compose en Ubuntu

Conéctate por SSH y ejecuta (método oficial de Docker):

```bash
# Dependencias base
sudo apt-get update
sudo apt-get install -y ca-certificates curl

# Clave GPG del repositorio de Docker
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Repositorio de Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker Engine + Compose plugin
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Verifica e (opcional) usa Docker sin `sudo`:

```bash
sudo docker run --rm hello-world      # prueba
docker compose version                # debe imprimir la versión del plugin

# Ejecutar docker sin sudo (recomendado):
sudo usermod -aG docker $USER
newgrp docker                         # o cierra sesión y vuelve a entrar
```

---

## 3. Subir la carpeta ProyectoODOO al VPS

Desde tu **PC Windows** (PowerShell), con `scp` (incluido en Windows 10/11):

```powershell
# Sustituye usuario e IP_DEL_VPS
scp -r "E:\ProyectosClaude\ProyectoODOO" usuario@IP_DEL_VPS:/home/usuario/
```

Alternativas:

- **rsync** (desde WSL/Git Bash; más rápido y permite excluir temporales):
  ```bash
  rsync -avz --exclude '.agents' --exclude '__pycache__' --exclude 'skills-lock.json' \
    /mnt/e/ProyectosClaude/ProyectoODOO/ usuario@IP_DEL_VPS:/home/usuario/ProyectoODOO/
  ```
- **Git** (si el proyecto está en un repositorio): `git clone` directamente en el VPS.
- **ZIP + SFTP** con WinSCP o FileZilla si prefieres interfaz gráfica.

No necesitas subir `.agents/` ni `skills-lock.json` (solo son las skills locales).
Lo imprescindible es `docker-compose.yml` y la carpeta `service_quote_manager/`.

Verifica en el VPS que la estructura llegó bien:

```bash
cd ~/ProyectoODOO
ls -la                                   # debe verse docker-compose.yml y service_quote_manager/
cat docker-compose.yml | grep extra-addons
# Debe aparecer: ./service_quote_manager:/mnt/extra-addons/service_quote_manager
```

---

## 4. Arrancar PostgreSQL y Odoo 17

```bash
cd ~/ProyectoODOO
docker compose up -d          # descarga imágenes odoo:17.0 y postgres:15 y arranca ambos
docker compose ps             # ambos servicios en estado "running"
docker compose logs -f odoo   # ver el arranque; Ctrl+C para salir del log
```

La primera vez tarda unos minutos en descargar las imágenes.

---

## 5. Instalar service_quote_manager

Instalación por línea de comandos (crea la BD `sqm_demo`, con datos demo, sin
pedir contraseña maestra):

```bash
cd ~/ProyectoODOO
docker compose run --rm odoo odoo -d sqm_demo -i service_quote_manager --stop-after-init
docker compose restart odoo   # para que el servidor web recargue y liste la BD
```

Alternativa por interfaz: abre `http://IP_DEL_VPS:8069`, crea la BD marcando
*"Load demonstration data"*, activa el **modo desarrollador**, ve a
**Apps → Actualizar lista de aplicaciones**, busca *Service Quote Manager* e
**Instalar**.

---

## 6. Ejecutar los tests

```bash
cd ~/ProyectoODOO
docker compose run --rm odoo odoo -d sqm_test -i service_quote_manager \
  --test-enable --test-tags=/service_quote_manager --stop-after-init
```

En la salida busca la línea del módulo con `0 failed, 0 error`. Los tests cubren
márgenes, flujo de estados, la regla de aceptación de solicitudes no rentables y
el cron de vencidas.

---

## 7. Abrir Odoo desde el navegador

1. Abre el puerto en el cortafuegos del VPS (solo mientras pruebas):
   ```bash
   sudo ufw allow 8069/tcp     # si usas ufw
   sudo ufw status
   ```
   > Si tu proveedor tiene un *Security Group* / firewall de red (AWS, GCP,
   > Oracle...), abre también ahí el puerto 8069 (TCP), idealmente **restringido
   > a tu IP**.
2. Navega a: `http://IP_DEL_VPS:8069`
3. Selecciona la BD `sqm_demo` e inicia sesión (usuario `admin`).

> **Seguridad:** cambia la contraseña de `admin` antes de exponerlo, y no dejes
> el puerto abierto más tiempo del necesario (ver §8).

### Alternativa más segura: túnel SSH (sin abrir 8069 al mundo)

En vez de abrir el puerto, deja Odoo escuchando solo en local y crea un túnel:

```bash
# En el VPS: edita docker-compose.yml y cambia el mapeo de puertos a:
#   - "127.0.0.1:8069:8069"
# luego: docker compose up -d
```
```powershell
# En tu PC Windows:
ssh -L 8069:localhost:8069 usuario@IP_DEL_VPS
# y abre http://localhost:8069 en tu navegador
```

---

## 8. Cerrar el puerto 8069 después de la prueba

Elige según cómo lo abriste:

```bash
# a) Cerrar el puerto en ufw
sudo ufw deny 8069/tcp
# o eliminar la regla que lo permitía:
sudo ufw delete allow 8069/tcp
sudo ufw status

# b) Parar solo el servicio web de Odoo (deja la BD levantada)
cd ~/ProyectoODOO
docker compose stop odoo

# c) Parar todo el stack (Odoo + PostgreSQL)
docker compose down            # conserva el volumen de datos 'odoo-db'
# docker compose down -v       # además BORRA la BD (empieza de cero la próxima vez)
```

Si abriste el puerto también en el *Security Group* del proveedor, ciérralo allí.

---

## 9. Errores comunes y soluciones

| Síntoma | Causa | Solución |
|---|---|---|
| `permission denied ... /var/run/docker.sock` | Usuario no está en el grupo `docker` | `sudo usermod -aG docker $USER` y reconecta, o usa `sudo docker ...` |
| El navegador no abre `:8069` | Puerto cerrado en ufw o en el firewall del proveedor | `sudo ufw allow 8069/tcp` y abre el puerto en el panel del VPS |
| Odoo muere durante la instalación / `Killed` | Poca RAM (OOM) | Añade swap (abajo) o sube el plan a 4 GB |
| `could not connect to server` / `role "odoo" does not exist` | Credenciales de `odoo` ≠ `postgres` | Deben coincidir `USER/PASSWORD` con `POSTGRES_USER/PASSWORD` (ya coinciden en el compose) |
| Módulo no aparece en Apps | Falta *Actualizar lista* / modo dev; o volumen mal montado | Verifica `docker compose exec odoo ls /mnt/extra-addons/service_quote_manager` |
| Datos demo ausentes | BD creada sin demo | Reinstala en una BD nueva con `-i ... ` (carga demo por defecto) |
| Pantalla pide *Master Password* al crear BD | Gestor de BD de Odoo | Crea la BD por CLI (§5), que no la pide |
| Imágenes no descargan | DNS/red del VPS | `sudo systemctl restart docker`; revisa salida a internet |

**Añadir 2 GB de swap (para VPS de 2 GB de RAM):**

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab   # persistente tras reinicio
free -h
```

---

## 10. Checklist para capturas y demo de entrevista

**Capturas a tomar** (para el porfolio / entrevista):
- [ ] **Apps**: tarjeta *Service Quote Manager* con su icono azul.
- [ ] **Tablero Kanban**: columnas por estado + badges de margen + marca *Vencida*.
- [ ] **Lista** con filtros (*Abiertas*, *Vencidas*, *No rentables*) aplicados.
- [ ] **Formulario** de una solicitud: statusbar, smart buttons y notebook.
- [ ] **Ribbon rojo *No rentable*** en `Taller Mecánico RM`.
- [ ] **Wizard** *Presupuesto rápido* con el preview de coste/precio/margen.
- [ ] **Error de la regla**: intento de *Aceptar* la no rentable como *User*.
- [ ] **Actividad de vencida** creada por el cron en `Gimnasio FitZone`.
- [ ] **Panel**: gráfico y tabla dinámica de rentabilidad.
- [ ] **Salida de tests**: `0 failed, 0 error`.

**Preparación de la demo:**
- [ ] BD `sqm_demo` instalada con datos demo.
- [ ] Contraseña de `admin` cambiada.
- [ ] Un usuario en *Service Quote User* y otro en *Service Quote Manager* creados.
- [ ] Puerto 8069 abierto solo durante la demo (o túnel SSH activo).
- [ ] Logs sin *tracebacks* (`docker compose logs odoo`).
- [ ] Tras la demo: puerto 8069 cerrado (§8).

---

## Comandos exactos (resumen)

```bash
# Arrancar Odoo 17 (PostgreSQL + Odoo)
cd ~/ProyectoODOO && docker compose up -d

# Instalar el módulo (BD nueva con demo)
docker compose run --rm odoo odoo -d sqm_demo -i service_quote_manager --stop-after-init
docker compose restart odoo

# Ejecutar los tests
docker compose run --rm odoo odoo -d sqm_test -i service_quote_manager --test-enable --test-tags=/service_quote_manager --stop-after-init

# Abrir puerto / cerrarlo tras la prueba
sudo ufw allow 8069/tcp
sudo ufw delete allow 8069/tcp
```
