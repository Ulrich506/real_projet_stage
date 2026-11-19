from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class EtatCivilImprimerActeWizard(models.TransientModel):
    _name = "etat.civil.imprimer.acte.wizard"
    _description = "Assistant d'impression d'acte depuis la fiche citoyen"

    individu_id = fields.Many2one(
        "etat.civil.individu",
        string="Citoyen",
        required=True,
        readonly=True,
    )

    # Acte de naissance
    has_naissance = fields.Boolean(
        string="Acte de naissance disponible",
        compute="_compute_actes_disponibles",
    )
    acte_naissance_id = fields.Many2one(
        "etat.civil.acte.naissance",
        string="Acte de naissance",
        compute="_compute_actes_disponibles",
        readonly=True,
    )

    # Acte de mariage
    has_mariage = fields.Boolean(
        string="Acte de mariage disponible",
        compute="_compute_actes_disponibles",
    )
    acte_mariage_ids = fields.Many2many(
        "etat.civil.acte.mariage",
        string="Actes de mariage disponibles",
        compute="_compute_actes_disponibles",
        readonly=True,
    )
    selected_mariage_id = fields.Many2one(
        "etat.civil.acte.mariage",
        string="Acte de mariage sélectionné",
    )

    # Acte de décès
    has_deces = fields.Boolean(
        string="Acte de décès disponible",
        compute="_compute_actes_disponibles",
    )
    acte_deces_id = fields.Many2one(
        "etat.civil.acte.deces",
        string="Acte de décès",
        compute="_compute_actes_disponibles",
        readonly=True,
    )

    # Sélection finale
    acte_type = fields.Selection(
        [
            ("naissance", "Acte de naissance"),
            ("mariage", "Acte de mariage"),
            ("deces", "Acte de décès"),
        ],
        string="Type d'acte à imprimer",
        required=False,
        readonly=True,
    )

    @api.depends("individu_id")
    def _compute_actes_disponibles(self):
        """Calculer les actes validés disponibles pour l'impression."""
        for record in self:
            individu = record.individu_id
            if not individu:
                record.has_naissance = False
                record.acte_naissance_id = False
                record.has_mariage = False
                record.acte_mariage_ids = False
                record.selected_mariage_id = False
                record.has_deces = False
                record.acte_deces_id = False
                record.acte_type = False
                continue

            # Acte de naissance — toujours disponible si un acte validé existe
            naissances = individu.acte_naissance_enfant_ids.filtered(
                lambda a: a.statut in ("valide", "rectifie", "archive")
            )
            record.has_naissance = bool(naissances)
            record.acte_naissance_id = naissances.sorted("id", reverse=True)[:1]

            # Actes de mariage — disponibles si la personne figure comme conjoint
            mariages = individu.acte_mariage_conjoint_1_ids | individu.acte_mariage_conjoint_2_ids
            mariages_valides = mariages.filtered(
                lambda a: a.statut in ("valide", "rectifie", "archive")
            )
            record.has_mariage = bool(mariages_valides)
            record.acte_mariage_ids = mariages_valides
            # Par défaut, sélectionner le plus récent
            mariages_sorted = mariages_valides.sorted("id", reverse=True)
            record.selected_mariage_id = mariages_sorted[:1] if mariages_sorted else False

            # Acte de décès — disponible si un acte de décès validé existe pour cet individu
            deces = individu.acte_deces_defunt_ids.filtered(
                lambda a: a.statut in ("valide", "rectifie", "archive")
            )
            record.has_deces = bool(deces)
            record.acte_deces_id = deces.sorted("id", reverse=True)[:1]

            # Définir le type par défaut : naissance en priorité, puis mariage, puis décès
            if record.has_naissance:
                record.acte_type = "naissance"
            elif record.has_mariage:
                record.acte_type = "mariage"
            elif record.has_deces:
                record.acte_type = "deces"
            else:
                record.acte_type = False

    def _check_agent_or_admin(self):
        """Vérifie que l'utilisateur est agent ou administrateur."""
        user = self.env.user
        is_agent = user.has_group("etat_civil.group_etat_civil_agent")
        is_admin = user.has_group("etat_civil.group_etat_civil_admin")
        if not (is_agent or is_admin):
            role_label = user.groups_id.mapped("name")
            role_str = ", ".join(role_label) if role_label else "Aucun"
            raise AccessError(
                "Impossible d'imprimer un acte : cette action est réservée aux agents "
                "et aux administrateurs d'état civil. "
                f"Votre profil actuel (« {role_str} ») ne permet pas cette opération. "
                "Demandez à un agent ou un administrateur d'effectuer l'impression."
            )

    def action_imprimer(self):
        """Lancer l'impression de l'acte sélectionné."""
        self._check_agent_or_admin()
        for record in self:
            if not record.acte_type:
                raise UserError(
                    "Aucun acte valide n'est disponible pour ce citoyen. "
                    "Vérifiez que l'acte a bien été enregistré et validé par l'officier."
                )

            acte = False
            acte_label = ""
            if record.acte_type == "naissance":
                acte = record.acte_naissance_id
                acte_label = "acte de naissance"
            elif record.acte_type == "mariage":
                acte = record.selected_mariage_id
                acte_label = "acte de mariage"
            elif record.acte_type == "deces":
                acte = record.acte_deces_id
                acte_label = "acte de décès"

            if not acte:
                raise UserError(
                    f"Aucun {acte_label} valide trouvé pour le citoyen "
                    f"« {record.individu_id.nom_complet} ». "
                    "Vérifiez que l'acte a bien été enregistré et validé."
                )

            # Vérifier que l'acte est bien validé (sécurité côté serveur)
            if acte.statut not in ("valide", "rectifie", "archive"):
                raise UserError(
                    f"Impossible d'imprimer cet {acte_label} : l'acte est actuellement "
                    f"dans l'état « {acte.statut} ». "
                    "Seuls les actes validés par l'officier peuvent être imprimés. "
                    "Attendez la validation ou contactez l'officier d'état civil."
                )

            # Tracer dans le journal d'audit
            self.env["etat.civil.audit.log"]._record_event(
                action_type="print",
                record=acte,
                details={
                    "source": "imprimer_acte_from_individu",
                    "individu_id": record.individu_id.id,
                    "individu_nom": record.individu_id.nom_complet,
                    "acte_type": acte_label,
                    "acte_numero": acte.numero_acte,
                    "acte_feuillet": acte.feuillet_numero,
                },
            )

            # Lancer l'impression via la méthode existante
            return acte.action_imprimer_acte()

        return True
