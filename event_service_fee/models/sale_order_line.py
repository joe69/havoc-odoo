from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model_create_multi
    def create(self, vals_list):
        """Trigger service fee calculation after creating order lines"""
        lines = super().create(vals_list)
        
        # Skip if context flag is set (prevents recursion)
        if self.env.context.get('skip_service_fee_update'):
            return lines
        
        # Collect all affected orders
        orders = lines.mapped('order_id')
        for order in orders:
            # Only recalculate if order is not confirmed yet
            if order.state in ['draft', 'sent']:
                order._update_service_fee()
        
        return lines

    def write(self, vals):
        """Trigger service fee calculation after updating order lines"""
        result = super().write(vals)
        
        # Skip if context flag is set (prevents recursion)
        if self.env.context.get('skip_service_fee_update'):
            return result
        
        # Check if relevant fields were changed
        if any(field in vals for field in ['product_id', 'product_uom_qty', 'price_unit', 'event_id', 'event_ticket_id']):
            orders = self.mapped('order_id')
            for order in orders:
                # Only recalculate if order is not confirmed yet
                if order.state in ['draft', 'sent']:
                    order._update_service_fee()
        
        return result

    def unlink(self):
        """Trigger service fee calculation after deleting order lines"""
        orders = self.mapped('order_id')
        result = super().unlink()
        
        for order in orders:
            if order.exists() and order.state in ['draft', 'sent']:
                order._update_service_fee()
        
        return result