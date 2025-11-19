from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            _logger.info("[VIP SPLIT] Auftragsbestätigung für %s", order.name)

            # Finde alle Zeilen mit dem Produkt "VIP"
            vip_lines = order.order_line.filtered(
                lambda l: l.product_id.name == 'VIP')

            for line in vip_lines:
                quantity = line.product_uom_qty
                _logger.info(
                    "[VIP SPLIT] VIP-Zeile gefunden: Produkt %s, Menge %s", line.product_id.name, quantity)

                # Lade die Produkte, die erstellt werden sollen
                ticket_product = self.env.ref(
                    'vip_ticket_split.product_ticket')
                vip_package_product = self.env.ref(
                    'vip_ticket_split.product_vip_package')

                # Finde alle zugehörigen Registrierungen der ursprünglichen VIP-Zeile
                registrations = self.env['event.registration'].search([
                    ('sale_order_line_id', '=', line.id)
                ])

                # Finde das Event-Ticket, das den neuen Zeilen zugewiesen werden soll
                # ACHTUNG: Event-ID ist hier hartcodiert (id=3)
                event_ticket = self.env['event.event.ticket'].search([
                    ('event_id', '=', 3),
                ], limit=1)

                if not event_ticket:
                    _logger.warning(
                        "[VIP SPLIT] Kein Event-Ticket für Event mit ID 3 gefunden!")
                    continue

                # Iteriere für jede gekaufte VIP-Einheit
                for i in range(int(quantity)):
                    reg = None
                    beschreibung_zusatz = ""

                    # Hole die passende Registrierung für diese Iteration
                    if i < len(registrations):
                        reg = registrations[i]
                        _logger.info(
                            "[VIP SPLIT] Bearbeite Registrierung: %s", reg.display_name)

                        antworten = []
                        # Hole die Antworten aus der Registrierung für die Beschreibung
                        for ans in reg.registration_answer_choice_ids:
                            antwort = ans.value_answer_id.name or ''
                            antworten.append(f"T-Shirt - {antwort}")

                        if antworten:
                            beschreibung_zusatz = "\n" + "\n".join(antworten)

                    # --- ANPASSUNG START ---

                    # 1. Erstelle die neue Ticket-Zeile und speichere sie in einer Variable
                    new_ticket_line = self.env['sale.order.line'].create({
                        'order_id': order.id,
                        'product_id': ticket_product.id,
                        'product_uom_qty': 1,
                        'event_id': event_ticket.event_id.id,  # Besser die ID vom Ticket nehmen
                        'event_ticket_id': event_ticket.id,
                    })
                    _logger.info(
                        "[VIP SPLIT] Neue Ticket-Zeile mit ID %s erstellt.", new_ticket_line.id)

                    # 2. Wenn eine Registrierung existiert, aktualisiere sie, damit sie auf die neue Zeile verweist
                    if reg:
                        reg.write({
                            'sale_order_line_id': new_ticket_line.id,
                            'event_ticket_id': event_ticket.id,  # auch hier das Ticket aktualisieren
                        })
                        _logger.info(
                            "[VIP SPLIT] Registrierung %s auf neue Zeile %s umgebucht.", reg.id, new_ticket_line.id)

                    # --- ANPASSUNG ENDE ---

                    # Erstelle die VIP-Package-Zeile mit der Beschreibung (wie zuvor)
                    self.env['sale.order.line'].create({
                        'order_id': order.id,
                        'product_id': vip_package_product.id,
                        'product_uom_qty': 1,
                        'name': f"{vip_package_product.name}{beschreibung_zusatz}",
                    })

                # Lösche die ursprüngliche "VIP"-Zeile, nachdem alle neuen Zeilen erstellt wurden
                line.unlink()

                _logger.info(
                    "[VIP SPLIT - 2] VIP-Zeile ersetzt durch %s× Ticket & VIP-Package", quantity)

        return super().action_confirm()
