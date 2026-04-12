# -*- coding: utf-8 -*-
"""
Telegram Send Wizard
=====================
Wizard to send Telegram messages from any record's chatter.
Supports text, PDF reports, photos, templates, inline buttons,
Markdown/HTML formatting, and scheduled sending.
"""

import json
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

BULK_SEND_LIMIT = 50


class TelegramSendWizard(models.TransientModel):
    _name = 'sm.telegram.send.wizard'
    _description = 'Send Telegram Message'

    # Context-driven
    res_model = fields.Char(string='Document Model', readonly=True)
    res_id = fields.Integer(string='Document ID', readonly=True)

    # Recipients
    partner_ids = fields.Many2many(
        'res.partner',
        string='Recipients',
        domain=[('telegram_chat_id', '!=', False), ('telegram_chat_id', '!=', '')],
        required=True,
    )

    # Content
    template_id = fields.Many2one(
        'sm.telegram.template',
        string='Template',
    )
    message = fields.Text(string='Message')
    parse_mode = fields.Selection([
        ('plain', 'Plain Text'),
        ('Markdown', 'Markdown'),
        ('HTML', 'HTML'),
    ], string='Format', default='plain')

    # Attachments
    report_id = fields.Many2one(
        'ir.actions.report',
        string='Report (PDF)',
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
        help='Send images or files as Telegram photos/documents.',
    )

    # Scheduling
    send_mode = fields.Selection([
        ('now', 'Send Now'),
        ('scheduled', 'Schedule'),
    ], string='Send Mode', default='now')
    scheduled_at = fields.Datetime(string='Schedule At')

    # Computed
    allowed_report_domain_ids = fields.Many2many(
        'ir.actions.report',
        relation='sm_tg_wizard_allowed_reports_rel',
        string='Allowed Reports',
        compute='_compute_allowed_report_domain_ids',
    )

    @api.depends('res_model')
    def _compute_allowed_report_domain_ids(self):
        for rec in self:
            if rec.res_model:
                rec.allowed_report_domain_ids = (
                    self.env['sm.telegram.model.config']._get_allowed_reports(rec.res_model)
                )
            else:
                rec.allowed_report_domain_ids = self.env['ir.actions.report']

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        ctx = self.env.context
        model = ctx.get('active_model')
        rec_id = ctx.get('active_id')
        if model:
            result['res_model'] = model
        if rec_id:
            result['res_id'] = rec_id
        # Auto-select default template
        if model:
            tpl = self.env['sm.telegram.model.config']._get_default_template(model)
            if tpl:
                result['template_id'] = tpl.id
        return result

    @api.onchange('template_id')
    def _onchange_template_id(self):
        """Apply template to message field."""
        if self.template_id:
            self.parse_mode = self.template_id.parse_mode
            if self.template_id.report_id:
                self.report_id = self.template_id.report_id
            # Render preview if record exists
            if self.res_model and self.res_id:
                record = self.env[self.res_model].browse(self.res_id)
                if record.exists():
                    self.message = self.template_id.render_message(record)

    @api.onchange('res_model')
    def _onchange_res_model(self):
        if self.res_model:
            allowed = self.env['sm.telegram.model.config']._get_allowed_reports(self.res_model)
            return {'domain': {'report_id': [('id', 'in', allowed.ids)]}}
        return {'domain': {'report_id': []}}

    def _validate(self):
        self.ensure_one()
        if not self.partner_ids:
            raise ValidationError(_('Please select at least one recipient.'))
        if not self.message and not self.report_id and not self.attachment_ids:
            raise ValidationError(_('Please enter a message, select a report, or attach a file.'))
        if len(self.partner_ids) > BULK_SEND_LIMIT:
            raise ValidationError(
                _('Maximum %d recipients at a time.') % BULK_SEND_LIMIT
            )
        if self.send_mode == 'scheduled' and not self.scheduled_at:
            raise ValidationError(_('Please set a schedule date.'))

    def action_send(self):
        """Send or schedule the Telegram message."""
        self.ensure_one()
        self._validate()

        if self.send_mode == 'scheduled':
            return self._schedule_messages()

        return self._send_now()

    def _send_now(self):
        """Send messages immediately."""
        bot = self.env['sm.telegram.bot'].get_bot()
        if not bot:
            raise UserError(
                _('No verified Telegram bot found. '
                  'Please configure a bot in Telegram > Configuration > Bots.')
            )

        record = self.env[self.res_model].browse(self.res_id) if self.res_model and self.res_id else None

        # Render template per partner if template is set
        pdf_data = None
        if self.report_id and record:
            pdf_data = self._render_pdf(record)

        parse_mode = self.parse_mode if self.parse_mode != 'plain' else None

        # Build inline keyboard from template
        reply_markup = None
        if self.template_id:
            rm = self.template_id.get_reply_markup()
            if rm:
                reply_markup = json.dumps(rm)

        success_partners = []
        failed_partners = []

        for partner in self.partner_ids:
            chat_id = partner.telegram_chat_id
            errors = []

            # Render per-partner message if template
            msg_text = self.message
            if self.template_id and record:
                msg_text = self.template_id.render_message(record, partner=partner)

            # Send text message
            if msg_text:
                ok, resp = bot.send_message(
                    chat_id, msg_text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
                if not ok:
                    errors.append(resp if isinstance(resp, str) else str(resp))

            # Send PDF
            if self.report_id and pdf_data:
                ok, resp = bot.send_document(
                    chat_id, pdf_data,
                    self.report_id.name + '.pdf',
                    parse_mode=parse_mode,
                )
                if not ok:
                    errors.append(resp if isinstance(resp, str) else str(resp))

            # Send attachments (images as photos, rest as documents)
            for att in self.attachment_ids:
                att_data = att.raw
                if att.mimetype and att.mimetype.startswith('image/'):
                    ok, resp = bot.send_photo(
                        chat_id, att_data,
                        filename=att.name,
                    )
                else:
                    ok, resp = bot.send_document(
                        chat_id, att_data,
                        att.name,
                    )
                if not ok:
                    errors.append(resp if isinstance(resp, str) else str(resp))

            if errors:
                failed_partners.append((partner, '; '.join(errors)))
                self._write_log(partner, bot, status='error', error_message='; '.join(errors))
            else:
                success_partners.append(partner)
                self._write_log(partner, bot, status='sent')

        # Post chatter note
        if record and hasattr(record, 'message_post'):
            self._post_chatter(record, success_partners, failed_partners)

        if failed_partners:
            names = ', '.join(p.name for p, _ in failed_partners)
            raise UserError(
                _('Failed to send to: %s. Check Telegram > Message Logs.') % names
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sent'),
                'message': _('Telegram message sent to %d recipient(s).') % len(success_partners),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def _schedule_messages(self):
        """Create queued log entries to be sent by cron."""
        bot = self.env['sm.telegram.bot'].get_bot()

        for partner in self.partner_ids:
            msg_text = self.message
            if self.template_id and self.res_model and self.res_id:
                record = self.env[self.res_model].browse(self.res_id)
                if record.exists():
                    msg_text = self.template_id.render_message(record, partner=partner)

            self.env['sm.telegram.message.log'].create({
                'partner_id': partner.id,
                'chat_id': partner.telegram_chat_id,
                'res_model': self.res_model,
                'res_id': self.res_id,
                'message_text': msg_text,
                'report_id': self.report_id.id if self.report_id else False,
                'template_id': self.template_id.id if self.template_id else False,
                'bot_id': bot.id if bot else False,
                'status': 'queued',
                'scheduled_at': self.scheduled_at,
                'parse_mode': self.parse_mode,
                'message_type': 'document' if self.report_id else 'text',
                'company_id': self.env.company.id,
            })

        # Convert to user timezone for display
        user_tz_dt = fields.Datetime.context_timestamp(self, self.scheduled_at)
        display_time = user_tz_dt.strftime('%d/%m/%Y %H:%M:%S')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Scheduled'),
                'message': _('%d messages scheduled for %s.') % (
                    len(self.partner_ids),
                    display_time,
                ),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def _render_pdf(self, record):
        """Render PDF report for the record."""
        if self.report_id.report_type not in ('qweb-pdf', 'qweb-html'):
            raise UserError(
                _('Report "%s" is not a PDF report (type: %s). '
                  'Only PDF reports can be sent via Telegram.')
                % (self.report_id.name, self.report_id.report_type)
            )
        try:
            pdf_content, _content_type = self.env['ir.actions.report']._render_qweb_pdf(
                self.report_id, record.ids,
            )
            return pdf_content
        except Exception as e:
            _logger.exception('PDF render error: %s', self.report_id.name)
            raise UserError(_('Could not render PDF: %s') % str(e)) from e

    def _write_log(self, partner, bot, status, error_message=None):
        """Write a message log entry."""
        self.env['sm.telegram.message.log'].create({
            'partner_id': partner.id,
            'chat_id': partner.telegram_chat_id,
            'res_model': self.res_model,
            'res_id': self.res_id,
            'message_text': self.message or False,
            'report_id': self.report_id.id if self.report_id else False,
            'template_id': self.template_id.id if self.template_id else False,
            'bot_id': bot.id if bot else False,
            'status': status,
            'error_message': error_message,
            'parse_mode': self.parse_mode,
            'message_type': 'document' if self.report_id else 'text',
            'company_id': self.env.company.id,
        })

    def _post_chatter(self, record, success_partners, failed_partners):
        """Post summary to the record's chatter."""
        lines = []
        if success_partners:
            names = ', '.join(p.name for p in success_partners)
            parts = []
            if self.message:
                parts.append(_('text'))
            if self.report_id:
                parts.append(_('PDF: %s') % self.report_id.name)
            if self.attachment_ids:
                parts.append(_('%d attachments') % len(self.attachment_ids))
            lines.append(_('✅ Telegram sent to: %s (%s)') % (names, ', '.join(parts)))

        if failed_partners:
            for partner, err in failed_partners:
                lines.append(_('❌ Telegram failed for %s: %s') % (partner.name, err))

        if lines:
            record.message_post(
                body='<br/>'.join(lines),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

    # ─── Webhook handler ───

    @api.model
    def _process_webhook_update(self, data):
        """Handle incoming Telegram webhook update."""
        message = data.get('message', {})
        if not message:
            return

        text = message.get('text', '')
        from_data = message.get('from', {})
        chat_data = message.get('chat', {})

        username = from_data.get('username', '').lower()
        chat_id = str(chat_data.get('id', ''))

        if not username or not chat_id:
            return

        if text.strip().startswith('/start'):
            partner = self.env['res.partner'].sudo().search(
                [('telegram_username', '=ilike', username)],
                limit=1,
            )
            if partner and partner.telegram_chat_id != chat_id:
                partner.write({'telegram_chat_id': chat_id})
                _logger.info(
                    'Telegram: chat_id %s mapped to partner %s (@%s)',
                    chat_id, partner.id, username,
                )
