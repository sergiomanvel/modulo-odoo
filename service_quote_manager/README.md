# Service Quote Manager

Módulo de Odoo para gestionar **solicitudes técnicas de servicio** y sus
**presupuestos**, con control de **rentabilidad** integrado en el flujo de
estados. Pensado como caso de uso realista para una empresa de servicios
(instalaciones eléctricas), a partir del prototipo *Service Quote Manager*.

> **Versión objetivo:** Odoo **17.0** (Community o Enterprise).
> La sintaxis de vistas usa el estilo moderno de Odoo 17 (`invisible="..."`
> en lugar de `attrs`, `<tree>` para las listas).

### Documentación del módulo

| Documento | Contenido |
|-----------|-----------|
| `README.md` | Instalación, uso, checklist de pruebas y mejoras futuras (este archivo) |
| `DEMO_SCRIPT.md` | Guion de demo cronometrado para entrevista |
| `TECHNICAL_NOTES.md` | Arquitectura, decisiones de diseño y convenciones Odoo 17 |

---

## 1. Características

| Requisito | Implementación |
|-----------|----------------|
| Modelos Python + ORM | `service.request`, `service.quote.line`, `service.request.type`, `service.quote.template.line`, `quick.quote.wizard` |
| Relación con clientes | `partner_id` → `res.partner` (obligatorio) |
| Responsable interno | `user_id` → `res.users` |
| Grupos de seguridad | *Service Quote User* y *Service Quote Manager* |
| Acciones de ventana | Solicitudes, Panel, Tablero Kanban, Asistente de presupuesto, Tipos de servicio |
| Menús | Menú raíz **Service Quote Manager** con submenús |
| Cron | Comprobación diaria de solicitudes vencidas |
| Chatter + Actividades | `mail.thread` + `mail.activity.mixin` |
| Wizard | `quick.quote.wizard` (asistente de presupuesto rápido) |
| Datos demo | 8 clientes + 8 solicitudes en distintos estados y márgenes |
| Vistas | Lista, formulario con statusbar, kanban, búsqueda, gráfico, pivot, wizard modal, smart buttons, notebook |

### Reglas de negocio de rentabilidad

El margen se calcula como `(precio_total − coste_total) / precio_total`:

| Categoría | Condición |
|-----------|-----------|
| **Saludable** | margen ≥ 30 % |
| **Ajustado** | 20 % ≤ margen < 30 % |
| **Bajo** | margen < 20 % |
| **Crítico** | margen < 10 % |
| **No rentable** | precio total < coste total |

> **Regla clave:** una solicitud **No rentable** no puede pasar a estado
> **Aceptado** salvo que el usuario pertenezca al grupo **Service Quote Manager**
> (ver `ServiceRequest.action_accept`).

### Flujo de estados

```
Borrador → Pendiente → Presupuestado → Aceptado → En curso → Completado
   └──────────────── Cancelar (casi cualquier estado) ────────────────┘
```

---

## 2. Estructura del módulo

```
service_quote_manager/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── service_quote_line.py       # Líneas de presupuesto + constantes compartidas
│   ├── service_request_type.py     # Tipos de servicio + líneas de plantilla
│   └── service_request.py          # Modelo principal (chatter, cron, reglas)
├── wizard/
│   ├── __init__.py
│   ├── quick_quote_wizard.py       # Asistente de presupuesto rápido
│   └── quick_quote_wizard_views.xml
├── views/
│   ├── service_request_type_views.xml
│   ├── service_quote_line_views.xml
│   ├── service_request_views.xml   # tree/form/kanban/search/graph/pivot + acciones
│   └── menu_views.xml
├── security/
│   ├── security.xml                # categoría, grupos, regla multi-compañía
│   └── ir.model.access.csv
├── data/
│   ├── service_request_data.xml    # secuencia SR- + tipos de servicio con plantillas
│   ├── cron.xml                    # ir.cron diario
│   └── demo_data.xml               # datos de demostración
├── tests/
│   ├── __init__.py
│   └── test_service_request.py     # márgenes, flujo, regla de aceptación, cron
├── static/description/icon.png
├── DEMO_SCRIPT.md
├── TECHNICAL_NOTES.md
└── README.md
```

---

## 3. Instalación en Odoo

### Opción A · Servidor Odoo local

1. Copia la carpeta `service_quote_manager` dentro de una ruta de *addons*, p. ej.:
   ```
   .../odoo/custom_addons/service_quote_manager
   ```
