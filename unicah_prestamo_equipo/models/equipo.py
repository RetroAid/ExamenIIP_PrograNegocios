from odoo import api, fields, models


class UnicahEquipo(models.Model):
    _name = "unicah.equipo"
    _description = "Equipo prestable"

    name = fields.Char(string="Nombre", required=True)
    codigo = fields.Char(string="Código", required=True, copy=False)
    categoria = fields.Selection(
        [
            ("proyector", "Proyector"),
            ("laptop", "Laptop"),
            ("camara", "Cámara"),
            ("otro", "Otro"),
        ],
        string="Categoría",
        default="otro",
    )
    en_mantenimiento = fields.Boolean(string="En mantenimiento")
    active = fields.Boolean(string="Activo", default=True)
    prestamo_ids = fields.One2many("unicah.prestamo", "equipo_id", string="Préstamos")
    estado = fields.Selection(
        [
            ("disponible", "Disponible"),
            ("prestado", "Prestado"),
            ("mantenimiento", "En mantenimiento"),
        ],
        string="Estado",
        compute="_compute_estado",
        store=True,
    )
    total_prestamos = fields.Integer(string="Veces prestado", compute="_compute_total_prestamos")

    _codigo_unico = models.Constraint(
        "UNIQUE(codigo)",
        "Ya existe un equipo con ese código.",
    )

    @api.depends("en_mantenimiento", "prestamo_ids.state")
    def _compute_estado(self):
        for equipo in self:
            if equipo.en_mantenimiento:
                equipo.estado = "mantenimiento"
            elif equipo.prestamo_ids.filtered(lambda p: p.state == "prestado"):
                equipo.estado = "prestado"
            else:
                equipo.estado = "disponible"

    @api.depends("prestamo_ids")
    def _compute_total_prestamos(self):
        for equipo in self:
            equipo.total_prestamos = len(equipo.prestamo_ids)
