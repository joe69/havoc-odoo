# payment_country_fix/__manifest__.py
{
    "name": "Payment Country Fix",
    "version": "18.0.1.0.0",
    "summary": "Stellt sicher, dass beim Online-Payment immer ein gültiges Länderkürzel gesetzt ist.",
    "author": "Thomas & ChatGPT",
    "license": "LGPL-3",
    "depends": [
        "website_sale",
        "payment",
    ],
    "data": [],
    "installable": True,
    "application": False,
}
