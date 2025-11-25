from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request, route


class WebsiteSaleForceBilling(WebsiteSale):

    @route(['/shop/checkout'], type='http', auth='public', website=True)
    def checkout(self, **post):
        """
        Verhindert, dass Odoo 19 die Rechnungsadresse automatisch überspringt.
        Der Checkout beginnt immer mit dem Step 'address'.
        """
        order = request.website.sale_get_order()

        # Wenn Bestellung existiert, immer address-Step erzwingen
        if order:
            post['step'] = 'address'

        return super().checkout(**post)
