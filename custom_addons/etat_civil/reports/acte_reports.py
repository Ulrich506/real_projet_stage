from odoo import _, api, models
from odoo.exceptions import AccessError, UserError


def _checked_records(env, model_name, docids):
    docids = list(docids or [])
    records = env[model_name].browse(docids).exists()
    if len(records) != len(docids):
        raise AccessError(_("Un ou plusieurs documents sont introuvables ou inaccessibles."))
    records.check_access_rights("read")
    records.check_access_rule("read")
    return records


class ReportEtatCivilActeNaissance(models.AbstractModel):
    _name = "report.etat_civil.report_acte_naissance"
    _description = "Extrait du registre des naissances"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = _checked_records(self.env, "etat.civil.acte.naissance", docids)
        for doc in docs:
            doc._ensure_competence_territoriale()
            if doc.statut not in ("valide", "rectifie"):
                raise UserError(
                    _("L'extrait officiel n'est disponible qu'après validation de l'acte.")
                )
            if (
                not doc.numero_acte
                or not doc.enfant_id.date_naissance
                or not doc.lieu_naissance
            ):
                raise UserError(_("L'acte de naissance validé ne contient pas les données requises pour l'extrait."))
            if doc.hash_empreinte_num and not doc.verify_integrity_hash()[0]:
                raise UserError(_("L'empreinte de l'acte ne correspond plus à son contenu; impression bloquée."))
        for doc in docs:
            self.env["etat.civil.audit.log"]._record_event("print", record=doc)
        return {
            "doc_ids": docs.ids,
            "doc_model": docs._name,
            "docs": docs,
            "copy_request": False,
        }


class ReportEtatCivilActeMariage(models.AbstractModel):
    _name = "report.etat_civil.report_acte_mariage"
    _description = "Extrait du registre des mariages"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = _checked_records(self.env, "etat.civil.acte.mariage", docids)
        for doc in docs:
            doc._ensure_competence_territoriale()
            if doc.statut in ("valide", "rectifie"):
                if (
                    not doc.numero_acte
                    or not doc.date_mariage
                    or not doc.lieu_mariage
                    or not doc.conjoint_1_id
                    or not doc.conjoint_2_id
                ):
                    raise UserError(_("L'acte de mariage validé ne contient pas les données requises pour l'extrait."))
                if (
                    not doc.donnees_historiques_incompletes
                    and (not doc.temoin_1_id or not doc.temoin_2_id)
                ):
                    raise UserError(_("Les témoins manquent dans l'acte de mariage validé."))
                if doc.hash_empreinte_num and not doc.verify_integrity_hash()[0]:
                    raise UserError(_("L'empreinte de l'acte ne correspond plus à son contenu; impression bloquée."))
        for doc in docs:
            self.env["etat.civil.audit.log"]._record_event("print", record=doc)
        return {
            "doc_ids": docs.ids,
            "doc_model": docs._name,
            "docs": docs,
            "copy_request": False,
        }


class ReportEtatCivilActeDeces(models.AbstractModel):
    _name = "report.etat_civil.report_acte_deces"
    _description = "Extrait du registre des décès"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = _checked_records(self.env, "etat.civil.acte.deces", docids)
        for doc in docs:
            doc._ensure_competence_territoriale()
            if doc.statut in ("valide", "rectifie"):
                if (
                    not doc.numero_acte
                    or not doc.date_deces
                    or not doc.lieu_deces
                    or not doc.defunt_id
                    or not doc.declarant_id
                ):
                    raise UserError(_("L'acte de décès validé ne contient pas les données requises pour l'extrait."))
                if doc.hash_empreinte_num and not doc.verify_integrity_hash()[0]:
                    raise UserError(_("L'empreinte de l'acte ne correspond plus à son contenu; impression bloquée."))
        for doc in docs:
            self.env["etat.civil.audit.log"]._record_event("print", record=doc)
        return {
            "doc_ids": docs.ids,
            "doc_model": docs._name,
            "docs": docs,
            "copy_request": False,
        }


class ReportEtatCivilMentionMarginale(models.AbstractModel):
    _name = "report.etat_civil.report_mention_marginale"
    _description = "Avis de mention marginale"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = _checked_records(self.env, "etat.civil.mention.marginale", docids)
        for doc in docs:
            doc._ensure_officier()
            doc._ensure_competence_territoriale()
            if doc.statut == "valide" and not (doc.name and doc.contenu and doc.date_mention):
                raise UserError(_("La mention validée ne contient pas les données requises pour l'avis."))
        for doc in docs:
            self.env["etat.civil.audit.log"]._record_event("print", record=doc)
        return {"doc_ids": docs.ids, "doc_model": docs._name, "docs": docs}
