# Notas técnicas — Service Quote Manager

Documento de arquitectura y decisiones de diseño. Complementa al `README.md`
(instalación/uso).

> **Versión objetivo:** Odoo **17.0**. El código sigue las convenciones de v17
> (ver §6).

---

## 1. Modelo de dominio

```
res.partner ──< service.request >── res.users
                     │  (mail.thread, mail.activity.mixin)
                     │
                     ├──< service.quote.line        (líneas reales del presupuesto)
                     │
                     └── service.request.type ──< service.quote.template.line
                                                    (plantillas reutilizables)

quick.quote.wizard (TransientModel) ──> genera service.quote.line desde una plantilla
```

| Modelo | Tipo | Rol |
|--------|------|-----|
| `service.request` | Model | Solicitud técnica; núcleo del flujo y de la rentabilidad |
| `service.quote.line` | Model | Línea de presupuesto (material/mano de obra/desplazamiento/extra) |
| `service.request.type` | Model | Tipo de servicio configurable con su plantilla |
| `service.quote.template.line` | Model | Línea de plantilla asociada a un tipo |
| `quick.quote.wizard` | TransientModel | Asistente de presupuesto rápido |

---

## 2. Cálculo de rentabilidad

Todo se calcula con campos **computados y almacenados** (`store=True`) para
poder filtrar, ordenar, agrupar y analizar (graph/pivot):

- `service.quote.line`: `subtotal_cost = quantity * unit_cost`,
  `subtotal_price = quantity * unit_price`, `margin = subtotal_price − subtotal_cost`.
- `service.request` (`_compute_totals`, depende de
  `quote_line_ids.subtotal_cost/subtotal_price`):
  - `total_cost`, `total_price`, `margin_amount = total_price − total_cost`.
  - `margin_percent = margin_amount / total_price * 100` (0 si `total_price` = 0).
  - `margin_category` vía el método puro `_get_margin_category(cost, price, pct)`.

### Reglas de categoría (orden de evaluación importa)

```python
if not total_cost and not total_price:  return False          # sin datos
if total_price < total_cost:            return 'unprofitable'  # No rentable
if margin_percent < 10:                 return 'critical'      # Crítico
if margin_percent < 20:                 return 'low'           # Bajo
if margin_percent < 30:                 return 'tight'         # Ajustado
return 'healthy'                                               # Saludable (>=30)
```

`_get_margin_category` es **estático y puro**: no toca la base de datos, lo que
lo hace trivial de testear con valores límite (ver `tests/`).

`margin_percent` se guarda como número 0–100 con `group_operator="avg"` para que
las agregaciones en gráficos/pivot tengan sentido (media, no suma).

---

## 3. Flujo de estados y regla de aceptación

```
draft → pending → quoted → accepted → in_progress → done
  └───────────────── cancelled ─────────────────┘
```

- Cada transición es un método (`action_confirm`, `action_quote`, …) que hace
  `write({'state': ...})`. Los botones del formulario llaman a estos métodos.
- La **statusbar no es clicable** (comportamiento por defecto en v17): se fuerza
  el paso por los botones para poder validar.
- `action_quote` exige que existan líneas.
- **Regla de negocio central** (`action_accept`):

  ```python
  if req.margin_category == 'unprofitable' and not user.has_group(
          'service_quote_manager.group_service_quote_manager'):
      raise UserError(...)
  ```

  Se implementa en el **método**, no en la vista, para que aplique en cualquier
  canal (UI, `load`, RPC/API). Ocultar el botón sería solo cosmético.

---

## 4. Solicitudes vencidas: campo calculado + cron

`is_overdue` es **computado y almacenado** (`_compute_is_overdue`, depende de
`date_deadline` y `state`): da feedback inmediato en lista/kanban y permite
decorar y (indirectamente) filtrar.

**Problema:** un `compute` basado en "hoy" no se recalcula solo con el paso del
tiempo (sus dependencias no cambian de un día a otro).

**Solución:** el cron diario `_cron_check_overdue_requests`:

1. Recalcula `is_overdue` en las solicitudes abiertas (cubre el cambio de día).
2. Notifica (chatter + `activity_schedule`) las recién vencidas.
3. Evita duplicados con el flag `overdue_notified`, que se **reinicia** cuando la
   solicitud deja de estar vencida.

El filtro *Vencidas* de la vista de búsqueda usa `context_today()` en el dominio,
así que es correcto con independencia de cuándo corrió el cron por última vez.

