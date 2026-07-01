# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError

STATE_SELECTION = [
    ("draft", "Borrador"),
    ("pending", "Pendiente"),
    ("quoted", "Presupuestado"),
    ("accepted", "Aceptado"),
    ("in_progress", "En curso"),
    ("done", "Completado"),
    ("cancelled", "Cancelado"),
]

PRIORITY_SELECTION = [
    ("0", "Baja"),
    ("1", "Media"),
    ("2", "Alta"),
    ("3", "Urgente"),
]

MARGIN_SELECTION = [
    ("healthy", "Saludable"),
    ("tight", "Ajustado"),
    ("low", "Bajo"),
    ("critical", "Crítico"),
    ("unprofitable", "No rentable"),
]

# Estados en los que una solicitud sigue "abierta" y su fecha límite es relevante.
OPEN_STATES = ("draft", "pending", "quoted")


class ServiceRequest(models.Model):
    _name = "service.request"
    _description = "Solicitud de servicio"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, date_request desc, id desc"
    _rec_name = "name"

    name = fields.Char(
        string="Referencia",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("Nuevo"),
        tracking=True,
    )
    title = fields.Char(
        string="Título del servicio",
        required=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)

    partner_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        required=True,
        tracking=True,
        index=True,
    )
    partner_phone = fields.Char(related="partner_id.phone", string="Teléfono", readonly=True)
    partner_email = fields.Char(related="partner_id.email", string="Email", readonly=True)

    user_id = fields.Many2one(
        "res.users",
        string="Responsable",
        default=lambda self: self.env.user,
        tracking=True,
        index=True,
    )
    type_id = fields.Many2one(
        "service.request.type",
        string="Tipo de servicio",
        tracking=True,
    )
    priority = fields.Selection(
        PRIORITY_SELECTION,
        string="Prioridad",
        default="1",
        tracking=True,
    )
    state = fields.Selection(
        STATE_SELECTION,
        string="Estado",
        default="draft",
        required=True,
        tracking=True,
        group_expand="_group_expand_states",
    )

    date_request = fields.Date(
        string="Fecha de solicitud",
        default=fields.Date.context_today,
        tracking=True,
    )
    date_deadline = fields.Date(string="Fecha límite", tracking=True)
    date_accepted = fields.Date(string="Fecha de aceptación", readonly=True, copy=False)
    date_done = fields.Date(string="Fecha de finalización", readonly=True, copy=False)

    description = fields.Html(string="Descripción del trabajo")
    internal_note = fields.Text(string="Notas internas")

    quote_line_ids = fields.One2many(
        "service.quote.line",
        "request_id",
        string="Líneas de presupuesto",
        copy=True,
    )
    quote_line_count = fields.Integer(
        string="Nº de líneas",
        compute="_compute_quote_line_count",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
        required=True,
    )

    total_cost = fields.Monetary(
        string="Coste total",
        compute="_compute_totals",
        store=True,
        tracking=True,
        currency_field="currency_id",
    )
    total_price = fields.Monetary(
        string="Precio total",
        compute="_compute_totals",
        store=True,
        tracking=True,
        currency_field="currency_id",
    )
    margin_amount = fields.Monetary(
        string="Beneficio bruto",
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )
    margin_percent = fields.Float(
        string="Margen %",
        compute="_compute_totals",
        store=True,
        digits=(16, 2),
        tracking=True,
        group_operator="avg",
    )
    margin_category = fields.Selection(
        MARGIN_SELECTION,
        string="Categoría de margen",
        compute="_compute_totals",
        store=True,
        tracking=True,
    )

    is_overdue = fields.Boolean(
        string="Vencida",
        compute="_compute_is_overdue",
        store=True,
    )
    # Marca interna para no notificar la misma solicitud vencida en cada ejecución del cron.
    overdue_notified = fields.Boolean(
        string="Vencimiento notificado",
        default=False,
        copy=False,
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    def _compute_quote_line_count(self):
        for req in self:
            req.quote_line_count = len(req.quote_line_ids)

    @api.depends("quote_line_ids.subtotal_cost", "quote_line_ids.subtotal_price")
    def _compute_totals(self):
        for req in self:
            total_cost = sum(req.quote_line_ids.mapped("subtotal_cost"))
            total_price = sum(req.quote_line_ids.mapped("subtotal_price"))
            margin_amount = total_price - total_cost
            margin_percent = (margin_amount / total_price * 100.0) if total_price else 0.0

            req.total_cost = total_cost
            req.total_price = total_price
            req.margin_amount = margin_amount
            req.margin_percent = margin_percent
            req.margin_category = self._get_margin_category(total_cost, total_price, margin_percent)

    @staticmethod
    def _get_margin_category(total_cost, total_price, margin_percent):
        """Clasifica el margen según las reglas de negocio.

        * No rentable : precio total < coste total.
        * Crítico     : margen < 10%.
        * Bajo        : margen < 20%.
        * Ajustado    : 20% <= margen < 30%.
        * Saludable   : margen >= 30%.
        """
        if not total_cost and not total_price:
            return False
        if total_price < total_cost:
            return "unprofitable"
        if margin_percent < 10.0:
            return "critical"
        if margin_percent < 20.0:
            return "low"
        if margin_percent < 30.0:
            return "tight"
        return "healthy"

    @api.depends("date_deadline", "state")
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for req in self:
            req.is_overdue = bool(
                req.date_deadline
                and req.date_deadline < today
                and req.state in OPEN_STATES
            )

    # ------------------------------------------------------------------
    # Onchange
    # ------------------------------------------------------------------
    @api.onchange("type_id")
    def _onchange_type_id(self):
        if self.type_id and self.type_id.default_priority:
            self.priority = self.type_id.default_priority

    # ------------------------------------------------------------------
    # Group expand (columnas kanban)
    # ------------------------------------------------------------------
    @api.model
    def _group_expand_states(self, states, domain, order=None):
        return [key for key, _label in STATE_SELECTION]

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == _("Nuevo"):
                vals["name"] = self.env["ir.sequence"].next_by_code("service.request") or _("Nuevo")
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Acciones de estado (statusbar)
    # ------------------------------------------------------------------
    def action_confirm(self):
        self.write({"state": "pending"})

    def action_quote(self):
        for req in self:
            if not req.quote_line_ids:
                raise UserError(
                    _("No puedes presupuestar «%s» sin líneas de presupuesto.") % req.name
                )
        self.write({"state": "quoted"})

    def action_accept(self):
        manager = self.env.user.has_group(
            "service_quote_manager.group_service_quote_manager"
        )
        for req in self:
            if req.margin_category == "unprofitable" and not manager:
                raise UserError(
                    _(
                        "La solicitud «%s» no es rentable: el precio total (%s) es "
                        "inferior al coste total (%s).\n\n"
                        "Solo un usuario del grupo «Service Quote Manager» puede "
                        "aceptar solicitudes no rentables."
                    )
                    % (req.name, req.total_price, req.total_cost)
                )
        self.write({"state": "accepted", "date_accepted": fields.Date.context_today(self)})

    def action_start(self):
        self.write({"state": "in_progress"})

    def action_done(self):
        self.write({"state": "done", "date_done": fields.Date.context_today(self)})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_reset_draft(self):
        self.write({"state": "draft"})

    # ------------------------------------------------------------------
    # Acciones de vista / smart buttons
    # ------------------------------------------------------------------
    def action_view_quote_lines(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Líneas de presupuesto · %s") % self.name,
            "res_model": "service.quote.line",
            "view_mode": "tree,form,graph",
            "domain": [("request_id", "=", self.id)],
            "context": {"default_request_id": self.id},
        }

    def action_open_quick_quote_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Asistente de presupuesto rápido"),
            "res_model": "quick.quote.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_request_id": self.id,
                "default_type_id": self.type_id.id,
            },
        }

    # ------------------------------------------------------------------
    # Notificación / Cron
    # ------------------------------------------------------------------
    def _notify_overdue(self):
        for req in self:
            req.message_post(
                body=_("⚠ La solicitud ha superado su fecha límite (%s).")
                % (req.date_deadline)
            )
            if req.user_id:
                req.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary=_("Solicitud vencida"),
                    note=_(
                        "La solicitud %s ha superado su fecha límite. Revisa su estado."
                    )
                    % req.name,
                    user_id=req.user_id.id,
                )

    @api.model
    def _cron_check_overdue_requests(self):
        """Cron diario: detecta solicitudes vencidas y avisa al responsable.

        1. Recalcula ``is_overdue`` en las solicitudes abiertas (para cubrir el
           cambio de día, que no dispara el compute por sí solo).
        2. Notifica (chatter + actividad) las que acaban de vencer.
        3. Reinicia la marca en las que ya no están vencidas.
        """
        open_requests = self.search(
            [("state", "in", list(OPEN_STATES)), ("active", "=", True)]
        )
        open_requests._compute_is_overdue()

        to_notify = open_requests.filtered(
            lambda r: r.is_overdue and not r.overdue_notified
        )
        to_notify._notify_overdue()
        to_notify.write({"overdue_notified": True})

        recovered = self.search(
            [("overdue_notified", "=", True), ("is_overdue", "=", False)]
        )
        if recovered:
            recovered.write({"overdue_notified": False})
        return True
