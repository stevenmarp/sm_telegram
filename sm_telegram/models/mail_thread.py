# -*- coding: utf-8 -*-
from odoo import models
from odoo.addons.mail.tools.discuss import Store


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _thread_to_store(self, store: Store, /, *, fields=None, request_list=None):
        super()._thread_to_store(store, fields=fields, request_list=request_list)
        if request_list:
            can_send = self.env['sm.telegram.model.config']._can_send_telegram(self._name)
            store.add(self, {'canSendTelegram': can_send}, as_thread=True)
