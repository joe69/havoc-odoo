from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _ensure_partner_has_country(self):
        """
        Stellt sicher, dass der Partner IMMER ein Land hat (Default: AT)
        """
        partner = self.partner_invoice_id or self.partner_id
        
        if not partner.country_id:
            austria = self.env['res.country'].sudo().search([('code', '=', 'AT')], limit=1)
            if austria:
                partner.sudo().write({'country_id': austria.id})

    def _create_payment_transaction(self, **kwargs):
        """
        Wird VOR PayPal-Aufruf aufgerufen - AT setzen falls leer
        """
        self._ensure_partner_has_country()
        return super()._create_payment_transaction(**kwargs)

    def _get_payment_transaction_values(self):
        """
        Alternative Hook - wird auch vor Payment verwendet
        """
        self._ensure_partner_has_country()
        return super()._get_payment_transaction_values()