---

## 5. Seguridad

- **Grupos** (`security/security.xml`): `group_service_quote_user` y
  `group_service_quote_manager`. El *Manager* implica al *User* (`implied_ids`).
- **Categoría** propia (`ir.module.category`) para que aparezcan agrupados en
  *Ajustes → Usuarios*.
- **ACL** (`ir.model.access.csv`):
  - *User*: crear/leer/editar solicitudes y líneas; **no** borrar solicitudes;
    solo lectura de tipos de servicio.
  - *Manager*: control total, incluida la configuración de tipos.
- **Regla de registro** multi-compañía sobre `service.request`.
- La regla de rentabilidad se apoya en `has_group(...manager)`.

---

## 6. Convenciones de Odoo 17 aplicadas

Revisado contra el skill `odoo-17`. Puntos clave (y qué se evita de v18/19):

| Concepto | Aquí (v17) | Evitado (v18+) |
|----------|------------|----------------|
| Vista lista | `<tree>` | `<list>` |
| Modificadores | `invisible="state == 'done'"` (expresión directa) | `attrs=` / `states=` (el validador de v17 los rechaza) |
| Agregación de campo | `group_operator="avg"` | `aggregator=` |
| `create` en lote | `@api.model_create_multi` | — |
| Plantilla kanban | `t-name="kanban-box"` | `t-name="card"` |
| Chatter | `<div class="oe_chatter">…</div>` | `<chatter/>` |
| Grupos | `category_id` en `res.groups` | `privilege_id` |
| Restricciones SQL | `_sql_constraints` (no se usa aquí) | `models.Constraint(...)` |

Otras buenas prácticas:
- Sin `search()` ni `create()` dentro de bucles (se usan comandos x2many y
  `mapped`).
- Cadenas de usuario marcadas con `_()` para i18n.
- Constantes compartidas (`LINE_TYPES`) definidas una sola vez.

---

## 7. Datos y demo

- `data/service_request_data.xml` (datos **reales**): secuencia `SR-` y los 5
  tipos de servicio con sus plantillas. Los tipos NO son `noupdate` para poder
  ajustarlos en actualizaciones; la secuencia sí (`noupdate="1"`).
- `data/demo_data.xml` (`noupdate="1"`): 8 clientes y 8 solicitudes que cubren
  todos los estados y **todas** las categorías de margen (incluida una no
  rentable y una vencida), para que la demo sea inmediata.
- Las fechas demo son **relativas a hoy** (`datetime.date.today()`), así la demo
  siempre tiene una solicitud recién vencida.

---

## 8. Tests

`tests/test_service_request.py` (`TransactionCase`, `@tagged('post_install',
'-at_install')`):

- Asignación de secuencia al crear.
- Cálculo de subtotales y totales.
- Reglas de `margin_category` con **valores límite** (9.99/10/19.99/20/29.99/30
  y precio < coste) sobre el método puro.
- Flujo completo de estados y bloqueo de *Presupuestar* sin líneas.
- Regla de aceptación: *User* bloqueado, *Manager* permitido, rentable permitido
  para todos (usando `new_test_user` y `with_user`).
- Wizard: modos *Añadir* y *Reemplazar*, y preview.
- `Form` para validar el `onchange` de prioridad por tipo.
- Cron: marca/notifica vencidas y reinicia el flag al dejar de estarlo.

**Ejecutar:**

```bash
odoo-bin -d NOMBRE_BD -i service_quote_manager --test-enable --stop-after-init
# o, ya instalado:
odoo-bin -d NOMBRE_BD -u service_quote_manager --test-enable --stop-after-init
# solo este módulo:
odoo-bin -d NOMBRE_BD -u service_quote_manager --test-enable \
         --test-tags=/service_quote_manager --stop-after-init
```

---

## 9. Decisiones deliberadas / límites conocidos

- **Sin integración con ventas/facturación** por alcance; el diseño lo permite
  (ver *Mejoras futuras* del README).
- **Líneas con coste/precio libres** (no `product.product`) para mantener el foco
  en la rentabilidad; migrar a productos es una mejora natural.
- `margin_percent` como 0–100 (no fracción 0–1): más legible en UI; por eso no se
  usa el widget `percentage` (que espera fracción).
- Prioridad como `Selection` 0–3 con `widget="priority"` (estrellas) para un
  toque nativo; el mapeo es Baja/Media/Alta/Urgente.
