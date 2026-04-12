==============================================
Telegram Integration Advanced — Documentation
==============================================

.. contents:: Table of Contents
   :depth: 2
   :local:

----

1. Getting Started
==================

Prerequisites
-------------

Before installing, make sure your environment meets these requirements:

.. warning::
   Telegram **only accepts HTTPS** webhook URLs.
   Your Odoo instance must be accessible via a public HTTPS domain.

+----------------------------+----------------------------------------------------------------+
| Requirement                | Description                                                    |
+============================+================================================================+
| ``web.base.url``           | Must be set to a **public HTTPS** domain                       |
|                            | (e.g. ``https://erp.yourcompany.com``)                         |
+----------------------------+----------------------------------------------------------------+
| Internet Access            | Domain must be reachable from Telegram servers (not localhost)  |
+----------------------------+----------------------------------------------------------------+
| SSL Certificate            | Valid HTTPS certificate (Let's Encrypt, Cloudflare, etc.)      |
+----------------------------+----------------------------------------------------------------+

.. tip::
   If you are developing locally, use `ngrok <https://ngrok.com>`_ to create
   a temporary HTTPS tunnel to your local Odoo instance.


Installation
------------

1. Upload the ``sm_telegram`` module folder to your server's **custom addons directory**.
2. **Restart** the Odoo service to detect the new module.
3. Navigate to **Apps** menu, click **Update Apps List**.
4. Search for **"Telegram Integration Advanced"** and click **Install**.

.. note::
   After installation, a new **Telegram** top-level menu will appear in the main menu bar.
   All bot management, templates, model configs, and message logs are accessible from there.

----

2. Creating a Bot
=================

To get started, you need to obtain an official Telegram Bot Token from BotFather.

Step 1: Talk to BotFather
-------------------------

1. Open Telegram on your phone or desktop.
2. Search for ``@BotFather`` and start a conversation.
3. Send the ``/newbot`` command.
4. Follow the instructions — choose a **name** and a **username** for your bot.
5. BotFather will provide you with a unique **API Token**.

.. important::
   **Keep your token secure!** Anyone with access to this token can control your bot.
   Never share it publicly or commit it to a public repository.

Step 2: Register Bot in Odoo
-----------------------------

1. Navigate to **Telegram → Bots → New**.
2. Fill in the following fields:

   :Token:
       Paste the API Token you received from BotFather.

   :Company:
       Select the company this bot belongs to. Each company can have its own bot.

3. Click the **Verify Bot** button.

   The system calls the Telegram ``getMe`` API to validate the token and automatically
   fetches the bot's **name** and **username**.

4. Click the **Setup Webhook** button.

   This registers your Odoo server URL with Telegram via the ``setWebhook`` API.
   A cryptographically secure **secret token** is auto-generated for webhook validation.

.. tip::
   You can see the bot status change to **Verified** and the webhook URL populated
   automatically. If verification fails, double-check your token and that ``web.base.url``
   is set correctly in **Settings → Technical → System Parameters**.

----

3. Model Configuration
======================

Before users can send Telegram messages from a specific model (e.g. Sale Order, Invoice),
an administrator must enable it.

Setup
-----

1. Navigate to **Telegram → Model Configuration → New**.
2. Configure the following fields:

   :Model:
       Select the Odoo model (e.g. ``sale.order``, ``account.move``, ``res.partner``).

   :Allowed Reports:
       Whitelist which QWeb PDF reports can be sent via Telegram for this model.
       If left empty, **all** PDF reports for the model are available.

   :Allowed Users:
       Optionally restrict which users can send Telegram messages for this model.
       If left empty, **all** users can send.

   :Default Template:
       Optionally select a template that will be **auto-loaded** when a user opens
       the send wizard for this model.

.. note::
   Once a model is configured, the **"Send Telegram"** button will automatically
   appear in the chatter of all records of that model.

----

4. Contact Mapping
==================

Telegram uses **chat IDs** to identify users. The module handles mapping automatically.

How It Works
------------

1. Your customer opens Telegram and searches for your bot (e.g. ``@YourCompanyBot``).
2. They send the ``/start`` command.
3. The webhook controller receives the update and automatically:

   - Extracts the Telegram **username** and **chat_id** from the message.
   - Searches for a ``res.partner`` with a matching ``telegram_username`` field.
   - Writes the ``telegram_chat_id`` on that partner record.

.. tip::
   To prepare contacts, set the **Telegram Username** field on partner records
   (found in the **Telegram** tab on the partner form). When the customer sends ``/start``,
   the mapping happens automatically — **zero manual work**.

Partner Fields
--------------

Two fields are added to ``res.partner``:

+----------------------------+----------------------------------------------------------------+
| Field                      | Description                                                    |
+============================+================================================================+
| ``telegram_username``      | The contact's Telegram username (without @)                    |
+----------------------------+----------------------------------------------------------------+
| ``telegram_chat_id``       | Auto-populated when the contact sends ``/start`` to the bot    |
+----------------------------+----------------------------------------------------------------+

----

5. Sending Messages
===================

From the Chatter
-----------------

1. Open any record (Sale Order, Invoice, Partner, etc.) that has a configured model.
2. In the chatter, click the **Send Telegram** button.
3. The **Send Wizard** opens with the following options:

   :Recipients:
       Select one or more partners who have a ``telegram_chat_id``.
       You can send to **up to 50 recipients** at once.

   :Template:
       Select a pre-configured template, or leave empty to write a custom message.
       If the model has a **default template**, it is auto-loaded.

   :Message:
       The message body. If a template is selected, it is rendered with Jinja2
       variables and pre-filled here. You can still edit it before sending.

   :Parse Mode:
       Choose between **Markdown**, **HTML**, or **Plain Text** formatting.

   :Report:
       Optionally attach a QWeb PDF report (only whitelisted reports are shown).

   :Attachments:
       Attach any ``ir.attachment`` files. Images are automatically sent as
       **Telegram photos**, other files as **documents**.

   :Scheduled Date:
       Leave empty to send **immediately**, or set a future date/time for
       **deferred delivery**.

4. Click **Send**.

.. tip::
   After sending, a summary is posted as a **chatter note** on the source
   document, showing which recipients succeeded and which failed.

----

6. Message Templates
====================

Templates let you create reusable, dynamic messages with variables and buttons.

Creating a Template
-------------------

1. Navigate to **Telegram → Templates → New**.
2. Configure the following:

   :Name:
       A descriptive name for the template (e.g. "Order Confirmation").

   :Model:
       The Odoo model this template applies to.

   :Body:
       The message body using **Jinja2** template syntax.

   :Parse Mode:
       Markdown or HTML for rich text formatting.

   :Report:
       Optionally attach a PDF report action — it auto-generates on send.

Available Variables
-------------------

These variables are available inside the template body:

+----------------------------+----------------------------------------------------------------+
| Variable                   | Description                                                    |
+============================+================================================================+
| ``{{ object }}``           | The source record (e.g. the Sale Order)                        |
+----------------------------+----------------------------------------------------------------+
| ``{{ object.name }}``      | Record name (e.g. ``SO001``)                                   |
+----------------------------+----------------------------------------------------------------+
| ``{{ partner }}``          | The recipient partner record                                   |
+----------------------------+----------------------------------------------------------------+
| ``{{ partner.name }}``     | Partner name                                                   |
+----------------------------+----------------------------------------------------------------+
| ``{{ company }}``          | Current company record                                         |
+----------------------------+----------------------------------------------------------------+
| ``{{ company.name }}``     | Company name                                                   |
+----------------------------+----------------------------------------------------------------+
| ``{{ user }}``             | Current user record                                            |
+----------------------------+----------------------------------------------------------------+
| ``{{ user.name }}``        | Current user name                                              |
+----------------------------+----------------------------------------------------------------+

**Example template body** (Markdown)::

   *Order Confirmation* 🎉

   Hello **{{ partner.name }}**,

   Your order **{{ object.name }}** has been confirmed!

   Total: {{ object.amount_total }} {{ object.currency_id.name }}

   Thank you for your business.
   — {{ company.name }}

Inline Keyboard Buttons
------------------------

Add clickable URL buttons that appear below the message in Telegram:

1. In the template form, go to the **Buttons** tab.
2. Click **Add a line** and fill in:

   :Label: The button text (e.g. "View Order")
   :URL: The destination URL
   :Row: Row number (buttons on the same row appear side by side)

.. tip::
   Use **Preview** to see exactly how the rendered message will look,
   and **Test Render** to validate Jinja2 syntax before sending.

----

7. Scheduling & Auto-Retry
===========================

Scheduled Messages
------------------

Instead of sending immediately, set a **scheduled date/time** in the send wizard.
The message will be saved with status **"scheduled"** and a background cron job
will process it when the time comes.

Auto-Retry for Failed Messages
-------------------------------

If a message fails to send (network error, Telegram API downtime, etc.),
the system can **automatically retry** it.

Configuration: Navigate to **Settings → General Settings → Telegram**.

+----------------------------+----------------------------------------------------------------+
| Setting                    | Description                                                    |
+============================+================================================================+
| **Default Bot**            | Auto-selected when sending if no specific bot is chosen        |
+----------------------------+----------------------------------------------------------------+
| **Enable Auto-Retry**      | Toggle automatic retry of failed messages on/off               |
+----------------------------+----------------------------------------------------------------+
| **Max Retry Count**        | Maximum number of retry attempts (default: 3)                  |
+----------------------------+----------------------------------------------------------------+

.. note::
   You can also **manually retry** any failed message from the
   **Telegram → Message Logs** view by clicking the **Retry** button.

----

8. Message Logs & Audit Trail
==============================

Every Telegram message (sent, failed, or scheduled) is recorded in the
**Telegram → Message Logs** view.

Log Fields
----------

+----------------------------+----------------------------------------------------------------+
| Field                      | Description                                                    |
+============================+================================================================+
| **Recipient**              | The partner the message was sent to                            |
+----------------------------+----------------------------------------------------------------+
| **Chat ID**                | The Telegram chat ID used                                      |
+----------------------------+----------------------------------------------------------------+
| **Status**                 | ``draft`` / ``sent`` / ``failed`` / ``scheduled``              |
+----------------------------+----------------------------------------------------------------+
| **Message**                | Full message content                                           |
+----------------------------+----------------------------------------------------------------+
| **Bot**                    | Which bot was used                                             |
+----------------------------+----------------------------------------------------------------+
| **Source Record**           | Link to the Odoo document that triggered the send             |
+----------------------------+----------------------------------------------------------------+
| **Template**               | Template used (if any)                                         |
+----------------------------+----------------------------------------------------------------+
| **Sent At / Scheduled At** | Timestamps                                                     |
+----------------------------+----------------------------------------------------------------+
| **Error**                  | Error message (for failed deliveries)                          |
+----------------------------+----------------------------------------------------------------+
| **Retry Count**            | Number of retry attempts                                       |
+----------------------------+----------------------------------------------------------------+

Chatter Audit Trail
-------------------

After every send operation, a **summary note** is automatically posted on the
chatter of the source document. The note includes:

- ✅ Recipients that received the message successfully
- ❌ Recipients that failed, with error details

----

9. Technical Architecture
=========================

End-to-End Flow
---------------

::

   ┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
   │  BotFather   │────▶│  Odoo Bot    │────▶│  setWebhook     │
   │  (get token) │     │  (verify)    │     │  (register URL) │
   └─────────────┘     └──────────────┘     └─────────────────┘
                                                      │
                        ┌──────────────────────────────┘
                        ▼
   ┌────────────────────────────────────┐
   │  /telegram/webhook/<secret>        │
   │  (controller receives updates)     │
   └────────────────────────────────────┘
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
   ┌─────────────────┐   ┌──────────────────┐
   │  /start command  │   │  Other messages   │
   │  (map chat_id)  │   │  (future use)     │
   └─────────────────┘   └──────────────────┘

   ┌─────────────────────────────────────────────────────┐
   │  Send Wizard (from chatter)                         │
   │  ┌─────────┐  ┌──────────┐  ┌─────────┐           │
   │  │ Message  │  │ Template │  │ Report  │           │
   │  │ (text)   │  │ (Jinja2) │  │ (PDF)   │           │
   │  └────┬─────┘  └────┬─────┘  └────┬────┘           │
   │       └──────────────┴─────────────┘                │
   │                      │                              │
   │              ┌───────┴───────┐                      │
   │              ▼               ▼                      │
   │     ┌──────────────┐ ┌──────────────┐              │
   │     │ Send Now     │ │ Schedule     │              │
   │     │ (Telegram    │ │ (cron job    │              │
   │     │  API call)   │ │  picks up)   │              │
   │     └──────┬───────┘ └──────┬───────┘              │
   │            └────────┬───────┘                       │
   │                     ▼                               │
   │          ┌─────────────────┐                        │
   │          │  Message Log    │                        │
   │          │  (audit trail)  │                        │
   │          └─────────────────┘                        │
   └─────────────────────────────────────────────────────┘

Models
------

+----------------------------------+--------------------------------------------------------+
| Model                            | Purpose                                                |
+==================================+========================================================+
| ``telegram.bot``                 | Bot configuration (token, webhook, company)            |
+----------------------------------+--------------------------------------------------------+
| ``telegram.model.config``        | Per-model access rules (reports, users, templates)     |
+----------------------------------+--------------------------------------------------------+
| ``telegram.template``            | Message templates with Jinja2 and inline buttons       |
+----------------------------------+--------------------------------------------------------+
| ``telegram.template.button``     | Inline keyboard buttons for templates                  |
+----------------------------------+--------------------------------------------------------+
| ``telegram.message.log``         | Message delivery log with status and retry tracking    |
+----------------------------------+--------------------------------------------------------+
| ``telegram.send.wizard``         | Transient model for the send wizard                    |
+----------------------------------+--------------------------------------------------------+

API Endpoints
-------------

+-----------------------------------------+-----------------------------------------------+
| Endpoint                                | Description                                   |
+=========================================+===============================================+
| ``/telegram/webhook/<secret>``          | Receives incoming Telegram webhook updates    |
+-----------------------------------------+-----------------------------------------------+

Cron Jobs
---------

+----------------------------------+--------------------------------------------------------+
| Cron                             | Description                                            |
+==================================+========================================================+
| Send Scheduled Messages          | Processes queued messages when their scheduled time     |
|                                  | has arrived                                            |
+----------------------------------+--------------------------------------------------------+
| Retry Failed Messages            | Retries failed messages up to the configured max       |
|                                  | retry count                                            |
+----------------------------------+--------------------------------------------------------+

----

Support
=======

We provide **free bug fixes and updates** for this module.

If you encounter any issues or need assistance:

1. Submit a support request through the **Odoo Apps support page**.
2. Our team (the same developers who built the module) will respond promptly.

.. important::
   Support is provided for **clean Odoo installations**. We cannot guarantee
   compatibility with heavily customized instances or conflicts with other
   third-party modules.
