# Guion de demo — Service Quote Manager

Guion pensado para una **entrevista técnica** (8–12 min). Cada bloque incluye
qué hacer, qué decir y el resultado esperado. Los datos demo ya están cargados
si instalaste el módulo en una BD con datos de demostración.

---

## 0 · Preparación (antes de empezar)

- BD con el módulo instalado **con datos demo**.
- Ten a mano dos usuarios: uno del grupo *Service Quote User* y otro
  *Service Quote Manager* (el admin ya es Manager).
- Abre el menú **Service Quote Manager**.

**Frase de apertura (30 s):**
> "Partí de un prototipo de diseño (*Service Quote Manager*) y lo convertí en un
> módulo Odoo real. No reutilicé el HTML: reconstruí la lógica con modelos
> Python, ORM, vistas nativas, seguridad, un wizard, un cron y chatter. La idea
> de negocio es gestionar solicitudes técnicas y sus presupuestos controlando la
> **rentabilidad** de cada trabajo."

---

## 1 · Tablero Kanban (1 min)

**Hacer:** *Service Quote Manager → Tablero Kanban*.

**Decir:**
> "Las tarjetas se agrupan por estado. Cada tarjeta muestra el cliente, la
> referencia, el tipo de servicio y una **etiqueta de margen** con código de
> color: verde saludable, azul ajustado, ámbar bajo, rojo crítico/no rentable.
> Las vencidas se marcan en rojo."

**Esperado:** columnas por estado (Borrador → … → Cancelado), badges de margen,
`Gimnasio FitZone` con marca *Vencida*.

---

## 2 · Lista + filtros (1 min)

**Hacer:** *Solicitudes*. Muestra el buscador y aplica filtros: *Abiertas*,
*Vencidas*, *No rentables*, *Margen saludable*. Agrupa por *Categoría de margen*.

**Decir:**
> "El filtro *Vencidas* usa `context_today()` en el dominio, así que es correcto
> cualquier día sin depender del cron. Puedo agrupar por estado, cliente,
> responsable o categoría de margen."

**Esperado:** filas con decoración roja para vencidas; agrupaciones dinámicas.

---

## 3 · Formulario + statusbar + smart buttons (2 min)

**Hacer:** abre `Restaurante La Brasa` (margen bajo, ~14 %).

**Señalar:**
- **Statusbar** arriba y **botones de flujo** (Confirmar → Presupuestar →
  Aceptar → Iniciar → Completar).
- **Smart buttons**: *Nº de líneas* y *Margen %*.
- **Notebook**: *Líneas de presupuesto* con totales al pie (coste, precio,
  beneficio, margen), *Cliente* y *Notas*.
- **Chatter** con seguimiento y actividades.

**Decir:**
> "Coste, precio, beneficio, margen % y la categoría son **campos calculados y
> almacenados** que se recalculan al editar cualquier línea. Los estados no se
> cambian pinchando la statusbar sino con los botones, para poder aplicar reglas
> de negocio en el `write`."

---

## 4 · Asistente de presupuesto rápido (2 min)

**Hacer:** abre la solicitud en borrador de `Juan Pérez` (sin líneas). Pulsa
**Presupuesto rápido**. Elige la plantilla *"Tomas y puntos de luz"*.

**Señalar:** el **preview** de coste / precio / beneficio / margen y la tabla de
líneas de la plantilla. Elige modo *Añadir* y pulsa **Aplicar al presupuesto**.

**Decir:**
> "El wizard es un `TransientModel`. Las plantillas viven en los *tipos de
> servicio*, así que son **configurables** sin tocar código. Al aplicar, genera
> las líneas reales y deja traza en el chatter. Tiene modo *Añadir* y
> *Reemplazar*."

**Esperado:** las 3 líneas de la plantilla aparecen en la solicitud; nuevo
mensaje en el chatter.

---

## 5 · Regla de rentabilidad (1.5 min) — el momento clave

**Hacer:** abre `Taller Mecánico RM` (**No rentable**: precio < coste).

1. Con un usuario del grupo *Service Quote User*, pulsa **Aceptar** →
   aparece un `UserError` que lo impide.
2. Repite con un usuario *Service Quote Manager* → la aceptación se permite.

**Decir:**
> "La regla dice que una solicitud no rentable no puede pasar a *Aceptado* salvo
> que el usuario sea Manager. La implementé en `action_accept`, no en la vista,
> para que se cumpla por cualquier vía: UI, importación o API. Además hay un
> **ribbon** rojo *No rentable* en el formulario."

---

## 6 · Cron de vencidas + actividades (1 min)

**Hacer:** *Ajustes → Técnico → Automatización → Acciones planificadas →*
"Service Quote: comprobar solicitudes vencidas" → **Ejecutar manualmente**.
Vuelve a `Gimnasio FitZone`.

**Decir:**
> "El cron corre a diario. Marca las vencidas, crea una **actividad** para el
> responsable y escribe en el chatter, sin duplicar avisos gracias a una marca
> interna. Recalcula `is_overdue` cada día porque un `compute` basado en *hoy*
> no se dispara solo con el paso del tiempo."

**Esperado:** actividad *"Solicitud vencida"* asignada al responsable + mensaje.

---

## 7 · Panel analítico (30 s)

**Hacer:** *Panel* → gráfico de barras y **tabla dinámica** por tipo de servicio.

**Decir:**
> "Reutilizo el mismo modelo con vistas `graph` y `pivot` para analizar precio y
> beneficio por tipo de servicio y estado."

---

## 8 · Cierre técnico (30 s)

> "Resumiendo: modelos + ORM, cinco vistas nativas, dos grupos de seguridad con
> ACL y regla multi-compañía, wizard, cron, chatter/actividades, datos demo y
> **tests** que cubren el cálculo de márgenes, el flujo de estados, la regla de
> aceptación y el cron. Está escrito siguiendo las convenciones de Odoo 17."

---

## Preguntas típicas y respuestas rápidas

- **¿Por qué la regla en el método y no en la vista?** Para que se aplique en
  cualquier canal (UI, API, import), no solo ocultando un botón.
- **¿Por qué `is_overdue` almacenado y además cron?** El almacenado da feedback
  inmediato y permite filtrar/decorar; el cron cubre el cambio de día y notifica.
- **¿Cómo evitas notificaciones duplicadas?** Con el flag `overdue_notified`, que
  se reinicia cuando la solicitud deja de estar vencida.
- **¿Cómo escalarías a facturación?** Generando `sale.order`/`account.move`
  desde la solicitud aceptada (ver *Mejoras futuras* en el README).
