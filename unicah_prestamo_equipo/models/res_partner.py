from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    prestamo_ids = fields.One2many("unicah.prestamo", "partner_id", string="Préstamos de equipo")
    prestamos_activos = fields.Integer(string="Equipos en su poder", compute="_compute_prestamos_activos")

    @api.depends("prestamo_ids.state")
    def _compute_prestamos_activos(self):
        for partner in self:
            partner.prestamos_activos = len(
                partner.prestamo_ids.filtered(lambda p: p.state == "prestado")
            )
