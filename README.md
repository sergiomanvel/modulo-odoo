# ProyectoODOO — Service Quote Manager

Addon **real y funcional para Odoo 17.0** que gestiona **solicitudes técnicas de
servicio** y sus **presupuestos**, con **control de rentabilidad** (margen)
integrado en el flujo de estados.

> Caso de uso: una empresa de servicios (p. ej. instalaciones eléctricas) que
> necesita presupuestar trabajos, controlar el margen y decidir qué solicitudes
> acepta en función de su rentabilidad.

El código del addon vive en la carpeta [`service_quote_manager/`](service_quote_manager/).

---

## ¿Qué es esto?

No es un prototipo ni una maqueta: es un **módulo de Odoo 17 instalable**, con
modelos Python sobre el ORM, vistas nativas, seguridad por grupos, wizard, cron,
chatter y tests automatizados.

## ¿Qué problema resuelve?

Muchas empresas de servicios presupuestan en hojas de cálculo sueltas, sin
visibilidad del margen ni control de qué trabajos conviene aceptar. Este módulo:

- Centraliza **solicitudes de servicio** con cliente, responsable y prioridad.
- Calcula automáticamente **coste, precio, beneficio y margen %** a partir de las
  líneas de presupuesto.
- **Clasifica la rentabilidad** (Saludable / Ajustado / Bajo / Crítico / No
  rentable) y **bloquea aceptar trabajos no rentables** salvo a un responsable
  autorizado.
- Avisa de **solicitudes vencidas** mediante un cron diario y actividades.

## Funcionalidades principales

- **Modelos:** `service.request`, `service.quote.line`, `service.request.type`,
  `quick.quote.wizard` (asistente de presupuesto rápido).
- **Cálculo de rentabilidad** con categorías de margen y regla de negocio de
  aceptación.
- **Flujo de estados** con statusbar: Borrador → Pendiente → Presupuestado →
  Aceptado → En curso → Completado (+ Cancelar).
- **Vistas nativas:** lista, formulario con smart buttons, kanban, búsqueda,
  gráfico y tabla dinámica.
- **Seguridad:** grupos *Service Quote User* y *Service Quote Manager*.
- **Cron** de solicitudes vencidas + **chatter** y actividades (`mail`).
- **Datos demo:** 8 clientes y 8 solicitudes en distintos estados y márgenes.
- **Tests** automatizados (`post_install`).

---

## Instalación rápida

```bash
# 1. Clona en tu directorio de custom addons
git clone https://github.com/sergiomanvel/modulo-odoo.git

# 2. Añade el directorio padre al addons_path de odoo.conf
#    addons_path = /ruta/odoo/addons,/ruta/a/modulo-odoo

# 3. Reinicia Odoo, actualiza la lista de Apps e instala "Service Quote Manager"
./odoo-bin -c odoo.conf -d sqm_demo -i service_quote_manager --stop-after-init
```

📖 **Guía paso a paso (5–10 min):** [`QUICK_INSTALL.md`](QUICK_INSTALL.md)

También disponible como paquete listo para copiar:
`release/service_quote_manager_odoo17_v1.0.0.zip` (solo la carpeta del módulo).

---

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [`QUICK_INSTALL.md`](QUICK_INSTALL.md) | Instalación rápida install-ready para Odoo 17 |
| [`service_quote_manager/README.md`](service_quote_manager/README.md) | Funcionalidad, uso, checklist de pruebas y mejoras futuras |
| [`service_quote_manager/TECHNICAL_NOTES.md`](service_quote_manager/TECHNICAL_NOTES.md) | Arquitectura y decisiones de diseño (Odoo 17) |

---

## Estado del proyecto

- ✅ **Validado en runtime sobre Odoo 17.0:** instala en BD limpia, carga datos
  demo (8 solicitudes) y **pasa los tests** (`0 failed, 0 error(s) of 14 tests`).
- ✅ **Validado estáticamente:** sintaxis de vistas moderna de Odoo 17
  (`invisible="..."`, `<tree>`), sin dependencias externas más allá de
  `base` y `mail`.
- 🎯 **Objetivo:** paquete *install-ready* para que un evaluador lo despliegue en
  su propia instancia de Odoo 17 en pocos minutos.

---

## Licencia

LGPL-3. Ver [`LICENSE`](LICENSE).
