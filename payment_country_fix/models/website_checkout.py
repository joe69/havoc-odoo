# payment_country_fix/models/website_checkout.py
from odoo import models, api


class Website(models.Model):
    _inherit = "website"

    def _get_default_country_id_for_payment(self):
        """Ermittelt eine sinnvolle Default-Country-ID.
        Reihenfolge:
        1) Systemparameter 'payment_default_country_code' (ISO-2, z.B. 'AT')
        2) Firma-Land (env.company.country_id)
        3) Fallback: versucht 'AT'
        """
        Param = self.env["ir.config_parameter"].sudo()
        country_model = self.env["res.country"].sudo()

        # 1) Systemparameter prüfen
        code = Param.get_param("payment_default_country_code")
        if code:
            country = country_model.search(
                [("code", "=", code.upper())], limit=1)
            if country:
                return country.id

        # 2) Firmenland
        if self.env.company.country_id:
            return self.env.company.country_id.id

        # 3) Fallback (hier hart 'AT' – kannst du ändern)
        fallback = country_model.search([("code", "=", "AT")], limit=1)
        if fallback:
            return fallback.id

        # Wenn gar nichts gefunden wird, None zurückgeben
        return None

    def _checkout_form_save(self, mode, checkout, all_values):
        """Stellt sicher, dass beim Checkout immer ein gültiges Land gesetzt wird,
        damit der Zahlungsanbieter keinen 'False' Country-Code bekommt.
        """
        # checkout dict enthält die Werte, mit denen der Partner angelegt/geschrieben wird
        if not checkout.get("country_id"):
            default_country_id = self._get_default_country_id_for_payment()
            if default_country_id:
                checkout["country_id"] = default_country_id

        return super()._checkout_form_save(mode, checkout, all_values)