2. Asegúrate de que esa ruta está en el `addons_path` del fichero de
   configuración (`odoo.conf`):
   ```ini
   addons_path = /ruta/odoo/addons,/ruta/odoo/custom_addons
   ```
3. Reinicia el servicio de Odoo:
   ```bash
   ./odoo-bin -c odoo.conf -u service_quote_manager -d NOMBRE_BD
   ```
   (o simplemente reinícialo y actualiza la lista de aplicaciones desde la UI).
4. En la interfaz web:
   - Activa el **modo desarrollador** (*Ajustes → Activar el modo de desarrollador*).
   - Ve a **Apps → Actualizar lista de aplicaciones**.
   - Busca **"Service Quote Manager"** y pulsa **Instalar**.
   - Para cargar los **datos demo**, instala en una base de datos creada con la
     opción *"cargar datos de demostración"* activada.

### Opción B · Docker

```bash
# Monta el módulo como volumen en la ruta de addons del contenedor
-v E:/ProyectosClaude/ProyectoODOO/service_quote_manager:/mnt/extra-addons/service_quote_manager
```
Luego actualiza la lista de apps e instálalo desde la interfaz.

### Asignar permisos

*Ajustes → Usuarios y compañías → Usuarios →* selecciona un usuario *→*
sección **Service Quote Manager** *→* elige **Service Quote User** o
**Service Quote Manager**. El administrador ya pertenece al grupo *Manager*.

---

## 4. Guion de demo (para entrevista)

Duración aproximada: **8–10 minutos**.

1. **Presentación (30 s)**
   > "Partí de un prototipo de diseño y lo convertí en un módulo Odoo real:
   > modelos, ORM, vistas nativas, seguridad, wizard, cron y chatter."

2. **Menú y Kanban (1 min)**
   Abre **Service Quote Manager → Tablero Kanban**. Muestra las tarjetas
   agrupadas por estado, con la **etiqueta de margen** (saludable/ajustado/
   bajo/no rentable) y la marca **Vencida** en rojo.

3. **Lista y filtros (1 min)**
   Ve a **Solicitudes**. Enseña la vista lista con decoraciones (vencidas en
   rojo), el buscador y filtros: *Abiertas*, *Vencidas*, *No rentables*,
   *Margen saludable*, y agrupaciones por estado / cliente / margen.

4. **Formulario + statusbar (2 min)**
   Abre `SR-0000x · Restaurante La Brasa` (margen bajo). Muestra:
   - La **statusbar** y los botones de flujo (Confirmar → Presupuestar → …).
   - Los **smart buttons** (Nº de líneas y Margen %).
   - El **notebook**: *Líneas de presupuesto* (con totales al pie), *Cliente*
     y *Notas*.
   - El **chatter** con el historial y las actividades.

5. **Asistente de presupuesto rápido (2 min)**
   Abre la solicitud en borrador `Juan Pérez` (sin líneas). Pulsa
   **Presupuesto rápido**, elige la plantilla *"Tomas y puntos de luz"*, revisa
   el **preview de coste/precio/margen** y pulsa **Aplicar al presupuesto**.
   Las líneas se generan automáticamente y se registra un mensaje en el chatter.

6. **Regla de negocio de rentabilidad (1.5 min)**
   Abre `Taller Mecánico RM` (**No rentable**, precio < coste). Intenta
   **Aceptar** con un usuario del grupo *User* → salta un error. Con un usuario
   *Manager* la aceptación se permite. *(Explica el porqué de la regla.)*

7. **Cron + Actividades (1 min)**
   *Ajustes → Técnico → Automatización → Acciones planificadas →*
   "Service Quote: comprobar solicitudes vencidas". Ejecútalo con **Ejecutar
   manualmente** y muestra que la solicitud vencida (`Gimnasio FitZone`) recibe
   una **actividad** y un mensaje en el chatter.

8. **Panel analítico (30 s)**
   Abre **Panel** → gráfico y tabla dinámica de rentabilidad por tipo de
   servicio.

---

## 5. Checklist de pruebas

### Instalación / carga
- [ ] El módulo instala sin errores en una BD limpia.
- [ ] Instala con datos demo y aparecen 8 solicitudes.
- [ ] El menú **Service Quote Manager** aparece con su icono.

### Modelos y cálculos
- [ ] Al crear una solicitud, `name` toma el valor de secuencia `SR-0000x`.
- [ ] `total_cost`, `total_price`, `margin_amount` y `margin_percent` se
      recalculan al editar líneas.
