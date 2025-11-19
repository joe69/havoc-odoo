from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)

SERVICE_FEE_PERCENTAGE = 0.05  # 5%


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _update_service_fee(self):
        """
        Berechnet und aktualisiert die Service-Gebühr für alle Event-Tickets.
        Erstellt EINE Service-Gebühr-Zeile für alle Tickets zusammen.
        """
        self.ensure_one()
        
        # Verhindere Rekursion
        if self.env.context.get('skip_service_fee_update'):
            return
        
        # Hole das Service-Gebühr Produkt
        service_fee_product = self.env.ref('event_service_fee.product_service_fee', raise_if_not_found=False)
        if not service_fee_product:
            _logger.warning("[SERVICE FEE] Service-Gebühr Produkt nicht gefunden!")
            return

        # Finde alle Event-Ticket Zeilen (Zeilen mit event_id oder event_ticket_id)
        event_lines = self.order_line.filtered(
            lambda l: (l.event_id or l.event_ticket_id) 
            and l.product_id.id != service_fee_product.id  # Keine Service-Gebühr selbst
        )

        # Finde existierende Service-Gebühr Zeile(n)
        existing_fee_lines = self.order_line.filtered(
            lambda l: l.product_id.id == service_fee_product.id
        )

        if not event_lines:
            # Keine Event-Tickets mehr vorhanden -> lösche Service-Gebühr
            if existing_fee_lines:
                _logger.info("[SERVICE FEE] Keine Event-Tickets mehr, lösche Service-Gebühr")
                existing_fee_lines.with_context(skip_service_fee_update=True).unlink()
            return

        # Berechne Gesamtpreis aller Event-Tickets
        total_event_price = sum(line.price_unit * line.product_uom_qty for line in event_lines)
        
        # Berechne Service-Gebühr (5%)
        service_fee_amount = total_event_price * SERVICE_FEE_PERCENTAGE

        _logger.info(
            "[SERVICE FEE] Auftrag %s: %s Event-Tickets, Gesamt: €%.2f, Service-Gebühr: €%.2f",
            self.name, len(event_lines), total_event_price, service_fee_amount
        )

        if service_fee_amount == 0:
            # Keine Gebühr nötig
            if existing_fee_lines:
                existing_fee_lines.with_context(skip_service_fee_update=True).unlink()
            return

        # Erstelle oder aktualisiere Service-Gebühr Zeile
        if existing_fee_lines:
            # Behalte nur die erste Zeile, lösche alle anderen
            if len(existing_fee_lines) > 1:
                _logger.info("[SERVICE FEE] Mehrere Service-Gebühr Zeilen gefunden, behalte nur eine")
                existing_fee_lines[1:].with_context(skip_service_fee_update=True).unlink()
                existing_fee_lines = existing_fee_lines[0]
            else:
                existing_fee_lines = existing_fee_lines[0]

            # Aktualisiere bestehende Zeile
            existing_fee_lines.with_context(skip_service_fee_update=True).write({
                'product_uom_qty': 1,
                'price_unit': service_fee_amount,
            })
            _logger.info("[SERVICE FEE] Service-Gebühr aktualisiert: €%.2f", service_fee_amount)
        else:
            # Erstelle neue Service-Gebühr Zeile
            self.env['sale.order.line'].with_context(skip_service_fee_update=True).create({
                'order_id': self.id,
                'product_id': service_fee_product.id,
                'product_uom_qty': 1,
                'price_unit': service_fee_amount,
                'name': 'Service-Gebühr (5% auf Event-Tickets)',
            })
            _logger.info("[SERVICE FEE] Service-Gebühr erstellt: €%.2f", service_fee_amount)

    def write(self, vals):
        """Recalculate service fee when order is modified"""
        result = super().write(vals)
        
        # If order lines were modified, recalculate
        if 'order_line' in vals and self.state in ['draft', 'sent']:
            self._update_service_fee()
        
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Calculate service fee after order creation"""
        orders = super().create(vals_list)
        
        for order in orders:
            if order.state in ['draft', 'sent']:
                order._update_service_fee()
        
        return orders