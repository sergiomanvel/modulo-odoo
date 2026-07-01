# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import Form, TransactionCase, new_test_user, tagged

from ..models.service_request import ServiceRequest


@tagged("post_install", "-at_install")
class TestServiceRequest(TransactionCase):
    """Cobertura de: cálculo de márgenes, secuencia, flujo de estados,
    regla de rentabilidad, asistente de presupuesto rápido y cron de vencidas.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Cliente Test"})
        cls.type_led = cls.env.ref("service_quote_manager.type_led")
        cls.type_reparacion = cls.env.ref("service_quote_manager.type_reparacion")

        # Usuario del grupo básico y usuario del grupo manager.
        cls.user = new_test_user(
            cls.env,
            login="sqm_user",
            groups="base.group_user,service_quote_manager.group_service_quote_user",
            name="SQM User",
        )
        cls.manager = new_test_user(
            cls.env,
            login="sqm_manager",
            groups="base.group_user,service_quote_manager.group_service_quote_manager",
            name="SQM Manager",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _create_request(self, lines=None, **kwargs):
        vals = {
            "title": kwargs.pop("title", "Solicitud de prueba"),
            "partner_id": self.partner.id,
        }
        vals.update(kwargs)
        if lines is not None:
            vals["quote_line_ids"] = [(0, 0, line) for line in lines]
        return self.env["service.request"].create(vals)

    # ------------------------------------------------------------------
    # Secuencia
    # ------------------------------------------------------------------
    def test_sequence_assigned_on_create(self):
        request = self._create_request()
        self.assertTrue(request.name.startswith("SR-"))
        self.assertNotEqual(request.name, "Nuevo")

    # ------------------------------------------------------------------
    # Cálculo de líneas y totales
    # ------------------------------------------------------------------
    def test_line_and_request_totals(self):
        request = self._create_request(
            lines=[
                {"line_type": "material", "name": "Material", "quantity": 2, "unit_cost": 50, "unit_price": 80},
                {"line_type": "labor", "name": "Mano de obra", "quantity": 3, "unit_cost": 20, "unit_price": 40},
            ]
        )
        # Línea 1: coste 100 / precio 160 ; Línea 2: coste 60 / precio 120
        self.assertEqual(request.total_cost, 160.0)
        self.assertEqual(request.total_price, 280.0)
        self.assertEqual(request.margin_amount, 120.0)
        self.assertAlmostEqual(request.margin_percent, 120.0 / 280.0 * 100.0, places=2)

    # ------------------------------------------------------------------
    # Reglas de categoría de margen (método puro, valores límite)
    # ------------------------------------------------------------------
    def test_margin_category_rules(self):
        get = ServiceRequest._get_margin_category
        cases = [
            # (coste, precio, margen%) -> categoría esperada
            (0.0, 0.0, 0.0, False),          # sin datos
            (100.0, 90.0, -11.0, "unprofitable"),  # precio < coste
            (100.0, 200.0, 9.99, "critical"),      # < 10
            (100.0, 200.0, 10.0, "low"),           # 10 -> bajo
            (100.0, 200.0, 19.99, "low"),          # < 20
            (100.0, 200.0, 20.0, "tight"),         # 20 -> ajustado
            (100.0, 200.0, 29.99, "tight"),        # < 30
            (100.0, 200.0, 30.0, "healthy"),       # >= 30
            (100.0, 200.0, 55.0, "healthy"),
        ]
        for cost, price, pct, expected in cases:
            with self.subTest(cost=cost, price=price, pct=pct):
                self.assertEqual(get(cost, price, pct), expected)

    def test_unprofitable_request_is_categorized(self):
        request = self._create_request(
            lines=[
                {"line_type": "material", "name": "Caro", "quantity": 1, "unit_cost": 900, "unit_price": 800},
            ]
        )
        self.assertEqual(request.margin_category, "unprofitable")

    # ------------------------------------------------------------------
    # Flujo de estados
    # ------------------------------------------------------------------
    def test_cannot_quote_without_lines(self):
        request = self._create_request()
        request.action_confirm()
        self.assertEqual(request.state, "pending")
        with self.assertRaises(UserError):
            request.action_quote()

    def test_full_state_flow(self):
        request = self._create_request(
            lines=[{"line_type": "labor", "name": "Trabajo", "quantity": 1, "unit_cost": 10, "unit_price": 30}]
        )
        request.action_confirm()
        request.action_quote()
        self.assertEqual(request.state, "quoted")
        request.action_accept()
        self.assertEqual(request.state, "accepted")
        self.assertTrue(request.date_accepted)
        request.action_start()
        self.assertEqual(request.state, "in_progress")
        request.action_done()
        self.assertEqual(request.state, "done")
        self.assertTrue(request.date_done)

    # ------------------------------------------------------------------
    # Regla de negocio: aceptar solicitud no rentable
    # ------------------------------------------------------------------
    def test_unprofitable_cannot_be_accepted_by_user(self):
        request = self._create_request(
            lines=[{"line_type": "material", "name": "Caro", "quantity": 1, "unit_cost": 900, "unit_price": 800}],
            state="quoted",
        )
        with self.assertRaises(UserError):
            request.with_user(self.user).action_accept()
        self.assertEqual(request.state, "quoted")

    def test_unprofitable_can_be_accepted_by_manager(self):
        request = self._create_request(
            lines=[{"line_type": "material", "name": "Caro", "quantity": 1, "unit_cost": 900, "unit_price": 800}],
            state="quoted",
        )
        request.with_user(self.manager).action_accept()
        self.assertEqual(request.state, "accepted")

    def test_profitable_can_be_accepted_by_user(self):
        request = self._create_request(
            lines=[{"line_type": "labor", "name": "Trabajo", "quantity": 1, "unit_cost": 10, "unit_price": 30}],
            state="quoted",
        )
        request.with_user(self.user).action_accept()
        self.assertEqual(request.state, "accepted")

    # ------------------------------------------------------------------
    # Asistente de presupuesto rápido (wizard)
    # ------------------------------------------------------------------
    def test_wizard_appends_template_lines(self):
        request = self._create_request()
        wizard = self.env["quick.quote.wizard"].create({
            "request_id": request.id,
            "type_id": self.type_led.id,
            "mode": "append",
        })
        # El preview refleja los totales de la plantilla.
        self.assertGreater(wizard.preview_price, 0.0)
        wizard.action_apply()
        self.assertEqual(len(request.quote_line_ids), len(self.type_led.template_line_ids))

    def test_wizard_replace_mode(self):
        request = self._create_request(
            lines=[{"line_type": "extra", "name": "Antigua", "quantity": 1, "unit_cost": 5, "unit_price": 10}]
        )
        wizard = self.env["quick.quote.wizard"].create({
            "request_id": request.id,
            "type_id": self.type_reparacion.id,
            "mode": "replace",
        })
        wizard.action_apply()
        self.assertEqual(len(request.quote_line_ids), len(self.type_reparacion.template_line_ids))
        self.assertNotIn("Antigua", request.quote_line_ids.mapped("name"))

    # ------------------------------------------------------------------
    # Formulario (flujo real de UI con onchange y one2many)
    # ------------------------------------------------------------------
    def test_form_onchange_sets_priority(self):
        with Form(self.env["service.request"]) as form:
            form.title = "Vía formulario"
            form.partner_id = self.partner
            form.type_id = self.type_reparacion  # default_priority = '3'
        request = form.record
        self.assertEqual(request.priority, "3")

    # ------------------------------------------------------------------
    # Cron de solicitudes vencidas
    # ------------------------------------------------------------------
    def test_cron_marks_and_notifies_overdue(self):
        yesterday = fields.Date.today() - timedelta(days=1)
        request = self._create_request(
            date_deadline=yesterday,
            state="pending",
        )
        self.assertTrue(request.is_overdue)  # compute directo

        self.env["service.request"]._cron_check_overdue_requests()
        self.assertTrue(request.overdue_notified)
        # Se ha creado una actividad para el responsable.
        self.assertTrue(request.activity_ids)

    def test_cron_resets_flag_when_no_longer_overdue(self):
        yesterday = fields.Date.today() - timedelta(days=1)
        request = self._create_request(date_deadline=yesterday, state="pending")
        self.env["service.request"]._cron_check_overdue_requests()
        self.assertTrue(request.overdue_notified)

        # Al mover la fecha al futuro deja de estar vencida.
        request.date_deadline = fields.Date.today() + timedelta(days=5)
        self.assertFalse(request.is_overdue)
        self.env["service.request"]._cron_check_overdue_requests()
        self.assertFalse(request.overdue_notified)
