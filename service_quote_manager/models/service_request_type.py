# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .service_quote_line import LINE_TYPES


class ServiceRequestType(models.Model):
    _name = "service.request.type"
    _description = "Tipo de servicio"
    _order = "sequence, name"

    name = fields.Char(string="Nombre", required=True, translate=True)
    code = fields.Char(string="Código")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Índice de color")
    default_priority = fields.Selection(
        [("0", "Baja"), ("1", "Media"), ("2", "Alta"), ("3", "Urgente")],
        string="Prioridad por defecto",
        default="1",
    )
    description = fields.Text(string="Descripción")

    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        default=lambda self: self.env.company.currency_id,
    )
    template_line_ids = fields.One2many(
        "service.quote.template.line",
        "type_id",
        string="Plantilla de líneas",
        copy=True,
    )

    template_line_count = fields.Integer(
        string="Nº de líneas de plantilla",
        compute="_compute_template_totals",
    )
    template_cost = fields.Monetary(
        string="Coste plantilla",
        compute="_compute_template_totals",
        currency_field="currency_id",
    )
    template_price = fields.Monetary(
        string="Precio plantilla",
        compute="_compute_template_totals",
        currency_field="currency_id",
    )
    template_margin_percent = fields.Float(
        string="Margen plantilla %",
        compute="_compute_template_totals",
        digits=(16, 2),
    )
    request_count = fields.Integer(
        string="Solicitudes",
        compute="_compute_request_count",
    )

    @api.depends(
        "template_line_ids.subtotal_cost",
        "template_line_ids.subtotal_price",
    )
    def _compute_template_totals(self):
        for rec in self:
            cost = sum(rec.template_line_ids.mapped("subtotal_cost"))
            price = sum(rec.template_line_ids.mapped("subtotal_price"))
            rec.template_line_count = len(rec.template_line_ids)
            rec.template_cost = cost
            rec.template_price = price
            rec.template_margin_percent = ((price - cost) / price * 100.0) if price else 0.0

    def _compute_request_count(self):
        Request = self.env["service.request"]
        for rec in self:
            rec.request_count = Request.search_count([("type_id", "=", rec.id)]) if rec.id else 0

    def action_view_requests(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": "service.request",
            "view_mode": "tree,kanban,form",
            "domain": [("type_id", "=", self.id)],
            "context": {"default_type_id": self.id},
        }


class ServiceQuoteTemplateLine(models.Model):
    _name = "service.quote.template.line"
    _description = "Línea de plantilla de presupuesto"
    _order = "type_id, sequence, id"

    type_id = fields.Many2one(
        "service.request.type",
        string="Tipo de servicio",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    line_type = fields.Selection(
        LINE_TYPES,
        string="Tipo",
        required=True,
        default="material",
    )
    name = fields.Char(string="Descripción", required=True)
    quantity = fields.Float(string="Cantidad", default=1.0, digits="Product Unit of Measure")
    unit_cost = fields.Monetary(string="Coste unitario", currency_field="currency_id")
    unit_price = fields.Monetary(string="Precio unitario", currency_field="currency_id")

    subtotal_cost = fields.Monetary(
        string="Coste",
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )
    subtotal_price = fields.Monetary(
        string="Precio",
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="type_id.currency_id",
        string="Moneda",
        store=True,
        readonly=True,
    )

    @api.depends("quantity", "unit_cost", "unit_price")
    def _compute_amounts(self):
        for line in self:
            line.subtotal_cost = line.quantity * line.unit_cost
            line.subtotal_price = line.quantity * line.unit_price
