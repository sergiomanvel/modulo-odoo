# -*- coding: utf-8 -*-
{
    "name": "Service Quote Manager",
    "version": "17.0.1.0.0",
    "category": "Services/Field Service",
    "summary": "Gestión de solicitudes técnicas y presupuestos con control de rentabilidad",
    "description": """
Service Quote Manager
=====================

Módulo empresarial para gestionar solicitudes técnicas de servicio y sus
presupuestos, con control de rentabilidad (margen) integrado en el flujo de
estados.

Funcionalidades principales
---------------------------
* Solicitudes de servicio (``service.request``) asociadas a un cliente
  (``res.partner``) y a un responsable interno (``res.users``).
* Líneas de presupuesto (``service.quote.line``) por tipo: material, mano de
  obra, desplazamiento y extra.
* Cálculo automático de coste total, precio total, beneficio y margen %.
* Categorización del margen: Saludable (>=30%), Ajustado (20-29%),
  Bajo (<20%), Crítico (<10%) y No rentable (precio < coste).
* Regla de negocio: una solicitud no rentable no puede aceptarse salvo por un
  usuario del grupo *Service Quote Manager*.
* Asistente de presupuesto rápido (``quick.quote.wizard``) que genera líneas
  a partir de plantillas por tipo de servicio.
* Tipos de servicio configurables (``service.request.type``) con plantillas.
* Chatter y actividades (mail.thread / mail.activity.mixin).
* Cron diario que detecta solicitudes vencidas y notifica al responsable.
* Vistas nativas: lista, formulario con statusbar, kanban, búsqueda, gráfico
  y tabla dinámica.
* Seguridad con dos grupos: *Service Quote User* y *Service Quote Manager*.
""",
    "author": "Sergio",
    "website": "https://www.example.com",
    "license": "LGPL-3",
    "depends": ["base", "mail"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/service_request_data.xml",
        "data/cron.xml",
        "views/service_request_type_views.xml",
        "views/service_quote_line_views.xml",
        "views/service_request_views.xml",
        "wizard/quick_quote_wizard_views.xml",
        "views/menu_views.xml",
    ],
    "demo": [
        "data/demo_data.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
}
