Step 1: Create Bot in BotFather
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Open Telegram and search for **@BotFather**.
2. Send the ``/newbot`` command and follow the instructions.
3. Copy the generated API token.

Step 2: Register Bot in Odoo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Navigate to **Telegram → Bots → New**.
2. Paste your API token in the **Token** field.
3. Click **Verify Bot** — the bot name and username will be fetched automatically.
4. Click **Setup Webhook** — this registers your Odoo URL with Telegram so incoming messages are received.

Step 3: Configure Model Access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Go to **Telegram → Model Configuration → New**.
2. Select the Odoo model (e.g. Sale Order, Invoice, Purchase Order).
3. Set which **PDF reports** are allowed to be sent for this model.
4. Optionally restrict which **users** can send Telegram messages.
5. Optionally set a **default template** for quick message composition.

Step 4: Map Telegram Users (Automatic)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a Telegram user sends ``/start`` to your bot, the webhook controller automatically
maps their **Telegram username → chat_id** on the corresponding ``res.partner`` record.

No manual mapping needed.
