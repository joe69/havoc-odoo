from odoo import models, api


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _ensure_partner_country(self):
        """
        Stellt sicher, dass Partner IMMER AT als Land hat
        """
        if self.partner_id and not self.partner_id.country_id:
            austria = self.env['res.country'].sudo().search([('code', '=', 'AT')], limit=1)
            if austria:
                self.partner_id.sudo().write({'country_id': austria.id})

    @api.model
    def create(self, vals):
        """
        AT setzen BEVOR Transaction erstellt wird
        """
        partner_id = vals.get('partner_id')
        if partner_id:
            partner = self.env['res.partner'].sudo().browse(partner_id)
            if not partner.country_id:
                austria = self.env['res.country'].sudo().search([('code', '=', 'AT')], limit=1)
                if austria:
                    partner.write({'country_id': austria.id})
        
        return super().create(vals)

    def _get_specific_rendering_values(self, processing_values):
        """
        AT setzen VOR jedem Payment Provider Call (PayPal, Stripe, etc.)
        """
        self._ensure_partner_country()
        return super()._get_specific_rendering_values(processing_values)

    def _send_payment_request(self):
        """
        AT setzen VOR Payment Request
        """
        self._ensure_partner_country()
        return super()._send_payment_request()