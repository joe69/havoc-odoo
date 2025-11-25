from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request, route


class WebsiteSaleForceBilling(WebsiteSale):

    @route(['/shop/address'], type='http', auth='public', website=True, sitemap=False)
    def address(self, **kw):
        """
        Verhindert das Überspringen des Adress-Schritts bei Events.
        Setzt try_skip_step=true auf false.
        """
        # Parameter zwingen auf false
        kw['try_skip_step'] = False
        
        return super().address(**kw)