- [ ] La categoría de margen coincide con las reglas (probar valores límite:
      9.9 %, 10 %, 19.9 %, 20 %, 29.9 %, 30 %, y precio < coste).
- [ ] Los subtotales de línea = cantidad × coste/precio.

### Flujo de estados
- [ ] Los botones de la statusbar cambian el estado en el orden esperado.
- [ ] No se puede **Presupuestar** una solicitud sin líneas.
- [ ] **Restablecer a borrador** funciona desde cualquier estado.

### Regla de rentabilidad
- [ ] Usuario *User* NO puede aceptar una solicitud no rentable (UserError).
- [ ] Usuario *Manager* SÍ puede aceptarla.
- [ ] Una solicitud rentable se acepta con cualquier usuario del módulo.

### Wizard
- [ ] Abierto desde la solicitud, `request_id` viene precargado y bloqueado.
- [ ] El preview de coste/precio/margen se actualiza al cambiar la plantilla.
- [ ] Modo *Añadir* conserva las líneas existentes; modo *Reemplazar* las borra.
- [ ] Tras aplicar, se registra un mensaje en el chatter.

### Seguridad
- [ ] Un usuario sin grupos del módulo no ve el menú.
- [ ] Usuario *User* no puede borrar solicitudes ni editar tipos de servicio.
- [ ] Usuario *Manager* accede a **Configuración → Tipos de servicio**.

### Cron / vencidas
- [ ] Ejecutando el cron manualmente, `is_overdue` se marca en las vencidas.
- [ ] Se crea una actividad para el responsable y un mensaje en el chatter.
- [ ] No se duplican notificaciones en ejecuciones sucesivas (`overdue_notified`).
- [ ] El filtro *Vencidas* de la búsqueda devuelve las mismas solicitudes.

### Vistas
- [ ] Kanban, lista, formulario, búsqueda, gráfico y pivot cargan sin error.
- [ ] Las decoraciones de color reflejan estado / margen / vencimiento.

---

## 5b. Ejecutar los tests

El módulo incluye tests en `tests/` (`TransactionCase`, etiquetados
`post_install`). Cubren el cálculo de márgenes (con valores límite), el flujo de
estados, la regla de aceptación de solicitudes no rentables y el cron de
vencidas.

```bash
# Instalar y ejecutar los tests
odoo-bin -d NOMBRE_BD -i service_quote_manager --test-enable --stop-after-init

# Con el módulo ya instalado
odoo-bin -d NOMBRE_BD -u service_quote_manager --test-enable --stop-after-init

# Solo los tests de este módulo
odoo-bin -d NOMBRE_BD -u service_quote_manager --test-enable \
         --test-tags=/service_quote_manager --stop-after-init
```

> Nota: algunos tests usan los datos base del módulo (tipos de servicio), que se
> cargan siempre; no dependen de los datos *demo*.

---

## 6. Posibles mejoras futuras

- **Generar Presupuesto/Factura de venta** (`sale.order`, `account.move`) a
  partir de la solicitud aceptada, mapeando las líneas y márgenes.
- **Productos reales** (`product.product`) en las líneas, con coste/precio
  desde la ficha de producto y unidades de medida.
- **Informe PDF** del presupuesto (QWeb report) con la marca de la empresa.
- **Portal del cliente** para que apruebe/rechace el presupuesto online.
- **SLA / plazos** configurables por tipo de servicio y prioridad, con
  escalados automáticos.
- **Panel OWL** nativo (tipo *spreadsheet dashboard*) con KPIs de rentabilidad.
- **Multi-moneda** por cliente y conversión automática.
- **Tests unitarios** (`tests/`) para el cálculo de márgenes y la regla de
  aceptación.
- **Integración con Field Service / Proyecto** para planificar la ejecución.
- **Reglas de registro por responsable** (que cada técnico vea solo lo suyo,
  configurable).

---

## 7. Notas técnicas

- El campo `margin_percent` se almacena como número (0–100) con agregación
  `avg` para gráficos y tablas dinámicas.
- `is_overdue` es un campo calculado y almacenado (depende de `date_deadline`
  y `state`); el cron lo **recalcula a diario** para cubrir el cambio de día,
  ya que un `compute` basado en "hoy" no se dispara solo con el paso del tiempo.
- Las constantes de tipos de línea (`LINE_TYPES`) se definen una sola vez en
  `models/service_quote_line.py` y se reutilizan en las plantillas.
- La regla de rentabilidad vive en `action_accept` para poder aplicarla en
  cualquier vía (UI, importación, API).
