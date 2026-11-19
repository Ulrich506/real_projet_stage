# -*- coding: utf-8 -*-

from odoo import models, api


class IrUiViewOfficier(models.AbstractModel):
    _name = "ir.ui.view.officier.hook"
    _description = "Hook pour créer les vues officier sans bouton Nouveau"

    @api.model
    def _register_hook(self):
        """Créer les vues tree sans bouton 'Nouveau' pour l'officier.

        Ces vues s'appliquent aux listes 'Dossiers à examiner' où l'officier
        ne doit pas pouvoir créer de nouveaux actes.
        """
        super()._register_hook()
        officier_group = self.env.ref("etat_civil.group_etat_civil_officier")

        views_to_create = [
            (
                "view_etat_civil_acte_naissance_tree_officier",
                "etat.civil.acte.naissance",
                "view_etat_civil_acte_naissance_tree",
            ),
            (
                "view_etat_civil_acte_mariage_tree_officier",
                "etat.civil.acte.mariage",
                "view_etat_civil_acte_mariage_tree",
            ),
            (
                "view_etat_civil_acte_deces_tree_officier",
                "etat.civil.acte.deces",
                "view_etat_civil_acte_deces_tree",
            ),
        ]

        for name, model, existing_name in views_to_create:
            # Vérifier si la vue existe déjà
            existing_view = self.env["ir.ui.view"].sudo().search(
                [("name", "=", name), ("model", "=", model)], limit=1
            )
            if existing_view:
                continue

            source_view = self.env.ref("etat_civil." + existing_name, raise_if_not_found=False)
            if not source_view:
                continue

            import lxml.etree as ET

            root = ET.fromstring(source_view.arch)
            root.set("create", "0")
            new_arch = ET.tostring(root, encoding="unicode")

            self.env["ir.ui.view"].sudo().create(
                {
                    "name": name,
                    "model": model,
                    "type": "tree",
                    "groups_id": [(4, officier_group.id)],
                    "arch": new_arch,
                }
            )

        # Mettre à jour les actions 'à examiner' pour utiliser les vues tree officier
        actions_to_update = [
            ("action_etat_civil_acte_naissance_a_valider",
             "view_etat_civil_acte_naissance_tree_officier"),
            ("action_etat_civil_acte_mariage_a_valider",
             "view_etat_civil_acte_mariage_tree_officier"),
            ("action_etat_civil_acte_deces_a_valider",
             "view_etat_civil_acte_deces_tree_officier"),
        ]

        for action_xmlid, view_xmlid in actions_to_update:
            action = self.env.ref(action_xmlid, raise_if_not_found=False)
            view = self.env.ref("etat_civil." + view_xmlid, raise_if_not_found=False)
            if action and view:
                action.sudo().write({"view_id": view.id})

        # S'assurer que les utilisateurs officier n'ont PAS le groupe agent.
        # Un officier avec le groupe agent voit les menus "File d'attente", "Actes"
        # et "Citoyens / Individus" qui ne lui sont pas destinés.
        agent_group = self.env.ref("etat_civil.group_etat_civil_agent")
        officiers = self.env["res.users"].search([
            ("groups_id", "in", officier_group.id),
            ("etat_civil_role", "=", "officier"),
        ])
        for user in officiers:
            if agent_group in user.groups_id:
                user.sudo().write({"groups_id": [(3, agent_group.id)]})
