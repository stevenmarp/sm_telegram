# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    telegram_default_bot_id = fields.Many2one(
        'sm.telegram.bot',
        string='Default Telegram Bot',
        config_parameter='sm_telegram.default_bot_id',
    )
    telegram_retry_enabled = fields.Boolean(
        string='Auto-Retry Failed Messages',
        config_parameter='sm_telegram.retry_enabled',
        default=True,
    )
    telegram_max_retries = fields.Integer(
        string='Max Retries',
        config_parameter='sm_telegram.max_retries',
        default=3,
    )
