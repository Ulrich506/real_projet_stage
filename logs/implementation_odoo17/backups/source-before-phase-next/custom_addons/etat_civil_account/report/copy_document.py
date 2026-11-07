from odoo import _, models
from odoo.exceptions import AccessError, UserError


class CopyDocumentReport(models.AbstractModel):
    _name = "report.etat_civil_account.copy_document"
    _description = "Rapport sécurisé de délivrance de copie"

    def _get_report_values(self, docids, data=None):
        requests = self.env["etat.civil.copy.request"].browse(docids).exists()
        if len(requests) != len(docids):
            raise AccessError(_("Demande de copie inaccessible."))
        requests.check_access_rights("read")
        requests.check_access_rule("read")
        for request in requests:
            request._check_center_access()
            if request.state not in ("authorized", "delivered"):
                raise UserError(_("Le document n'est pas autorisé à la délivrance."))
            if not request.is_free and not request._payment_is_satisfied():
                raise UserError(_("Le paiement n'est pas confirmé; accès au document bloqué."))
            request._selected_act()
        return {"doc_ids": requests.ids, "doc_model": requests._name, "docs": requests}

