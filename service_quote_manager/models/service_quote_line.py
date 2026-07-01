# -*- coding: utf-8 -*-
from odoo import api, fields, models

# Tipos de línea de presupuesto. Reutilizado por las líneas reales
# (service.quote.line) y por las líneas de plantilla (service.quote.template.line).
LINE_TYPES = [
    ("material", "Material"),
    ("labor", "Mano de obra"),
    ("travel", "Desplazamiento"),
    ("extra", "Extra"),
]


class ServiceQuoteLine(models.Model):
    _name = "service.quote.line"
    _description = "Línea de presupuesto de servicio"
    _order = "request_id, sequence, id"

    request_id = fields.Many2one(
        "service.request",
        string="Solicitud",
        required=True,
        ondelete="cascade",
        index=True,
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
    margin = fields.Monetary(
        string="Beneficio",
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )

    currency_id = fields.Many2one(
        related="request_id.currency_id",
        string="Moneda",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        related="request_id.company_id",
        string="Compañía",
        store=True,
        readonly=True,
    )

    @api.depends("quantity", "unit_cost", "unit_price")
    def _compute_amounts(self):
        for line in self:
            line.subtotal_cost = line.quantity * line.unit_cost
            line.subtotal_price = line.quantity * line.unit_price
            line.margin = line.subtotal_price - line.subtotal_cost
