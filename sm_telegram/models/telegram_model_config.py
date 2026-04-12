# -*- coding: utf-8 -*-
from odoo import api, fields, models


class TelegramModelConfig(models.Model):
    _name = 'sm.telegram.model.config'
    _description = 'Telegram Model Configuration'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
    )
    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
    )
    model_name = fields.Char(
        related='model_id.model',
        string='Model Name',
        store=True,
        readonly=True,
    )
    active = fields.Boolean(default=True)
    allowed_report_ids = fields.Many2many(
        'ir.actions.report',
        string='Allowed Reports',
        domain="[('model', '=', model_name)]",
        help='Reports that can be sent via Telegram. Leave empty to allow all.',
    )
    allowed_user_ids = fields.Many2many(
        'res.users',
        string='Allowed Users',
        help='Users who can send Telegram from this model. Leave empty to allow all.',
    )
    default_template_id = fields.Many2one(
        'sm.telegram.template',
        string='Default Template',
        help='Default message template when sending from this model.',
    )

    _sql_constraints = [
        ('model_unique', 'unique(model_id)', 'A Telegram config already exists for this model.'),
    ]

    @api.depends('model_id')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.model_id.name if rec.model_id else ''

    def _can_send_telegram(self, model_name):
        """Check if current user can send Telegram from given model."""
        config = self.search([
            ('model_name', '=', model_name),
            ('active', '=', True),
        ], limit=1)
        if not config:
            return False
        if not config.allowed_user_ids:
            return True
        return self.env.user in config.allowed_user_ids

    def _get_allowed_reports(self, model_name):
        """Return allowed reports for the model."""
        config = self.search([
            ('model_name', '=', model_name),
            ('active', '=', True),
        ], limit=1)
        if not config:
            return self.env['ir.actions.report']
        if config.allowed_report_ids:
            return config.allowed_report_ids.filtered(
                lambda r: r.report_type in ('qweb-pdf', 'qweb-html')
            )
        return self.env['ir.actions.report'].search([
            ('model', '=', model_name),
            ('report_type', 'in', ('qweb-pdf', 'qweb-html')),
        ])

    def _get_default_template(self, model_name):
        """Return default template for the model."""
        config = self.search([
            ('model_name', '=', model_name),
            ('active', '=', True),
        ], limit=1)
        return config.default_template_id if config else self.env['sm.telegram.template']
