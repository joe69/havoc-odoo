{
    "name": "Event Service Fee",
    "version": "19.0.1.0.0",
    "depends": ["sale", "event_sale"],
    "author": "Thomas",
    "category": "Sales",
    "description": """
        Fügt automatisch eine 5% Service-Gebühr zu allen Event-Tickets hinzu.
        - Gilt nur für Produkte mit Veranstaltungsregistrierung
        - Eine Service-Gebühr-Position für alle Tickets zusammen
        - Automatische Berechnung und Aktualisierung
    """,
    "data": [
        "data/product_data.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}