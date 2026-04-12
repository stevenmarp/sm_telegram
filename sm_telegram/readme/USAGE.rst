Sending Messages
~~~~~~~~~~~~~~~~~

1. Open any document that has a chatter (Sale Order, Invoice, Partner, etc.).
2. Click the **Send Telegram** button in the chatter.
3. In the wizard:

   - Select **recipients** (partners with Telegram chat_id).
   - Write your **message** or select a **template**.
   - Optionally attach a **PDF report** or **files**.
   - Choose to **send now** or **schedule for later**.

4. Click **Send** — the message is delivered instantly via Telegram API.

Using Templates
~~~~~~~~~~~~~~~~

1. Go to **Telegram → Templates → New**.
2. Write your message body using **Jinja2** variables:

   - ``{{ object.name }}`` — record name
   - ``{{ partner.name }}`` — partner name
   - ``{{ company.name }}`` — company name

3. Set **parse mode** (Markdown or HTML) for rich text formatting.
4. Add **inline keyboard buttons** with clickable URLs (e.g. "View Order", "Contact Us").

Scheduling Messages
~~~~~~~~~~~~~~~~~~~~

- In the send wizard, set a **scheduled date/time** instead of sending immediately.
- A background **cron job** processes scheduled messages at the configured interval.
- Failed messages are **automatically retried** by the same cron.

Message Logs
~~~~~~~~~~~~~

- Every sent message is logged in **Telegram → Message Logs**.
- Track delivery **status**: draft, sent, failed, scheduled.
- View the full **message content**, recipient, timestamp, and error details.
- Messages are also logged as **chatter notes** on the source document.

Technical Flow
~~~~~~~~~~~~~~~

1. Bot verification via ``getMe`` API call.
2. Webhook registration via ``setWebhook``.
3. Incoming updates handled at ``/telegram/webhook/<secret>``.
4. ``/start`` command maps Telegram username → chat_id on ``res.partner``.
5. Send wizard composes payload: text, template, PDF report, or file attachments.
6. Message sent immediately or queued for scheduled delivery.
7. Background cron processes scheduled messages & retries failed ones.
8. Full audit trail via chatter notes + dedicated message log records.
