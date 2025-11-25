from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request, route


class WebsiteSaleForceBilling(WebsiteSale):

    def _check_address_is_complete(self, order, mode):
        """
        Überschreibt die Prüfung, ob Adresse vollständig ist.
        Bei Events IMMER false zurückgeben, damit Adress-Schritt nicht übersprungen wird.
        """
        # Prüfen ob Order Event-Tickets enthält
        has_event = any(line.event_id for line in order.order_line if hasattr(line, 'event_id'))
        
        if has_event:
            # Bei Events: Adresse ist NIEMALS vollständig -> Schritt nicht überspringen
            return False
        
        # Für normale Produkte: Original-Logik
        return super()._check_address_is_complete(order, mode)