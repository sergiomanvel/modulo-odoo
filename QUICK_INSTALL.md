# QUICK_INSTALL — Service Quote Manager (Odoo 17)

Guía rápida para instalar el addon **`service_quote_manager`** en una instancia
propia de **Odoo 17.0**.

> ⏱️ **Tiempo estimado de instalación: 5–10 minutos.**

---

## 1. Requisitos

- **Odoo 17.0** (Community o Enterprise) ya instalado y arrancable.
- **PostgreSQL** en marcha y configurado, con un rol que Odoo pueda usar
  (el usuario/clave de tu `odoo.conf`). El rol necesita permiso `CREATEDB`
  si quieres que Odoo cree la base de datos.
- Permisos de escritura sobre un directorio de **custom addons** y para
  **reiniciar** el servicio de Odoo.
- Dependencias del módulo: `base` y `mail` (incluidas en Odoo estándar).

---

## 2. Instalación rápida — Opción A · Desde GitHub

```bash
# 1. Clona el repositorio en tu directorio de addons personalizados
cd /ruta/a/tus/custom_addons
git clone https://github.com/sergiomanvel/modulo-odoo.git

# Resultado: /ruta/a/tus/custom_addons/modulo-odoo/service_quote_manager
```

El `addons_path` debe apuntar al **directorio que contiene** la carpeta
`service_quote_manager` (aquí: `.../custom_addons/modulo-odoo`).

> Alternativa: clona y copia solo la carpeta del módulo:
> ```bash
> git clone https://github.com/sergiomanvel/modulo-odoo.git /tmp/sqm
> cp -r /tmp/sqm/service_quote_manager /ruta/a/tus/custom_addons/
> ```

---

## 3. Instalación rápida — Opción B · Copiando la carpeta

Si tienes el ZIP de release o la carpeta suelta:

1. Descomprime `service_quote_manager_odoo17_v1.0.0.zip`.
2. Copia la carpeta **`service_quote_manager/`** dentro de tu directorio de
   addons, por ejemplo:
   ```
   .../odoo/custom_addons/service_quote_manager
   ```

> ⚠️ Copia la **carpeta `service_quote_manager`**, no su contenido suelto.
> El directorio de addons debe contener `service_quote_manager/__manifest__.py`.

---

## 4. Configurar `addons_path`

Edita tu `odoo.conf` y añade el **directorio padre** que contiene
`service_quote_manager` (separado por comas, sin espacios sobrantes):

```ini
[options]
addons_path = /ruta/odoo/addons,/ruta/odoo/custom_addons
```

> 🔑 **Regla de oro:** el `addons_path` apunta al directorio **padre**
> (`.../custom_addons`), **nunca** a la carpeta del módulo
> (`.../custom_addons/service_quote_manager`).

Ejemplo real en Windows:

```ini
addons_path = e:\odoo17\server\odoo\addons,e:\ruta\a\custom_addons
```

---

## 5. Reiniciar Odoo

**Linux (servicio):**
```bash
sudo systemctl restart odoo
```

**Windows (servicio):**
```bat
net stop odoo-server-17.0 && net start odoo-server-17.0
```

**Ejecución manual:**
```bash
./odoo-bin -c odoo.conf
```

---

## 6. Actualizar la lista de Apps

1. Inicia sesión como administrador.
2. Activa el **modo desarrollador**: *Ajustes → (abajo) Activar el modo de desarrollador*.
3. Ve a **Apps → (menú) Actualizar lista de aplicaciones → Actualizar**.

---

## 7. Buscar e instalar el módulo

1. En **Apps**, quita el filtro *"Aplicaciones"* si no lo ves.
2. Busca **`Service Quote Manager`**.
3. Pulsa **Activar / Instalar**.

Al terminar aparece el menú raíz **Service Quote Manager** con sus submenús
(Solicitudes, Tablero Kanban, Panel, Configuración).

### Alternativa por línea de comandos (instala en una BD concreta)

```bash
# Crea/usa la BD "sqm_demo" e instala el módulo
./odoo-bin -c odoo.conf -d sqm_demo -i service_quote_manager --stop-after-init
```

---

## 8. Cargar datos demo

