from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

DIAS_MAXIMOS = 7


class UnicahPrestamo(models.Model):
    _name = "unicah.prestamo"
    _description = "Préstamo de equipo"
    _order = "fecha_salida desc"

    name = fields.Char(string="Préstamo", compute="_compute_name", store=True)
    equipo_id = fields.Many2one("unicah.equipo", string="Equipo", required=True)
    partner_id = fields.Many2one("res.partner", string="Solicitante", required=True)
    fecha_salida = fields.Datetime(string="Salida", required=True, default=fields.Datetime.now)
    fecha_limite = fields.Datetime(
        string="Fecha límite",
        required=True,
        default=lambda self: fields.Datetime.now() + timedelta(days=3),
    )
    fecha_devolucion = fields.Datetime(string="Devuelto el", readonly=True, copy=False)
    state = fields.Selection(
        [
            ("borrador", "Borrador"),
            ("prestado", "Prestado"),
            ("devuelto", "Devuelto"),
        ],
        string="Estado",
        default="borrador",
        readonly=True,
        copy=False,
    )
    notas = fields.Text(string="Notas")
    dias_retraso = fields.Integer(string="Días de retraso", compute="_compute_dias_retraso")

    @api.depends("equipo_id", "partner_id")
    def _compute_name(self):
        for prestamo in self:
            if prestamo.equipo_id and prestamo.partner_id:
                prestamo.name = f"{prestamo.equipo_id.name} - {prestamo.partner_id.name}"
            else:
                prestamo.name = "Nuevo préstamo"

    @api.depends("state", "fecha_limite", "fecha_devolucion")
    def _compute_dias_retraso(self):
        ahora = fields.Datetime.now()
        for prestamo in self:
            prestamo.dias_retraso = 0
            if not prestamo.fecha_limite or prestamo.state == "borrador":
                continue
            fin = prestamo.fecha_devolucion if prestamo.state == "devuelto" else ahora
            if fin and fin > prestamo.fecha_limite:
                prestamo.dias_retraso = (fin - prestamo.fecha_limite).days

    @api.constrains("fecha_salida", "fecha_limite")
    def _check_fechas(self):
        for prestamo in self:
            if prestamo.fecha_limite < prestamo.fecha_salida:
                raise ValidationError("La fecha límite no puede ser anterior a la fecha de salida.")
            dias = (prestamo.fecha_limite - prestamo.fecha_salida).days
            if dias > DIAS_MAXIMOS:
                raise ValidationError(
                    f"Un préstamo no puede durar más de {DIAS_MAXIMOS} días. "
                    f"Este dura {dias}."
                )

    @api.constrains("equipo_id", "state")
    def _check_equipo_libre(self):
        for prestamo in self.filtered(lambda p: p.state == "prestado"):
            otros = self.search([
                ("equipo_id", "=", prestamo.equipo_id.id),
                ("state", "=", "prestado"),
                ("id", "!=", prestamo.id),
            ], limit=1)
            if otros:
                raise ValidationError(
                    f"El equipo {prestamo.equipo_id.name} ya está prestado a "
                    f"{otros.partner_id.name}."
                )

    def action_entregar(self):
        for prestamo in self:
            if prestamo.equipo_id.en_mantenimiento:
                raise UserError("Este equipo está en mantenimiento y no se puede prestar.")
            prestamo.state = "prestado"

    def action_devolver(self):
        for prestamo in self:
            prestamo.write({
                "state": "devuelto",
                "fecha_devolucion": fields.Datetime.now(),
            })
