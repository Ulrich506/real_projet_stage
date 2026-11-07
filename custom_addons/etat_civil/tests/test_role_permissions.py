from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEtatCivilRolePermissions(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agent_group = cls.env.ref("etat_civil.group_etat_civil_agent")
        cls.officer_group = cls.env.ref("etat_civil.group_etat_civil_officier")
        cls.admin_group = cls.env.ref("etat_civil.group_etat_civil_admin")
        cls.agent = cls.env["res.users"].create(
            {
                "name": "Role test agent",
                "login": "role-test-agent",
                "email": "role-agent@example.test",
                "groups_id": [(6, 0, [cls.agent_group.id])],
            }
        )
        cls.officer = cls.env["res.users"].create(
            {
                "name": "Role test officer",
                "login": "role-test-officer",
                "email": "role-officer@example.test",
                "groups_id": [(6, 0, [cls.officer_group.id])],
            }
        )
        cls.admin = cls.env["res.users"].create(
            {
                "name": "Role test admin",
                "login": "role-test-admin",
                "email": "role-admin@example.test",
                "groups_id": [(6, 0, [cls.admin_group.id])],
            }
        )

    def _create_birth_act(self, user=None, suffix=""):
        user = user or self.agent
        centre = self.env["etat.civil.centre"].sudo().create(
            {
                "code_centre": f"ROLE-TEST{suffix}",
                "nom_centre": f"Centre de test des rôles {suffix}".strip(),
                "commune": "Commune de test",
            }
        )
        registre = self.env["etat.civil.registre"].sudo().create(
            {
                "annee": 2026,
                "type_registre": "naissance",
                "numero_volume": 1,
                "centre_id": centre.id,
            }
        )
        self.agent.sudo().write({"etat_civil_centre_ids": [(4, centre.id)]})
        self.officer.sudo().write({"etat_civil_centre_ids": [(4, centre.id)]})
        self.agent.invalidate_recordset(["etat_civil_centre_ids"])
        self.officer.invalidate_recordset(["etat_civil_centre_ids"])
        enfant = self.env["etat.civil.individu"].with_user(user).create(
            {
                "nom": "Enfant",
                "sexe": "M",
                "date_naissance": "2026-01-01",
            }
        )
        mere = self.env["etat.civil.individu"].with_user(user).create(
            {
                "nom": "Mère",
                "sexe": "F",
                "date_naissance": "2000-01-01",
            }
        )
        return self.env["etat.civil.acte.naissance"].with_user(user).create(
            {
                "numero_acte": "ROLE-1",
                "feuillet_numero": 1,
                "registre_id": registre.id,
                "texte_integral_acte": "Brouillon de test",
                "lieu_naissance": "Commune de test",
                "enfant_id": enfant.id,
                "mere_id": mere.id,
            }
        )

    def _transmit_as_admin(self, acte):
        admin_acte = acte.with_user(self.admin)
        admin_acte.piece_ids.write({"etat": "recu"})
        self.env["etat.civil.transmission.acte.wizard"].with_user(
            self.admin
        ).create(
            {
                "acte_type": "naissance",
                "acte_id": acte.id,
                "acte_display": acte.display_name,
                "centre_id": acte.registre_id.centre_id.id,
                "officier_id": self.officer.id,
            }
        ).action_confirmer_transmission()

    def _validate_as_admin(self, acte):
        admin_acte = acte.with_user(self.admin)
        self._transmit_as_admin(acte)
        admin_acte.piece_ids.write({"etat": "verifie"})
        admin_acte.action_valider_acte()

    def test_act_numbers_and_page_numbers_are_defaulted_by_act_type(self):
        centre = self.env["etat.civil.centre"].sudo().create(
            {
                "code_centre": "NUM-SEQ-TEST",
                "nom_centre": "Centre de test des séquences",
                "commune": "Commune de test",
            }
        )
        for type_registre, model_name, prefix in (
            ("mariage", "etat.civil.acte.mariage", "MAR/"),
            ("deces", "etat.civil.acte.deces", "DEC/"),
        ):
            registre = self.env["etat.civil.registre"].sudo().create(
                {
                    "annee": 2026,
                    "type_registre": type_registre,
                    "numero_volume": 1,
                    "centre_id": centre.id,
                }
            )
            draft = self.env[model_name].sudo().create(
                {
                    "registre_id": registre.id,
                    "texte_integral_acte": "Brouillon de test",
                    **(
                        {
                            "conjoint_1_id": self._create_person("Conjoint 1", "M", "1980-01-01").id,
                            "conjoint_2_id": self._create_person("Conjoint 2", "F", "1981-01-01").id,
                            "temoin_1_id": self._create_person("Témoin 1", "M", "1970-01-01").id,
                            "temoin_2_id": self._create_person("Témoin 2", "F", "1971-01-01").id,
                            "date_mariage": "2001-01-01",
                            "lieu_mariage": "Commune de test",
                            "regime_matrimonial": "communaute_biens",
                        }
                        if type_registre == "mariage"
                        else {
                            "defunt_id": self._create_person("Défunt", "M", "1960-01-01").id,
                            "declarant_id": self._create_person("Déclarant", "F", "1980-01-01").id,
                            "date_deces": "2000-01-01",
                            "lieu_deces": "Commune de test",
                        }
                    ),
                }
            )
            self.assertTrue(draft.numero_acte.startswith(prefix))
            self.assertEqual(draft.feuillet_numero, 1)

    def _create_person(self, name, sex, birth_date):
        return self.env["etat.civil.individu"].sudo().create(
            {
                "nom": name,
                "sexe": sex,
                "date_naissance": birth_date,
            }
        )

    def _transmit_birth_act(self, acte):
        acte.piece_ids.with_user(self.agent).write({"etat": "recu"})
        acte.with_user(self.agent).action_envoyer_validation(officier=self.officer)

    def test_manual_act_number_is_preserved_and_folio_increments_per_register(self):
        first_act = self._create_birth_act()
        self.assertEqual(first_act.numero_acte, "ROLE-1")
        self.assertEqual(first_act.feuillet_numero, 1)

        enfant = self.env["etat.civil.individu"].with_user(self.agent).create(
            {
                "nom": "Deuxième enfant",
                "sexe": "F",
                "date_naissance": "2026-02-01",
            }
        )
        second_act = self.env["etat.civil.acte.naissance"].with_user(self.agent).create(
            {
                "registre_id": first_act.registre_id.id,
                "texte_integral_acte": "Deuxième brouillon de test",
                "lieu_naissance": "Commune de test",
                "enfant_id": enfant.id,
                "mere_id": first_act.mere_id.id,
            }
        )
        self.assertTrue(second_act.numero_acte.startswith("NAI/"))
        self.assertEqual(second_act.feuillet_numero, 2)

    def test_agent_transmits_to_the_assigned_officer(self):
        acte = self._create_birth_act()
        self._transmit_birth_act(acte)

        self.assertEqual(acte.statut, "en_attente")
        self.assertEqual(acte.officier_validateur_id, self.officer)
        self.assertEqual(acte.agent_transmetteur_id, self.agent)
        self.assertTrue(acte.date_transmission)

    def test_admin_has_full_act_workflow_without_officer_membership(self):
        self.assertTrue(self.admin.has_group("etat_civil.group_etat_civil_agent"))
        self.assertFalse(self.admin.has_group("etat_civil.group_etat_civil_officier"))
        self.assertFalse(self.admin.has_group("base.group_system"))

        acte = self._create_birth_act(user=self.admin, suffix="-ADMIN-CREATE")
        acte.write({"texte_integral_acte": "Brouillon créé et modifié par l'administrateur."})
        self.assertEqual(acte.create_uid, self.admin)

        deletable_acte = self._create_birth_act(
            user=self.admin,
            suffix="-ADMIN-DELETE",
        )
        deletable_acte.unlink()
        self.assertFalse(deletable_acte.exists())

        self._validate_as_admin(acte)
        self.assertEqual(acte.statut, "valide")
        self.assertEqual(acte.officier_validateur_id, self.officer)
        self.assertEqual(acte.utilisateur_validation_id, self.admin)
        with self.assertRaises(UserError):
            acte.unlink()

    def test_admin_can_process_decisions_without_territorial_assignment(self):
        correction_act = self._create_birth_act(
            user=self.admin,
            suffix="-ADMIN-CORRECTION",
        )
        self._transmit_as_admin(correction_act)
        self.env["etat.civil.retour.correction.wizard"].with_user(
            self.admin
        ).create(
            {
                "action_type": "correction",
                "acte_type": "naissance",
                "acte_id": correction_act.id,
                "acte_display": correction_act.display_name,
                "motif": "Compléter le dossier.",
            }
        ).action_confirmer()
        self.assertEqual(correction_act.statut, "a_corriger")

        refusal_act = self._create_birth_act(
            user=self.admin,
            suffix="-ADMIN-REFUS",
        )
        self._transmit_as_admin(refusal_act)
        refusal_act.with_user(self.admin).action_refuser_acte("Dossier non conforme.")
        self.assertEqual(refusal_act.statut, "annule")
        self.assertIn("Dossier non conforme", refusal_act.motif_annulation)

        annulled_act = self._create_birth_act(suffix="-ADMIN-ANNULATION")
        self._validate_as_admin(annulled_act)
        self.env["etat.civil.annulation.acte.wizard"].with_user(
            self.admin
        ).create(
            {
                "acte_type": "naissance",
                "acte_id": annulled_act.id,
                "acte_display": annulled_act.display_name,
                "motif": "Erreur matérielle.",
            }
        ).action_confirmer()
        self.assertEqual(annulled_act.statut, "annule")
        annulled_act.with_user(self.admin).action_archiver_acte()
        self.assertEqual(annulled_act.statut, "archive")

        rectified_act = self._create_birth_act(
            user=self.admin,
            suffix="-ADMIN-RECTIFICATION",
        )
        self._validate_as_admin(rectified_act)
        rectified_act.with_user(self.admin).action_rectifier_acte()
        self.assertEqual(rectified_act.statut, "rectifie")

    def test_admin_can_manage_mentions_and_read_across_centres(self):
        first_act = self._create_birth_act(suffix="-ADMIN-CENTRE-1")
        second_act = self._create_birth_act(
            user=self.admin,
            suffix="-ADMIN-CENTRE-2",
        )
        visible_ids = self.env["etat.civil.acte.naissance"].with_user(self.admin).search(
            [("id", "in", [first_act.id, second_act.id])]
        ).ids
        self.assertEqual(set(visible_ids), {first_act.id, second_act.id})

        mention = self.env["etat.civil.mention.marginale"].with_user(self.admin).create(
            {
                "type_mention": "autre",
                "contenu": "Mention créée par un administrateur sans affectation locale.",
                "acte_naissance_id": first_act.id,
            }
        )
        mention.action_valider_mention()
        self.assertEqual(mention.statut, "valide")

    def test_admin_can_create_centres_registers_and_admin_users(self):
        centre = self.env["etat.civil.centre"].with_user(self.admin).create(
            {
                "code_centre": "ROLE-ADMIN-CRUD",
                "nom_centre": "Centre créé par l'administrateur",
                "commune": "Commune de test",
            }
        )
        centre.with_user(self.admin).write({"commune": "Commune modifiée"})
        registre = self.env["etat.civil.registre"].with_user(self.admin).create(
            {
                "annee": 2026,
                "type_registre": "naissance",
                "numero_volume": 1,
                "centre_id": centre.id,
            }
        )
        self.assertEqual(registre.centre_id, centre)

        wizard = self.env["etat.civil.gestion.utilisateur"].with_user(
            self.admin
        ).create(
            {
                "mode": "create",
                "name": "Nouvel administrateur État Civil",
                "login": "new-role-test-admin",
                "new_user_role": "admin",
                "password": "test-password",
            }
        )
        wizard.action_save()
        new_admin = self.env["res.users"].sudo().search(
            [("login", "=", "new-role-test-admin")], limit=1
        )
        self.assertTrue(new_admin.has_group("etat_civil.group_etat_civil_admin"))
        self.assertFalse(new_admin.has_group("base.group_system"))

    def test_agent_cannot_assign_an_officer_from_another_centre(self):
        acte = self._create_birth_act()
        acte.piece_ids.with_user(self.agent).write({"etat": "recu"})
        other_centre = self.env["etat.civil.centre"].sudo().create(
            {
                "code_centre": "OTHER-ROLE-TEST",
                "nom_centre": "Autre centre de test",
                "commune": "Autre commune",
            }
        )
        other_officer = self.env["res.users"].sudo().create(
            {
                "name": "Officer from another centre",
                "login": "role-test-other-officer",
                "groups_id": [(6, 0, [self.officer_group.id])],
                "etat_civil_centre_ids": [(4, other_centre.id)],
            }
        )

        with self.assertRaises(AccessError):
            acte.action_envoyer_validation(officier=other_officer)

    def test_agent_cannot_read_acts_outside_assigned_centres(self):
        other_centre = self.env["etat.civil.centre"].sudo().create(
            {
                "code_centre": "OTHER-READ-TEST",
                "nom_centre": "Centre de lecture externe",
                "commune": "Autre commune",
            }
        )
        other_register = self.env["etat.civil.registre"].sudo().create(
            {
                "annee": 2026,
                "type_registre": "naissance",
                "numero_volume": 1,
                "centre_id": other_centre.id,
            }
        )
        other_act = self.env["etat.civil.acte.naissance"].sudo().create(
            {
                "numero_acte": "OTHER-READ-1",
                "feuillet_numero": 1,
                "registre_id": other_register.id,
                "texte_integral_acte": "Acte du centre externe",
                "enfant_id": self.env["etat.civil.individu"].sudo().create(
                    {
                        "nom": "Enfant externe",
                        "sexe": "M",
                        "date_naissance": "2026-01-01",
                    }
                ).id,
                "mere_id": self.env["etat.civil.individu"].sudo().create(
                    {
                        "nom": "Mère externe",
                        "sexe": "F",
                        "date_naissance": "2000-01-01",
                    }
                ).id,
            }
        )

        visible = self.env["etat.civil.acte.naissance"].with_user(self.agent).search(
            [("id", "=", other_act.id)]
        )
        self.assertFalse(visible)

    def test_agent_cannot_set_act_status_directly_or_validate(self):
        acte = self._create_birth_act()

        with self.assertRaises(UserError):
            acte.write({"statut": "valide"})
        with self.assertRaises(AccessError):
            acte.action_valider_acte()

    def test_civil_admin_can_validate_without_officer_group_membership(self):
        acte = self._create_birth_act()

        self.assertTrue(self.admin.has_group("etat_civil.group_etat_civil_agent"))
        self.assertFalse(self.admin.has_group("etat_civil.group_etat_civil_officier"))

        self._transmit_birth_act(acte)
        acte.piece_ids.with_user(self.admin).write({"etat": "verifie"})
        acte.with_user(self.admin).action_valider_acte()

        self.assertEqual(acte.statut, "valide")
        self.assertEqual(acte.officier_validateur_id, self.officer)
        self.assertEqual(acte.utilisateur_validation_id, self.admin)

    def test_officer_group_does_not_imply_agent_group(self):
        self.assertFalse(self.officer.has_group("etat_civil.group_etat_civil_agent"))

    def test_user_with_agent_and_officer_groups_is_not_allowed_agent_actions(self):
        acte = self._create_birth_act()
        multi_role_user = self.env["res.users"].sudo().create(
            {
                "name": "Agent Officier multi-rôle",
                "login": "role-test-multi-role",
                "groups_id": [(6, 0, [self.agent_group.id, self.officer_group.id])],
                "etat_civil_centre_ids": [(4, acte.registre_id.centre_id.id)],
            }
        )
        self.assertTrue(multi_role_user.has_group("etat_civil.group_etat_civil_agent"))
        self.assertTrue(multi_role_user.has_group("etat_civil.group_etat_civil_officier"))

        with self.assertRaises(AccessError):
            acte.with_user(multi_role_user).action_envoyer_validation(officier=self.officer)
        with self.assertRaises(AccessError):
            acte.with_user(multi_role_user).write({"texte_integral_acte": "Édition Agent."})

    def test_officer_validation_locks_all_act_data_but_keeps_mentions_optional(self):
        acte = self._create_birth_act()
        self._transmit_birth_act(acte)
        acte.piece_ids.with_user(self.officer).write({"etat": "verifie"})
        acte.with_user(self.officer).action_valider_acte()

        with self.assertRaises(UserError):
            acte.with_user(self.agent).write({"lieu_naissance": "Modification interdite"})

        acte.with_user(self.officer).write(
            {
                "mention_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Rectification facultative",
                            "type_mention": "rectification",
                            "contenu": "Mention de correction officielle",
                        },
                    )
                ]
            }
        )
        self.assertEqual(len(acte.mention_ids), 1)

    def test_act_validation_requires_verified_documents(self):
        acte = self._create_birth_act()
        self._transmit_birth_act(acte)
        with self.assertRaises(ValidationError):
            acte.with_user(self.officer).action_valider_acte()
        acte.piece_ids.with_user(self.officer).write({"etat": "verifie"})
        acte.with_user(self.officer).action_valider_acte()
        self.assertEqual(acte.statut, "valide")

    def test_civil_status_cannot_be_changed_outside_approved_workflows(self):
        person = self.env["etat.civil.individu"].with_user(self.agent).create({
            "nom": "Statut protégé",
            "sexe": "F",
            "date_naissance": "1990-01-01",
        })
        with self.assertRaises(UserError):
            person.with_user(self.agent).write({"statut_vital": "decede"})
        with self.assertRaises(UserError):
            person.with_user(self.agent).write(
                {"situation_matrimoniale": "marie"}
            )
        with self.assertRaises(UserError):
            self.env["etat.civil.individu"].with_user(self.agent).create({
                "nom": "Statut initial non autorisé",
                "sexe": "M",
                "date_naissance": "1990-01-01",
                "statut_vital": "decede",
            })

    def test_only_officer_can_verify_required_documents(self):
        acte = self._create_birth_act()
        with self.assertRaises(AccessError):
            acte.piece_ids.with_user(self.agent).write({"etat": "verifie"})

    def test_agent_can_read_but_cannot_create_marginal_mentions(self):
        with self.assertRaises(AccessError):
            self.env["etat.civil.mention.marginale"].with_user(self.agent).create(
                {
                    "name": "Mention réservée",
                    "type_mention": "rectification",
                    "contenu": "Test de restriction",
                    "acte_naissance_id": 1,
                }
            )

    def test_officer_cannot_read_or_change_another_centres_mentions(self):
        acte = self._create_birth_act()
        mention = self.env["etat.civil.mention.marginale"].with_user(
            self.officer
        ).create({
            "type_mention": "rectification",
            "contenu": "Mention du centre affecté.",
            "acte_naissance_id": acte.id,
        })

        other_centre = self.env["etat.civil.centre"].sudo().create({
            "code_centre": "ROLE-MENTION-OTHER",
            "nom_centre": "Autre centre",
            "commune": "Autre commune",
        })
        other_officer = self.env["res.users"].sudo().create({
            "name": "Officier autre centre",
            "login": "role-other-centre-officer",
            "groups_id": [(6, 0, [self.officer_group.id])],
            "etat_civil_centre_ids": [(6, 0, [other_centre.id])],
        })

        visible = self.env["etat.civil.mention.marginale"].with_user(
            other_officer
        ).search([("id", "=", mention.id)])
        self.assertFalse(visible)
        with self.assertRaises(AccessError):
            mention.with_user(other_officer).write(
                {"contenu": "Modification hors périmètre."}
            )
        visible_pieces = self.env["etat.civil.piece.justificative"].with_user(
            other_officer
        ).search([("id", "in", acte.piece_ids.ids)])
        self.assertFalse(visible_pieces)
        with self.assertRaises(AccessError):
            acte.piece_ids.with_user(other_officer).write({"etat": "recu"})

    def test_officer_cannot_set_mention_status_directly(self):
        acte = self._create_birth_act()
        mention = self.env["etat.civil.mention.marginale"].with_user(
            self.officer
        ).create({
            "type_mention": "rectification",
            "contenu": "Mention à valider via action.",
            "acte_naissance_id": acte.id,
        })
        with self.assertRaises(ValidationError):
            mention.write({"statut": "valide"})

    def test_civil_admin_can_create_role_limited_internal_user(self):
        wizard = self.env["etat.civil.gestion.utilisateur"].with_user(
            self.admin
        ).create(
            {
                "mode": "create",
                "name": "Utilisateur créé par admin",
                "login": "role-created-agent",
                "new_user_role": "agent",
                "password": "Test-Only-Password-2026",
            }
        )
        wizard.action_save()
        user = self.env["res.users"].sudo().search(
            [("login", "=", "role-created-agent")], limit=1
        )
        self.assertTrue(user)
        self.assertFalse(user.share)
        self.assertIn(self.agent_group, user.groups_id)
        self.assertNotIn(self.officer_group, user.groups_id)
        self.assertNotIn(self.admin_group, user.groups_id)
        self.assertNotIn(self.env.ref("base.group_system"), user.groups_id)

    def test_civil_admin_can_create_an_officer_account(self):
        wizard = self.env["etat.civil.gestion.utilisateur"].with_user(
            self.admin
        ).create(
            {
                "mode": "create",
                "name": "Officier créé par admin",
                "login": "role-created-officer",
                "new_user_role": "officier",
                "password": "Test-Only-Password-2026",
            }
        )
        wizard.action_save()
        user = self.env["res.users"].sudo().search(
            [("login", "=", "role-created-officer")], limit=1
        )
        self.assertIn(self.officer_group, user.groups_id)
        self.assertNotIn(self.agent_group, user.groups_id)
        self.assertNotIn(self.admin_group, user.groups_id)

    def test_agent_cannot_open_user_management(self):
        with self.assertRaises(AccessError):
            self.env["etat.civil.gestion.utilisateur"].with_user(self.agent).create(
                {"mode": "create"}
            )

    def test_civil_admin_can_change_an_internal_users_role(self):
        wizard = self.env["etat.civil.gestion.utilisateur"].with_user(
            self.admin
        ).create(
            {
                "mode": "edit",
                "user_id": self.agent.id,
                "name": self.agent.name,
                "login": self.agent.login,
                "role": "officier",
                "active": True,
            }
        )
        wizard.action_save()
        self.agent.invalidate_recordset(["groups_id"])
        self.assertIn(self.officer_group, self.agent.groups_id)
        self.assertNotIn(self.agent_group, self.agent.groups_id)
        self.assertNotIn(self.admin_group, self.agent.groups_id)

    def test_cannot_disable_last_civil_admin(self):
        wizard = self.env["etat.civil.gestion.utilisateur"].with_user(
            self.admin
        ).create(
            {
                "mode": "edit",
                "user_id": self.admin.id,
                "name": self.admin.name,
                "login": self.admin.login,
                "role": "agent",
                "active": False,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_save()

    def test_incomplete_act_cannot_be_transmitted(self):
        acte = self._create_birth_act()
        with self.assertRaises(ValidationError):
            acte.action_envoyer_validation()
        self.assertEqual(acte.statut, "brouillon")

    def test_double_transmission_is_rejected(self):
        acte = self._create_birth_act()
        acte.piece_ids.with_user(self.agent).write({"etat": "recu"})
        acte.action_envoyer_validation()
        with self.assertRaises(UserError):
            acte.action_envoyer_validation()
        self.assertEqual(acte.statut, "en_attente")

    def test_officer_can_return_for_correction_and_agent_can_resubmit(self):
        acte = self._create_birth_act()
        self._transmit_birth_act(acte)
        acte.with_user(self.officer).action_retourner_correction("Pièce illisible")
        self.assertEqual(acte.statut, "a_corriger")
        self.assertEqual(acte.motif_correction, "Pièce illisible")
        acte.with_user(self.agent).write({"texte_integral_acte": "Texte corrigé"})
        acte.piece_ids.with_user(self.agent).write({"etat": "recu"})
        acte.with_user(self.agent).action_envoyer_validation(officier=self.officer)
        self.assertEqual(acte.statut, "en_attente")

    def test_officer_can_refuse_waiting_act(self):
        acte = self._create_birth_act()
        self._transmit_birth_act(acte)
        acte.with_user(self.officer).action_refuser_acte("Dossier hors compétence communale")
        self.assertEqual(acte.statut, "annule")
        self.assertIn("hors compétence", acte.motif_annulation)
        self.assertTrue(acte.motif_annulation.startswith("REFUS"))

    def test_validated_act_cannot_be_transmitted(self):
        acte = self._create_birth_act()
        self._transmit_birth_act(acte)
        acte.piece_ids.with_user(self.officer).write({"etat": "verifie"})
        acte.with_user(self.officer).action_valider_acte()
        with self.assertRaises(UserError):
            acte.with_user(self.agent).action_envoyer_validation()

    def test_officer_from_another_centre_cannot_validate(self):
        acte = self._create_birth_act()
        self._transmit_birth_act(acte)
        other_centre = self.env["etat.civil.centre"].sudo().create(
            {
                "code_centre": "OTHER-VALIDATE",
                "nom_centre": "Centre non compétent",
                "commune": "Autre commune",
            }
        )
        outsider = self.env["res.users"].sudo().create(
            {
                "name": "Officier extérieur",
                "login": "role-test-outsider-officer",
                "groups_id": [(6, 0, [self.officer_group.id])],
                "etat_civil_centre_ids": [(4, other_centre.id)],
            }
        )
        visible = self.env["etat.civil.acte.naissance"].with_user(outsider).search(
            [("id", "=", acte.id)]
        )
        self.assertFalse(visible)
        with self.assertRaises(AccessError):
            acte.with_user(outsider).action_valider_acte()

    def test_only_the_assigned_officer_can_validate(self):
        acte = self._create_birth_act()
        self._transmit_birth_act(acte)
        acte.piece_ids.with_user(self.officer).write({"etat": "verifie"})
        other_officer = self.env["res.users"].sudo().create(
            {
                "name": "Officer same centre, not assigned",
                "login": "role-test-unassigned-officer",
                "groups_id": [(6, 0, [self.officer_group.id])],
                "etat_civil_centre_ids": [(4, acte.registre_id.centre_id.id)],
            }
        )

        with self.assertRaises(AccessError):
            acte.with_user(other_officer).action_valider_acte()
        acte.with_user(self.officer).action_valider_acte()

    def test_officer_cannot_create_edit_or_transmit_agent_acts(self):
        acte = self._create_birth_act()

        with self.assertRaises(AccessError):
            self.env["etat.civil.acte.naissance"].with_user(self.officer).create(
                {
                    "registre_id": acte.registre_id.id,
                    "texte_integral_acte": "Création interdite à l'officier.",
                    "lieu_naissance": "Commune de test",
                    "enfant_id": acte.enfant_id.id,
                    "mere_id": acte.mere_id.id,
                }
            )
        with self.assertRaises(AccessError):
            acte.with_user(self.officer).write({"texte_integral_acte": "Modification interdite."})
        with self.assertRaises(AccessError):
            acte.with_user(self.officer).action_envoyer_validation(officier=self.officer)

    def test_officer_full_lifecycle_annulation_and_archivage(self):
        acte = self._create_birth_act()
        self._transmit_birth_act(acte)
        acte.piece_ids.with_user(self.officer).write({"etat": "verifie"})
        acte.with_user(self.officer).action_valider_acte()
        self.assertEqual(acte.statut, "valide")

        # Un acte validé ne peut pas être archivé directement (doit être annulé d'abord)
        with self.assertRaises(UserError):
            acte.with_user(self.officer).action_archiver_acte()

        # Un agent ne peut pas annuler un acte.
        with self.assertRaises(AccessError):
            acte.with_user(self.agent).action_annuler_acte("Motif agent interdit")

        # L'officier compétent annule l'acte
        acte.with_user(self.officer).action_annuler_acte("Erreur matérielle avérée sur la filiation")
        self.assertEqual(acte.statut, "annule")
        self.assertIn("Erreur matérielle", acte.motif_annulation)
        self.assertTrue(acte.motif_annulation.startswith("ANNULATION"))

        # L'officier compétent archive l'acte annulé
        acte.with_user(self.officer).action_archiver_acte()
        self.assertEqual(acte.statut, "archive")

    def test_cancellation_wizard(self):
        acte = self._create_birth_act()
        self._transmit_birth_act(acte)
        acte.piece_ids.with_user(self.officer).write({"etat": "verifie"})
        acte.with_user(self.officer).action_valider_acte()

        wizard = self.env["etat.civil.annulation.acte.wizard"].with_user(self.officer).create({
            "acte_type": "naissance",
            "acte_id": acte.id,
            "acte_display": acte.display_name,
            "motif": "Annulation légale via wizard",
        })
        wizard.action_confirmer()
        self.assertEqual(acte.statut, "annule")
        self.assertEqual(acte.motif_annulation, "ANNULATION — Annulation légale via wizard")
