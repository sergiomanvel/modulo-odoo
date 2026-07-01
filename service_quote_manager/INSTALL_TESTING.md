# Guía de instalación y pruebas — Service Quote Manager (Odoo 17.0)

Guía exacta para instalar y probar el módulo `service_quote_manager` en un
entorno **real de Odoo 17.0**. Dos opciones: **Docker** (recomendada en Windows)
e **instalación local con `odoo-bin`**.

> Complementa a `README.md` (uso) y `TECHNICAL_NOTES.md` (arquitectura).

---

## Opción 1 · Docker (recomendada)

### Estructura esperada

El `docker-compose.yml` va en la **raíz del proyecto**, junto a la carpeta del
módulo:

```
E:\ProyectosClaude\ProyectoODOO\
├── docker-compose.yml            ← en la raíz del proyecto
└── service_quote_manager\        ← el módulo
    ├── __manifest__.py
    └── ...
```

### docker-compose.yml

Ya incluido en la raíz del proyecto (`E:\ProyectosClaude\ProyectoODOO\docker-compose.yml`).
El volumen que monta el módulo debe ser **exactamente**:

```yaml
- ./service_quote_manager:/mnt/extra-addons/service_quote_manager
```

> ⚠ No uses una ruta cortada tipo `/mnt/extra-addons/ser`. La ruta destino debe
> terminar en `/service_quote_manager` completo.

### Configuración de addons_path

No hay que tocar nada: la imagen `odoo:17.0` ya incluye `/mnt/extra-addons` en su
`addons_path` por defecto. Solo montamos el módulo **dentro** de esa ruta.

### Arrancar Odoo

```powershell
cd E:\ProyectosClaude\ProyectoODOO
docker compose up -d
docker compose logs -f odoo      # ver arranque; Ctrl+C para salir del log
```

Abre `http://localhost:8069` y crea una BD **marcando "Load demonstration data"**.

### Instalar el módulo

Por línea de comandos (BD nueva `sqm_demo`, carga demo automáticamente):

```powershell
docker compose run --rm odoo odoo -d sqm_demo -i service_quote_manager --stop-after-init
```

O desde la UI: activa **modo desarrollador** → **Apps → Actualizar lista de
aplicaciones** → busca *Service Quote Manager* → **Instalar**.

### Ejecutar los tests

```powershell
docker compose run --rm odoo odoo -d sqm_test -i service_quote_manager --test-enable --test-tags=/service_quote_manager --stop-after-init
```

Busca en la salida: `service_quote_manager ... 0 failed, 0 error`.

### Errores típicos (Docker) y solución

| Síntoma | Causa | Solución |
|---|---|---|
| `Bind for 0.0.0.0:8069 failed: port is already allocated` | Puerto ocupado | Cambia el mapeo a `"8070:8069"` y entra por `:8070` |
| `could not connect to server` / `role "odoo" does not exist` | `USER/PASSWORD` de odoo ≠ `POSTGRES_USER/PASSWORD` | Que coincidan exactamente en ambos servicios |
| Módulo no aparece en Apps | Falta *Actualizar lista* o modo dev off; o volumen mal montado | Modo dev → Actualizar apps. Verifica: `docker compose exec odoo ls /mnt/extra-addons/service_quote_manager` |
| BD ya existía sin demo | Reusaste una BD | Usa un nombre nuevo o bórrala desde `/web/database/manager` |
| Volumen vacío en el contenedor (Windows) | File sharing del disco no habilitado | Docker Desktop → Settings → Resources → File Sharing → añade `E:\` |
| `permission denied` en el volumen | Permisos del host | Reinicia Docker Desktop; evita rutas sincronizadas con OneDrive |

---

## Opción 2 · Local con `odoo-bin`

> En Windows nativo Odoo es incómodo (PostgreSQL + build de dependencias). Lo más
> fiable es **WSL2 (Ubuntu)** o Linux; los comandos son los mismos. Requisitos:
> **Python 3.10/3.11**, **PostgreSQL** en marcha y las dependencias del código
> fuente de Odoo 17 (`pip install -r requirements.txt`).

### Estructura esperada

```
C:\odoo17\                         (o ~/odoo17 en WSL)
├── odoo-bin
├── odoo\                          (código fuente de Odoo 17)
├── addons\                        (addons estándar de Odoo)
└── odoo.conf                      ← lo creas

