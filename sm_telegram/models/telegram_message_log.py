# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class TelegramMessageLog(models.Model):
    _name = 'sm.telegram.message.log'
    _description = 'Telegram Message Log'
    _order = 'sent_at desc'

    partner_id = fields.Many2one('res.partner', string='Recipient', index=True)
    chat_id = fields.Char(string='Chat ID')
    res_model = fields.Char(string='Document Model', index=True)
    res_id = fields.Integer(string='Document ID')
    message_text = fields.Text(string='Message')
    report_id = fields.Many2one('ir.actions.report', string='Report')
    template_id = fields.Many2one('sm.telegram.template', string='Template')
    bot_id = fields.Many2one('sm.telegram.bot', string='Bot')

    status = fields.Selection([
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('error', 'Error'),
    ], string='Status', default='sent', index=True)

    telegram_response = fields.Text(string='Telegram Response')
    error_message = fields.Text(string='Error Message')
    retry_count = fields.Integer(string='Retry Count', default=0)
    max_retries = fields.Integer(string='Max Retries', default=3)

    sent_at = fields.Datetime(
        string='Sent At',
        default=fields.Datetime.now,
        readonly=True,
    )
    scheduled_at = fields.Datetime(
        string='Scheduled For',
        help='If set, message will be sent at this time instead of immediately.',
    )
    sent_by = fields.Many2one(
        'res.users',
        string='Sent By',
        default=lambda self: self.env.user,
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )

    parse_mode = fields.Selection([
        ('plain', 'Plain Text'),
        ('Markdown', 'Markdown'),
        ('HTML', 'HTML'),
    ], string='Format', default='plain')

    message_type = fields.Selection([
        ('text', 'Text'),
        ('document', 'Document'),
        ('photo', 'Photo'),
    ], string='Type', default='text')

    def action_retry(self):
        """Manually retry a failed message."""
        self.ensure_one()
        if self.status != 'error':
            return
        self._send_queued_message()

    def _send_queued_message(self):
        """Send this queued/failed message."""
        self.ensure_one()
        bot = self.bot_id or self.env['sm.telegram.bot'].get_bot(self.company_id.id)
        if not bot:
            self.write({
                'status': 'error',
                'error_message': 'No verified bot found.',
            })
            return False

        chat_id = self.chat_id
        if not chat_id:
            self.write({
                'status': 'error',
                'error_message': 'No chat ID.',
            })
            return False

        parse_mode = self.parse_mode if self.parse_mode != 'plain' else None
        ok, resp = False, 'Nothing to send.'

        # Send text message first (if present)
        if self.message_text:
            ok, resp = bot.send_message(chat_id, self.message_text, parse_mode=parse_mode)

        # Send PDF document (if present)
        if self.message_type == 'document' and self.report_id and self.res_model and self.res_id:
            record = self.env[self.res_model].browse(self.res_id)
            if record.exists():
                pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                    self.report_id, record.ids,
                )
                ok, resp = bot.send_document(
                    chat_id, pdf_content,
                    self.report_id.name + '.pdf',
                    parse_mode=parse_mode,
                )
            else:
                ok, resp = False, 'Record no longer exists.'

        if ok:
            self.write({
                'status': 'sent',
                'sent_at': fields.Datetime.now(),
                'error_message': False,
            })
            return True
        else:
            error = resp if isinstance(resp, str) else str(resp)
            self.write({
                'status': 'error',
                'error_message': error,
                'retry_count': self.retry_count + 1,
            })
            return False

    @api.model
    def _cron_retry_failed(self):
        """Cron: retry failed messages that haven't exceeded max retries."""
        retry_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'sm_telegram.retry_enabled', 'True'
        )
        if retry_enabled != 'True':
            return

        max_retries = int(self.env['ir.config_parameter'].sudo().get_param(
            'sm_telegram.max_retries', '3'
        ))
        failed = self.search([
            ('status', '=', 'error'),
            ('retry_count', '<', max_retries),
        ], limit=20)

        for log in failed:
            try:
                log._send_queued_message()
            except Exception:
                _logger.exception('Telegram retry failed for log %d', log.id)

    @api.model
    def _cron_send_scheduled(self):
        """Cron: send queued messages whose scheduled_at has passed."""
        now = fields.Datetime.now()
        queued = self.search([
            ('status', '=', 'queued'),
            ('scheduled_at', '<=', now),
        ], limit=50)

        for log in queued:
            try:
                log._send_queued_message()
            except Exception:
                _logger.exception('Telegram scheduled send failed for log %d', log.id)
