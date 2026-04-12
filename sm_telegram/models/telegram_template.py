# -*- coding: utf-8 -*-
"""
Telegram Message Templates
============================
Dynamic message templates with Jinja2 variables.
Example: "Hello {{ object.partner_id.name }}, your order {{ object.name }} is confirmed!"
"""

import logging

from jinja2 import Environment, BaseLoader, exceptions as jinja2_exc

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TelegramTemplate(models.Model):
    _name = 'sm.telegram.template'
    _description = 'Telegram Message Template'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    model_id = fields.Many2one(
        'ir.model',
        string='Applies To',
        help='The Odoo model this template can be used with.',
    )
    model_name = fields.Char(
        related='model_id.model',
        store=True,
        readonly=True,
    )
    active = fields.Boolean(default=True)

    body = fields.Text(
        string='Message Body',
        required=True,
        help='Message template using Jinja2 syntax.\n'
             'Available variables:\n'
             '  {{ object }} — the current record\n'
             '  {{ user }} — the current user\n'
             '  {{ company }} — the current company\n'
             '  {{ partner }} — the recipient partner\n'
             'Example: Hello {{ object.partner_id.name }}, '
             'your order {{ object.name }} is ready!',
    )

    parse_mode = fields.Selection([
        ('plain', 'Plain Text'),
        ('Markdown', 'Markdown'),
        ('HTML', 'HTML'),
    ], string='Format', default='plain')

    report_id = fields.Many2one(
        'ir.actions.report',
        string='Attach Report',
        domain="[('model', '=', model_name)]",
        help='Automatically attach this report as PDF.',
    )

    include_buttons = fields.Boolean(
        string='Include Buttons',
        help='Add inline keyboard buttons to the message.',
    )
    button_ids = fields.One2many(
        'sm.telegram.template.button',
        'template_id',
        string='Buttons',
    )

    preview = fields.Text(
        string='Preview',
        compute='_compute_preview',
    )

    @api.depends('body')
    def _compute_preview(self):
        for rec in self:
            if rec.body:
                rec.preview = rec.body[:200] + ('...' if len(rec.body or '') > 200 else '')
            else:
                rec.preview = ''

    def render_message(self, record, partner=None):
        """Render the template body with the given record context."""
        self.ensure_one()
        env = Environment(loader=BaseLoader(), autoescape=False)
        try:
            tpl = env.from_string(self.body or '')
            return tpl.render({
                'object': record,
                'user': self.env.user,
                'company': self.env.company,
                'partner': partner or record.env['res.partner'],
            })
        except jinja2_exc.TemplateSyntaxError as e:
            raise ValidationError(
                _('Template syntax error at line %d: %s') % (e.lineno, e.message)
            ) from e
        except Exception as e:
            _logger.exception('Template render error: %s', self.name)
            raise ValidationError(_('Template render error: %s') % str(e)) from e

    def get_reply_markup(self):
        """Build Telegram inline keyboard from button_ids."""
        self.ensure_one()
        if not self.include_buttons or not self.button_ids:
            return None
        keyboard = []
        row = []
        for btn in self.button_ids.sorted('sequence'):
            row.append({
                'text': btn.text,
                'url': btn.url,
            })
            if btn.new_row or len(row) >= 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        return {'inline_keyboard': keyboard}

    def action_test_render(self):
        """Test render the template with a dummy context."""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Preview'),
                'message': self.preview or _('(empty)'),
                'type': 'info',
                'sticky': True,
            },
        }


class TelegramTemplateButton(models.Model):
    _name = 'sm.telegram.template.button'
    _description = 'Telegram Template Inline Button'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        'sm.telegram.template',
        string='Template',
        required=True,
        ondelete='cascade',
    )
    text = fields.Char(string='Button Text', required=True)
    url = fields.Char(string='URL', required=True)
    sequence = fields.Integer(default=10)
    new_row = fields.Boolean(
        string='New Row',
        help='Start a new row before this button.',
    )
