# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class QuickQuoteWizard(models.TransientModel):
    _name = "quick.quote.wizard"
    _description = "Asistente de presupuesto rápido"

    request_id = fields.Many2one(
        "service.request",
        string="Solicitud",
        required=True,
        default=lambda self: self._default_request(),
    )
    type_id = fields.Many2one(
        "service.request.type",
        string="Plantilla de servicio",
        required=True,
    )
    mode = fields.Selection(
        [
            ("append", "Añadir a las líneas existentes"),
            ("replace", "Reemplazar las líneas existentes"),
        ],
        string="Modo",
        default="append",
        required=True,
    )

    template_line_ids = fields.One2many(
        related="type_id.template_line_ids",
        string="Líneas de la plantilla",
        readonly=True,
    )

    currency_id = fields.Many2one(
        related="request_id.currency_id",
        string="Moneda",
        readonly=True,
    )
    preview_cost = fields.Monetary(
        string="Coste plantilla",
        compute="_compute_preview",
        currency_field="currency_id",
    )
    preview_price = fields.Monetary(
        string="Precio plantilla",
        compute="_compute_preview",
        currency_field="currency_id",
    )
    preview_margin = fields.Monetary(
        string="Beneficio plantilla",
        compute="_compute_preview",
        currency_field="currency_id",
    )
    preview_margin_percent = fields.Float(
        string="Margen plantilla %",
        compute="_compute_preview",
        digits=(16, 2),
    )

    @api.model
    def _default_request(self):
        if self.env.context.get("active_model") == "service.request":
            return self.env.context.get("active_id")
        return False

    @api.depends("type_id")
    def _compute_preview(self):
        for wiz in self:
            lines = wiz.type_id.template_line_ids
            cost = sum(lines.mapped("subtotal_cost"))
            price = sum(lines.mapped("subtotal_price"))
            wiz.preview_cost = cost
            wiz.preview_price = price
            wiz.preview_margin = price - cost
            wiz.preview_margin_percent = ((price - cost) / price * 100.0) if price else 0.0

    def action_apply(self):
        self.ensure_one()
        if not self.request_id:
            raise UserError(_("Selecciona una solicitud sobre la que aplicar la plantilla."))
        if not self.type_id.template_line_ids:
            raise UserError(
                _("La plantilla «%s» no tiene líneas configuradas.") % self.type_id.name
            )

        if self.mode == "replace" and self.request_id.quote_line_ids:
            self.request_id.quote_line_ids.unlink()

        sequence = max(self.request_id.quote_line_ids.mapped("sequence") or [0])
        commands = []
        for tpl in self.type_id.template_line_ids:
            sequence += 10
            commands.append(
                (0, 0, {
                    "sequence": sequence,
                    "line_type": tpl.line_type,
                    "name": tpl.name,
                    "quantity": tpl.quantity,
                    "unit_cost": tpl.unit_cost,
                    "unit_price": tpl.unit_price,
                })
            )

        vals = {"quote_line_ids": commands}
        if not self.request_id.type_id:
            vals["type_id"] = self.type_id.id
        self.request_id.write(vals)

        self.request_id.message_post(
            body=_("Se aplicó la plantilla «%s» (%d líneas) mediante el asistente de presupuesto rápido.")
            % (self.type_id.name, len(self.type_id.template_line_ids))
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Solicitud"),
            "res_model": "service.request",
            "res_id": self.request_id.id,
            "view_mode": "form",
            "target": "current",
        }
