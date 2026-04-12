# -*- coding: utf-8 -*-
"""
Telegram Bot Configuration
===========================
Multi-company bot support. Each company can have its own bot.
"""

import logging
import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

TELEGRAM_API_URL = 'https://api.telegram.org/bot{token}/{method}'


class TelegramBot(models.Model):
    _name = 'sm.telegram.bot'
    _description = 'Telegram Bot'
    _order = 'sequence, id'

    name = fields.Char(string='Bot Name', required=True)
    token = fields.Char(string='Bot Token', required=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)
    webhook_url = fields.Char(
        string='Webhook URL',
        compute='_compute_webhook_url',
    )
    webhook_secret = fields.Char(
        string='Webhook Secret',
        help='Secret token to validate incoming webhook requests.',
    )
    bot_username = fields.Char(
        string='Bot Username',
        readonly=True,
        help='Fetched automatically from Telegram.',
    )
    state = fields.Selection([
        ('draft', 'Not Verified'),
        ('verified', 'Verified'),
        ('error', 'Error'),
    ], string='Status', default='draft', readonly=True)

    _sql_constraints = [
        ('token_unique', 'unique(token)', 'Bot token must be unique!'),
    ]

    @api.depends('webhook_secret')
    def _compute_webhook_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        for bot in self:
            if bot.webhook_secret:
                bot.webhook_url = f'{base_url}/telegram/webhook/{bot.webhook_secret}'
            else:
                bot.webhook_url = False

    def action_verify_bot(self):
        """Verify bot token by calling getMe."""
        self.ensure_one()
        url = TELEGRAM_API_URL.format(token=self.token, method='getMe')
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data.get('ok'):
                result = data['result']
                self.write({
                    'bot_username': result.get('username', ''),
                    'name': result.get('first_name', self.name),
                    'state': 'verified',
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Bot verified: @%s') % result.get('username', ''),
                        'type': 'success',
                        'sticky': False,
                    },
                }
            else:
                self.write({'state': 'error'})
                raise UserError(_('Invalid bot token: %s') % data.get('description', ''))
        except requests.RequestException as e:
            self.write({'state': 'error'})
            raise UserError(_('Connection error: %s') % str(e)) from e

    def action_setup_webhook(self):
        """Register webhook URL with Telegram in one click."""
        self.ensure_one()
        if not self.webhook_secret:
            import uuid
            self.webhook_secret = uuid.uuid4().hex[:24]

        url = TELEGRAM_API_URL.format(token=self.token, method='setWebhook')
        payload = {
            'url': self.webhook_url,
            'secret_token': self.webhook_secret,
            'allowed_updates': ['message'],
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
            if data.get('ok'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Webhook Set'),
                        'message': _('Webhook registered successfully.'),
                        'type': 'success',
                        'sticky': False,
                    },
                }
            else:
                raise UserError(_('Webhook setup failed: %s') % data.get('description', ''))
        except requests.RequestException as e:
            raise UserError(_('Connection error: %s') % str(e)) from e

    def action_remove_webhook(self):
        """Remove webhook from Telegram."""
        self.ensure_one()
        url = TELEGRAM_API_URL.format(token=self.token, method='deleteWebhook')
        try:
            resp = requests.post(url, timeout=10)
            data = resp.json()
            if data.get('ok'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Webhook Removed'),
                        'message': _('Webhook deleted successfully.'),
                        'type': 'info',
                        'sticky': False,
                    },
                }
        except requests.RequestException as e:
            raise UserError(_('Connection error: %s') % str(e)) from e

    # ─── API helpers ───

    def send_message(self, chat_id, text, parse_mode=None, reply_markup=None):
        """Send a text message via this bot."""
        self.ensure_one()
        url = TELEGRAM_API_URL.format(token=self.token, method='sendMessage')
        payload = {
            'chat_id': chat_id,
            'text': text,
        }
        if parse_mode:
            payload['parse_mode'] = parse_mode
        if reply_markup:
            payload['reply_markup'] = reply_markup
        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
            if data.get('ok'):
                return True, data
            return False, data.get('description', 'Unknown error')
        except Exception as e:
            _logger.exception('Telegram sendMessage error chat_id=%s', chat_id)
            return False, str(e)

    def send_document(self, chat_id, file_bytes, filename, caption=None, parse_mode=None):
        """Send a document (PDF, etc.) via this bot."""
        self.ensure_one()
        url = TELEGRAM_API_URL.format(token=self.token, method='sendDocument')
        data = {'chat_id': chat_id}
        if caption:
            data['caption'] = caption
        if parse_mode:
            data['parse_mode'] = parse_mode
        safe_name = (filename or 'document').replace(' ', '_')
        try:
            resp = requests.post(
                url,
                data=data,
                files={'document': (safe_name, file_bytes, 'application/pdf')},
                timeout=30,
            )
            result = resp.json()
            if result.get('ok'):
                return True, result
            return False, result.get('description', 'Unknown error')
        except Exception as e:
            _logger.exception('Telegram sendDocument error chat_id=%s', chat_id)
            return False, str(e)

    def send_photo(self, chat_id, photo_bytes, filename='photo.jpg', caption=None, parse_mode=None):
        """Send a photo via this bot."""
        self.ensure_one()
        url = TELEGRAM_API_URL.format(token=self.token, method='sendPhoto')
        data = {'chat_id': chat_id}
        if caption:
            data['caption'] = caption
        if parse_mode:
            data['parse_mode'] = parse_mode
        try:
            resp = requests.post(
                url,
                data=data,
                files={'photo': (filename, photo_bytes, 'image/jpeg')},
                timeout=30,
            )
            result = resp.json()
            if result.get('ok'):
                return True, result
            return False, result.get('description', 'Unknown error')
        except Exception as e:
            _logger.exception('Telegram sendPhoto error chat_id=%s', chat_id)
            return False, str(e)

    @api.model
    def get_bot(self, company_id=None):
        """Get the active bot for the given company (or current company)."""
        company_id = company_id or self.env.company.id
        bot = self.search([
            ('company_id', '=', company_id),
            ('active', '=', True),
            ('state', '=', 'verified'),
        ], limit=1)
        if not bot:
            # Fallback: any verified bot
            bot = self.search([
                ('active', '=', True),
                ('state', '=', 'verified'),
            ], limit=1)
        return bot
