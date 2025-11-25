from odoo import models, api


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def create(self, vals):
        """
        Stellt sicher, dass Partner IMMER ein Land hat bevor PayPal-Transaction erstellt wird
        """
        # Partner aus vals oder sale_order holen
        partner_id = vals.get('partner_id')
        sale_order_id = vals.get('sale_order_ids')
        
        if partner_id:
            partner = self.env['res.partner'].sudo().browse(partner_id)
        elif sale_order_id:
            order = self.env['sale.order'].sudo().browse(sale_order_id[0][2][0] if sale_order_id else False)
            partner = order.partner_invoice_id or order.partner_id if order else False
        else:
            partner = False
        
        # AT setzen falls kein Land
        if partner and not partner.country_id:
            austria = self.env['res.country'].sudo().search([('code', '=', 'AT')], limit=1)
            if austria:
                partner.sudo().write({'country_id': austria.id})
        
        return super().create(vals)

    def _get_specific_rendering_values(self, processing_values):
        """
        Wird direkt vor PayPal-API-Call aufgerufen
        """
        res = super()._get_specific_rendering_values(processing_values)
        
        # Partner-Land nochmal prüfen
        if self.partner_id and not self.partner_id.country_id:
            austria = self.env['res.country'].sudo().search([('code', '=', 'AT')], limit=1)
            if austria:
                self.partner_id.sudo().write({'country_id': austria.id})
        
        return res