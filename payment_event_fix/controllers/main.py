from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request, route


class WebsiteSaleForceBilling(WebsiteSale):

    @route(['/shop/checkout'], type='http', auth='public', website=True)
    def checkout(self, **post):
        """
        Verhindert, dass Odoo den Rechnungs-/Adress-Schritt überspringt.
        Funktioniert ohne request.website.sale_get_order().
        """

        # Sale Order aus der Session holen (Standard bei Website Sale)
        sale_order_id = request.session.get('sale_order_id')
        order = request.env['sale.order'].sudo().browse(sale_order_id) if sale_order_id else request.env['sale.order']

        # Wenn kein Schritt übergeben wurde, mit 'address' starten
        if not post.get('step'):
            post['step'] = 'address'

        # Wenn Odoo direkt zu payment/confirm will, prüfen wir, ob eine Rechnungsadresse sauber gesetzt ist
        if post.get('step') in ('payment', 'confirm'):
            partner = getattr(order, 'partner_invoice_id', False)
            # Hier kannst du definieren, was "vollständige" Rechnungsadresse heißt
            if not partner or not partner.street or not partner.country_id:
                # zurück zum Adress-Schritt zwingen
                post['step'] = 'address'

        return super().checkout(**post)
