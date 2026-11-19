from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class EtatCivilCreerActeWizard(models.TransientModel):
    _name = "etat.civil.creer.acte.wizard"
    _description = "Assistant de création d'acte depuis la fiche citoyen"

    individu_id = fields.Many2one(
        "etat.civil.individu",
        string="Citoyen",
        required=True,
        readonly=True,
    )

    # Disponibilité des types d'acte
    can_create_naissance = fields.Boolean(
        string="Naissance disponible",
        compute="_compute_actes_disponibles",
    )
    can_create_mariage = fields.Boolean(
        string="Mariage disponible",
        compute="_compute_actes_disponibles",
    )
    can_create_deces = fields.Boolean(
        string="Décès disponible",
        compute="_compute_actes_disponibles",
    )

    # Sélection du type d'acte
    acte_type = fields.Selection(
        [
            ("naissance", "Acte de naissance"),
            ("mariage", "Acte de mariage"),
            ("deces", "Acte de décès"),
        ],
        string="Type d'acte à créer",
        required=False,
    )

    # Pour le mariage : rôle de l'individu (conjoint 1 ou conjoint 2)
    mariage_role = fields.Selection(
        [
            ("conjoint_1", "Premier conjoint"),
            ("conjoint_2", "Second conjoint"),
        ],
        string="Rôle dans le mariage",
        default="conjoint_1",
    )

    @api.depends("individu_id")
    def _compute_actes_disponibles(self):
        """Calculer les types d'acte créables pour cet individu."""
        for record in self:
            ind = record.individu_id
            if not ind:
                record.can_create_naissance = False
                record.can_create_mariage = False
                record.can_create_deces = False
                continue

            # Naissance : disponible si l'individu n'a pas déjà un acte de naissance
            record.can_create_naissance = bool(
                not ind.acte_naissance_enfant_ids.filtered(
                    lambda a: a.statut in ("brouillon", "transmis", "valide", "rectifie", "archive")
                )
            )

            # Mariage : disponible si l'individu est éligible (âge ≥ 18 ans, vivant, pas déjà marié avec acte valide)
            record.can_create_mariage = bool(
                ind.eligible_conjoint
                and ind.statut_vital == "vivant"
                and not ind.acte_mariage_conjoint_1_ids.filtered(
                    lambda a: a.statut in ("valide", "rectifie", "archive")
                )
                and not ind.acte_mariage_conjoint_2_ids.filtered(
                    lambda a: a.statut in ("valide", "rectifie", "archive")
                )
            )

            # Décès : disponible si l'individu n'a pas déjà un acte de décès
            record.can_create_deces = bool(
                not ind.acte_deces_defunt_ids.filtered(
                    lambda a: a.statut in ("brouillon", "transmis", "valide", "rectifie", "archive")
                )
            )

            # Définir le type par défaut
            if record.can_create_naissance:
                record.acte_type = "naissance"
            elif record.can_create_mariage:
                record.acte_type = "mariage"
            elif record.can_create_deces:
                record.acte_type = "deces"

    @api.onchange("acte_type")
    def _onchange_acte_type(self):
        """Masquer le choix du rôle si ce n'est pas un mariage."""
        if self.acte_type != "mariage":
            self.mariage_role = False

    def _check_agent_or_admin(self):
        """Vérifie que l'utilisateur est agent ou administrateur."""
        user = self.env.user
        is_agent = user.has_group("etat_civil.group_etat_civil_agent")
        is_admin = user.has_group("etat_civil.group_etat_civil_admin")
        if not (is_agent or is_admin):
            role_label = user.groups_id.mapped("name")
            role_str = ", ".join(role_label) if role_label else "Aucun"
            raise AccessError(
                "Impossible de créer un acte : cette action est réservée aux agents "
                "et aux administrateurs d'état civil. "
                f"Votre profil actuel (« {role_str} ») ne permet pas cette opération. "
                "Demandez à un agent ou un administrateur d'effectuer cette action."
            )

    def action_creer_acte(self):
        """Ouvrir le formulaire de création d'acte avec l'individu pré-sélectionné."""
        self._check_agent_or_admin()
        for record in self:
            ind = record.individu_id

            if record.acte_type == "naissance":
                # Vérifier qu'il n'a pas déjà un acte de naissance
                naissance_existante = ind.acte_naissance_enfant_ids.filtered(
                    lambda a: a.statut in ("brouillon", "transmis", "valide", "rectifie", "archive")
                )
                if naissance_existante:
                    raise UserError(
                        f"Impossible de créer un acte de naissance pour « {ind.nom_complet} » : "
                        f"un acte de naissance existe déjà (N° {naissance_existante[:1].numero_acte}, état « {naissance_existante[:1].statut} »). "
                        "Un second acte de naissance n'est pas autorisé."
                    )

                # Ouvrir le formulaire de naissance avec l'individu comme enfant
                return {
                    "type": "ir.actions.act_window",
                    "name": "Créer un acte de naissance",
                    "res_model": "etat.civil.acte.naissance",
                    "view_mode": "form",
                    "target": "current",
                    "context": {
                        "default_enfant_id": ind.id,
                    },
                }

            elif record.acte_type == "mariage":
                # Vérifications supplémentaires pour le mariage
                if ind.statut_vital != "vivant":
                    raise UserError(
                        f"Impossible de créer un acte de mariage pour « {ind.nom_complet} » : "
                        f"ce citoyen a le statut vital « {dict(ind._fields['statut_vital'].selection).get(ind.statut_vital, ind.statut_vital)} ». "
                        "Seul un citoyen vivant peut contracter un mariage."
                    )
                if not ind.eligible_conjoint:
                    raise UserError(
                        f"Impossible de créer un acte de mariage pour « {ind.nom_complet} » : "
                        "cet individu n'est pas éligible (âge inférieur à 18 ans ou date de naissance manquante). "
                        "L'âge minimum légal pour se marier est de 18 ans."
                    )
                # Vérifier qu'il n'a pas déjà un mariage valide
                mariages_valides = (ind.acte_mariage_conjoint_1_ids | ind.acte_mariage_conjoint_2_ids).filtered(
                    lambda a: a.statut in ("valide", "rectifie", "archive")
                )
                if mariages_valides:
                    raise UserError(
                        f"Impossible de créer un acte de mariage pour « {ind.nom_complet} » : "
                        f"ce citoyen figure déjà dans un acte de mariage valide (N° {mariages_valides[:1].numero_acte}). "
                        "Un second mariage n'est pas autorisé tant que le premier n'est pas dissous."
                    )

                # Ouvrir le formulaire de mariage avec l'individu pré-sélectionné
                role = record.mariage_role or "conjoint_1"
                return {
                    "type": "ir.actions.act_window",
                    "name": "Créer un acte de mariage",
                    "res_model": "etat.civil.acte.mariage",
                    "view_mode": "form",
                    "target": "current",
                    "context": {
                        f"default_{role}": ind.id,
                    },
                }

            elif record.acte_type == "deces":
                # Vérifier qu'il n'a pas déjà un acte de décès
                deces_existant = ind.acte_deces_defunt_ids.filtered(
                    lambda a: a.statut in ("brouillon", "transmis", "valide", "rectifie", "archive")
                )
                if deces_existant:
                    raise UserError(
                        f"Impossible de créer un acte de décès pour « {ind.nom_complet} » : "
                        f"un acte de décès existe déjà (N° {deces_existant[:1].numero_acte}, état « {deces_existant[:1].statut} »). "
                        "Un second acte de décès n'est pas autorisé."
                    )

                # Ouvrir le formulaire de décès avec l'individu comme défunt
                return {
                    "type": "ir.actions.act_window",
                    "name": "Créer un acte de décès",
                    "res_model": "etat.civil.acte.deces",
                    "view_mode": "form",
                    "target": "current",
                    "context": {
                        "default_defunt_id": ind.id,
                    },
                }

        return True
