from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            _logger.info("[VIP SPLIT] Auftragsbestätigung für %s", order.name)

            # WICHTIG: Setze Context-Flag um Service-Gebühr Neuberechnung zu verhindern
            order = order.with_context(skip_service_fee_update=True)

            # Finde VIP Gold Ticket Zeilen
            vip_gold_product = self.env.ref('vip_ticket_split.product_vip_gold_ticket', raise_if_not_found=False)
            vip_gold_lines = order.order_line.filtered(
                lambda l: l.product_id.id == vip_gold_product.id
            ) if vip_gold_product else self.env['sale.order.line']

            # Finde VIP Ticket Zeilen
            vip_product = self.env.ref('vip_ticket_split.product_vip_ticket', raise_if_not_found=False)
            vip_lines = order.order_line.filtered(
                lambda l: l.product_id.id == vip_product.id
            ) if vip_product else self.env['sale.order.line']

            # Verarbeite VIP Gold Tickets
            if vip_gold_lines:
                _logger.info("[VIP SPLIT] %s VIP Gold Ticket Zeile(n) gefunden", len(vip_gold_lines))
                self._process_vip_lines(
                    vip_gold_lines, 
                    order,
                    'vip_ticket_split.product_vip_gold',
                    'vip_ticket_split.product_vip_gold_package',
                    'VIP GOLD'
                )

            # Verarbeite normale VIP Tickets
            if vip_lines:
                _logger.info("[VIP SPLIT] %s VIP Ticket Zeile(n) gefunden", len(vip_lines))
                self._process_vip_lines(
                    vip_lines,
                    order,
                    'vip_ticket_split.product_vip',
                    'vip_ticket_split.product_vip_package',
                    'VIP'
                )

        return super().action_confirm()

    def _process_vip_lines(self, lines, order, ticket_xml_id, package_xml_id, vip_type):
        """
        Verarbeitet VIP-Zeilen und splittet sie in Ticket + Package
        
        :param lines: Sale Order Lines die gesplittet werden sollen
        :param order: Der zugehörige Sale Order
        :param ticket_xml_id: Externe ID für das Ticket-Produkt (z.B. VIP GOLD)
        :param package_xml_id: Externe ID für das Package-Produkt (z.B. VIP GOLD PACKAGE)
        :param vip_type: Name des VIP-Typs für Logging (z.B. 'VIP GOLD')
        """
        # Lade die Ziel-Produkte
        ticket_product = self.env.ref(ticket_xml_id, raise_if_not_found=False)
        package_product = self.env.ref(package_xml_id, raise_if_not_found=False)

        if not ticket_product or not package_product:
            _logger.error(
                "[VIP SPLIT] Produkte nicht gefunden! Ticket: %s, Package: %s",
                ticket_xml_id, package_xml_id
            )
            return

        for line in lines:
            quantity = line.product_uom_qty
            _logger.info(
                "[VIP SPLIT] %s-Zeile gefunden: Produkt %s, Menge %s",
                vip_type, line.product_id.name, quantity
            )

            # Finde alle zugehörigen Registrierungen der ursprünglichen VIP-Zeile
            registrations = self.env['event.registration'].search([
                ('sale_order_line_id', '=', line.id)
            ])

            # Hole Event-Ticket aus der ursprünglichen Zeile
            event_ticket = None
            if line.event_id and line.event_ticket_id:
                event_ticket = line.event_ticket_id
                _logger.info("[VIP SPLIT] Event-Ticket gefunden: %s", event_ticket.name)
            elif line.event_id:
                # Fallback: Suche ein Ticket für dieses Event
                event_ticket = self.env['event.event.ticket'].search([
                    ('event_id', '=', line.event_id.id),
                ], limit=1)
                if event_ticket:
                    _logger.info("[VIP SPLIT] Event-Ticket per Suche gefunden: %s", event_ticket.name)

            if not event_ticket:
                _logger.warning(
                    "[VIP SPLIT] Kein Event-Ticket gefunden für %s-Zeile %s! Überspringe.",
                    vip_type, line.id
                )
                continue

            # Iteriere für jede gekaufte VIP-Einheit
            for i in range(int(quantity)):
                reg = None
                beschreibung_zusatz = ""

                # Hole die passende Registrierung für diese Iteration
                if i < len(registrations):
                    reg = registrations[i]
                    _logger.info(
                        "[VIP SPLIT] Bearbeite Registrierung: %s", reg.display_name
                    )

                    antworten = []
                    # Hole die Antworten aus der Registrierung für die Beschreibung
                    for ans in reg.registration_answer_choice_ids:
                        antwort = ans.value_answer_id.name or ''
                        antworten.append(f"T-Shirt - {antwort}")

                    if antworten:
                        beschreibung_zusatz = "\n" + "\n".join(antworten)

                # 1. Erstelle die neue Ticket-Zeile (z.B. VIP GOLD für €100)
                new_ticket_line = self.env['sale.order.line'].with_context(skip_service_fee_update=True).create({
                    'order_id': order.id,
                    'product_id': ticket_product.id,
                    'product_uom_qty': 1,
                    'event_id': event_ticket.event_id.id,
                    'event_ticket_id': event_ticket.id,
                })
                
                # Preis explizit nochmal setzen (nach Event-Zuweisung)
                # damit er nicht vom Event-Ticket überschrieben wird
                new_ticket_line.with_context(skip_service_fee_update=True).write({
                    'price_unit': ticket_product.list_price,
                })
                
                _logger.info(
                    "[VIP SPLIT] Neue %s Ticket-Zeile mit ID %s erstellt (Preis: €%.2f).",
                    vip_type, new_ticket_line.id, new_ticket_line.price_unit
                )

                # 2. Wenn eine Registrierung existiert, aktualisiere sie
                if reg:
                    reg.with_context(skip_service_fee_update=True).write({
                        'sale_order_line_id': new_ticket_line.id,
                        'event_ticket_id': event_ticket.id,
                    })
                    _logger.info(
                        "[VIP SPLIT] Registrierung %s auf neue Zeile %s umgebucht.",
                        reg.id, new_ticket_line.id
                    )

                # 3. Erstelle die Package-Zeile (z.B. VIP GOLD PACKAGE)
                package_line = self.env['sale.order.line'].with_context(skip_service_fee_update=True).create({
                    'order_id': order.id,
                    'product_id': package_product.id,
                    'product_uom_qty': 1,
                    'price_unit': package_product.list_price,  # Preis explizit setzen
                    'name': f"{package_product.name}{beschreibung_zusatz}",
                })
                _logger.info(
                    "[VIP SPLIT] %s Package-Zeile erstellt (Preis: €%.2f).", 
                    vip_type, package_line.price_unit
                )

            # Lösche die ursprüngliche VIP-Zeile
            line.with_context(skip_service_fee_update=True).unlink()
            _logger.info(
                "[VIP SPLIT] %s-Zeile ersetzt durch %s× Ticket & Package",
                vip_type, quantity
            )