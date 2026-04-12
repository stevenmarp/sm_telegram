# -*- coding: utf-8 -*-
{
    'name': 'Telegram Integration Advanced | All in One',
    'version': '18.0.1.0.1',
    'category': 'Productivity/Discuss',
    'summary': 'Send Telegram messages, PDFs, images & scheduled notifications from any Odoo record',
    'description': """
Telegram Integration Advanced
=============================
All-in-one Telegram integration for Odoo with premium features.

**Core Features:**
- Send Telegram messages from any record's chatter
- Send PDF reports as documents
- Send product images / attachments as photos
- Per-model configuration (allowed reports, users)
- Webhook auto-mapping (/start -> chat_id)
- Full message logging with status tracking

**Premium Features:**
- Message Templates with dynamic fields (Jinja2)
- Automated triggers via server actions
- Inline keyboard buttons (clickable URLs in messages)
- Markdown & HTML formatting support
- Scheduled messages (send later)
- Failed message auto-retry (cron)
- Multi-company bot support
- One-click webhook setup
- Message dashboard & analytics
    """,
    'author': 'Steven Marp',
    'depends': ['mail', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_data.xml',
        'views/res_partner_views.xml',
        'views/telegram_bot_views.xml',
        'views/telegram_model_config_views.xml',
        'views/telegram_template_views.xml',
        'views/telegram_message_log_views.xml',
        'views/telegram_menus.xml',
        'views/res_config_settings_views.xml',
        'wizard/telegram_send_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sm_telegram/static/src/chatter/web/chatter_patch.xml',
            'sm_telegram/static/src/chatter/web/chatter_patch.js',
        ],
    },
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
    'price': 96.69,
    'currency': 'USD',
}