Los datos demo crean **8 clientes + 8 solicitudes** en distintos estados y
márgenes (ideal para una demo de entrevista).

- **Desde la UI:** los datos demo se cargan si la **base de datos se creó con la
  opción *"Cargar datos de demostración"* activada** (pantalla *Gestor de bases
  de datos → Crear base de datos*). No se pueden añadir demo a una BD creada sin
  ellos.
- **Desde la CLI (BD nueva con demo):**
  ```bash
  ./odoo-bin -c odoo.conf -d sqm_demo -i service_quote_manager --stop-after-init
  # (si tu odoo.conf tiene without_demo=False, se cargan automáticamente)
  ```

Para una BD **sin** datos demo, usa `--without-demo=all` al crearla.

---

## 9. Ejecutar los tests

El módulo trae tests (`TransactionCase`, `post_install`): márgenes con valores
límite, flujo de estados, regla de aceptación de solicitudes no rentables y cron
de vencidas.

```bash
# Instalar y ejecutar solo los tests de este módulo
./odoo-bin -c odoo.conf -d sqm_demo -i service_quote_manager \
    --test-enable --test-tags=/service_quote_manager --stop-after-init

# Con el módulo ya instalado
./odoo-bin -c odoo.conf -d sqm_demo -u service_quote_manager \
    --test-enable --test-tags=/service_quote_manager --stop-after-init
```

Resultado esperado: **`0 failed, 0 error(s) of 14 tests`**.

> 🪟 **Windows + Git Bash:** un argumento que empieza por `/` (como
> `--test-tags=/service_quote_manager`) se convierte en ruta. Prefija el comando
> con `MSYS_NO_PATHCONV=1` o usa `cmd`/PowerShell.

---

## 10. Errores comunes y solución rápida

| Síntoma | Causa | Solución |
|---------|-------|----------|
| El módulo **no aparece** en Apps | `addons_path` mal o lista sin actualizar | Verifica que apunta al **directorio padre**; reinicia Odoo y **Actualiza lista de aplicaciones** (modo desarrollador). |
| `addons_path` apunta a la carpeta del módulo | Ruta demasiado profunda | Debe apuntar al padre: `.../custom_addons`, no `.../custom_addons/service_quote_manager`. |
| `FATAL: role "xxx" does not exist` | El usuario de `odoo.conf` no existe en PostgreSQL | Crea el rol: `CREATE ROLE openpg LOGIN CREATEDB PASSWORD 'openpgpwd';` (ajusta al `db_user`/`db_password` de tu conf). |
| `could not connect to server` | PostgreSQL parado o `db_host/db_port` erróneos | Arranca PostgreSQL y revisa `db_host`, `db_port` en `odoo.conf`. |
| No se ven los **datos demo** | La BD se creó sin datos de demostración | Recrea la BD activando *"Cargar datos de demostración"*, o instala con la CLI en una BD nueva. |
| `AttributeError: 'method_descriptor' object has no attribute 'today'` en datos XML | En el `eval` de los XML, `datetime` es la **clase** `datetime.datetime` | Usa `datetime.today()` y `timedelta(...)` (no `datetime.date.today()` ni `datetime.timedelta(...)`). *Ya corregido en este release.* |
| El usuario no ve el menú | Falta grupo de seguridad | *Ajustes → Usuarios →* asigna **Service Quote User** o **Service Quote Manager**. |
| Vistas con error `attrs`/`states` | Sintaxis antigua | Este módulo ya usa el estilo Odoo 17 (`invisible="..."`, `<tree>`). Asegúrate de estar en **17.0**. |

---

## 11. Verificación final (checklist)

- [ ] El módulo instala sin errores en una BD limpia.
- [ ] Aparece el menú **Service Quote Manager** con su icono.
- [ ] Con demo: se ven **8 solicitudes** en distintos estados.
- [ ] `--test-enable` → **0 failed, 0 error(s) of 14 tests**.

---

Más detalle funcional y técnico en:
- [`service_quote_manager/README.md`](service_quote_manager/README.md)
- [`service_quote_manager/TECHNICAL_NOTES.md`](service_quote_manager/TECHNICAL_NOTES.md)
