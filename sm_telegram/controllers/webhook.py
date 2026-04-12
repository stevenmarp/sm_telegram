# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TelegramWebhookController(http.Controller):

    @http.route(
        '/telegram/webhook/<string:secret_token>',
        methods=['POST'],
        type='http',
        auth='public',
        csrf=False,
    )
    def webhook(self, secret_token, **kwargs):
        """
        Receive Telegram webhook updates.
        Validates secret token against configured bots.
        Currently handles /start command for chat_id auto-mapping.
        """
        # Find the bot with this webhook secret
        bot = request.env['sm.telegram.bot'].sudo().search([
            ('webhook_secret', '=', secret_token),
            ('active', '=', True),
        ], limit=1)

        if not bot:
            _logger.warning('Telegram webhook: invalid secret token')
            return request.make_response('Forbidden', status=403)

        try:
            data = json.loads(request.httprequest.data)
        except Exception:
            _logger.warning('Telegram webhook: invalid JSON body')
            return request.make_response('Bad Request', status=400)

        try:
            request.env['sm.telegram.send.wizard'].sudo()._process_webhook_update(data)
        except Exception:
            _logger.exception('Telegram webhook: error processing update')

        return request.make_response('OK', status=200)