E:\ProyectosClaude\ProyectoODOO\
└── service_quote_manager\         ← tu módulo
```

### Configuración de addons_path (odoo.conf)

```ini
[options]
; addons_path apunta al DIRECTORIO PADRE que CONTIENE la carpeta del módulo,
; NO a la carpeta del módulo en sí.
addons_path = C:\odoo17\addons,E:\ProyectosClaude\ProyectoODOO
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo
```

En WSL/Linux, por ejemplo:
`addons_path = /home/user/odoo17/addons,/mnt/e/ProyectosClaude/ProyectoODOO`

### Arrancar Odoo

```powershell
cd C:\odoo17
python odoo-bin -c odoo.conf
```

Abre `http://localhost:8069` y crea la BD con datos demo.

### Instalar el módulo

```powershell
python odoo-bin -c odoo.conf -d sqm_demo -i service_quote_manager --stop-after-init
```

### Ejecutar los tests

```powershell
python odoo-bin -c odoo.conf -d sqm_test -i service_quote_manager --test-enable --test-tags=/service_quote_manager --stop-after-init
```

### Errores típicos (local) y solución

| Síntoma | Causa | Solución |
|---|---|---|
| El módulo no se detecta | `addons_path` apunta a la carpeta del módulo en vez de a su **padre** | Usa `...,E:\ProyectosClaude\ProyectoODOO` (el padre) |
| `role "odoo" does not exist` | Rol de PostgreSQL inexistente | `createuser -s odoo` y `ALTER USER odoo WITH PASSWORD 'odoo';` (o ajusta `db_user`) |
| `psycopg2` / `pg_config` falla al instalar | Falta libpq/dev | `pip install psycopg2-binary` |
| `wkhtmltopdf not found` (warning) | No hay binario PDF | Ignorable: este módulo no genera informes PDF |
| `database "sqm_test" already exists` | BD reutilizada | `dropdb sqm_test` antes de reinstalar (o usa otro nombre) |
| `Unsupported Python version` | Python 3.12+/3.9 | Usa 3.10 o 3.11 |
| Puerto ocupado | Otra instancia | Añade `xmlrpc_port = 8070` al `.conf` |

---

## Checklist final — listo para enseñar en entrevista

**Instalación / arranque**
- [ ] Logs sin *tracebacks*; Odoo arranca en `:8069`.
- [ ] En **Apps** aparece *Service Quote Manager* con su icono azul.
- [ ] Instala en BD limpia **con demo** sin errores.

**Datos y navegación**
- [ ] Menú **Service Quote Manager** con: Panel, Solicitudes, Tablero Kanban, Presupuesto rápido, Configuración.
- [ ] 8 solicitudes demo; todos los estados representados.
- [ ] Kanban con badges de margen y marca *Vencida* (Gimnasio FitZone).

**Funcionalidad clave**
- [ ] Statusbar + botones de flujo (Confirmar→…→Completar) operan.
- [ ] Smart buttons (Nº líneas, Margen %) y totales al pie correctos.
- [ ] Wizard *Presupuesto rápido* genera líneas y deja mensaje en chatter.
- [ ] **Regla:** usuario *User* NO acepta la no rentable (Taller RM); *Manager* SÍ.
- [ ] Cron "comprobar solicitudes vencidas" → **Ejecutar manualmente** crea actividad + mensaje.
- [ ] Panel *graph/pivot* cargan.

**Calidad**
- [ ] Tests OK: `--test-enable --test-tags=/service_quote_manager` → *0 failed, 0 error*.
- [ ] Dos usuarios preparados (uno *User*, uno *Manager*) para la demo de la regla.
- [ ] Filtro *Vencidas* devuelve lo esperado.

---

## Comandos exactos (resumen Docker)

```powershell
# 1) Arrancar Odoo 17
cd E:\ProyectosClaude\ProyectoODOO
docker compose up -d

# 2) Instalar el módulo (BD nueva con demo)
docker compose run --rm odoo odoo -d sqm_demo -i service_quote_manager --stop-after-init

# 3) Ejecutar los tests
docker compose run --rm odoo odoo -d sqm_test -i service_quote_manager --test-enable --test-tags=/service_quote_manager --stop-after-init
```
