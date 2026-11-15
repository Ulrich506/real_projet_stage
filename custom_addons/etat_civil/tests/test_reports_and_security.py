# -*- coding: utf-8 -*-
"""
Tests BRIQUE 5 : Rapports QWeb, QR codes, intégrité documentaire, chatter.

Ces tests vérifient :
- Le rendu correct des rapports PDF (naissance, mariage, décès) sous Odoo 17.
- La génération du hash SHA-256 et du QR code lors de la validation.
- La présence du disclaimer légal dans les rapports (non-substitution à la signature manuscrite).
- Le bon fonctionnement du chatter mail.thread.
"""
import base64
import os
from html import unescape
from pathlib import Path

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestReportsAndSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.centre = cls.env["etat.civil.centre"].create(
            {
                "code_centre": "CPT-01",
                "nom_centre": "Centre Principal de Test",
                "commune": "Fianarantsoa",
                "district_province": "Haute Matsiatra",
                "reference_legale": (
                    "Teny midina faha - 788 - MJ/CAB tamin'ny 29 desambra 1961 "
                    "nataon'ny Minisitry ny Fitsarana sy Mpitahiry ny"
                ),
                "logo_commune": base64.b64encode(
                    (Path(__file__).parent / "assets" / "commune_fianarantsoa_reference.jpg").read_bytes()
                ),
                "logo_region": base64.b64encode(
                    (Path(__file__).parent / "assets" / "region_haute_matsiatra_reference.png").read_bytes()
                ),
            }
        )
        cls.registre_naissance = cls.env["etat.civil.registre"].create(
            {
                "annee": 2026,
                "type_registre": "naissance",
                "numero_volume": 1,
                "centre_id": cls.centre.id,
            }
        )
        cls.registre_mariage = cls.env["etat.civil.registre"].create(
            {
                "annee": 2026,
                "type_registre": "mariage",
                "numero_volume": 1,
                "centre_id": cls.centre.id,
            }
        )
        cls.registre_deces = cls.env["etat.civil.registre"].create(
            {
                "annee": 2026,
                "type_registre": "deces",
                "numero_volume": 1,
                "centre_id": cls.centre.id,
            }
        )

        cls.enfant = cls.env["etat.civil.individu"].create(
            {
                "nom": "Rakoto",
                "prenoms": "Soa Kely",
                "sexe": "F",
                "date_naissance": "2026-01-01",
                # Mineur : CIN non requise
            }
        )
        cls.mere = cls.env["etat.civil.individu"].create(
            {
                "nom": "Rasoa",
                "prenoms": "Bakoly",
                "sexe": "F",
                "date_naissance": "1995-05-10",
                "cin": "101995123456",
            }
        )
        cls.conjoint1 = cls.env["etat.civil.individu"].create(
            {
                "nom": "Rabe",
                "prenoms": "Jean",
                "sexe": "M",
                "date_naissance": "1990-03-15",
                "cin": "101990123456",
            }
        )
        cls.conjoint2 = cls.env["etat.civil.individu"].create(
            {
                "nom": "Razafy",
                "prenoms": "Marie",
                "sexe": "F",
                "date_naissance": "1992-07-20",
                "cin": "101992654321",
            }
        )
        cls.temoin1 = cls.env["etat.civil.individu"].create(
            {
                "nom": "Andria",
                "prenoms": "Hery",
                "sexe": "M",
                "date_naissance": "1988-02-14",
                "cin": "101988111222",
            }
        )
        cls.temoin2 = cls.env["etat.civil.individu"].create(
            {
                "nom": "Ranaivo",
                "prenoms": "Faly",
                "sexe": "M",
                "date_naissance": "1989-08-25",
                "cin": "101989333444",
            }
        )
        cls.defunt = cls.env["etat.civil.individu"].create(
            {
                "nom": "Rakotomalala",
                "prenoms": "Paul",
                "sexe": "M",
                "date_naissance": "1950-01-01",
                "cin": "101950123456",
            }
        )
        cls.declarant_deces = cls.env["etat.civil.individu"].create(
            {
                "nom": "Rakotomalala",
                "prenoms": "Fils Declarant",
                "sexe": "M",
                "date_naissance": "1975-06-10",
                "cin": "101975789456",
            }
        )

        agent_group = cls.env.ref("etat_civil.group_etat_civil_agent")
        officier_group = cls.env.ref("etat_civil.group_etat_civil_officier")
        cls.agent = cls.env["res.users"].create(
            {
                "name": "Agent Test Reports",
                "login": "agent_test_report@example.com",
                "email": "agent_test_report@example.com",
                "groups_id": [(6, 0, [agent_group.id])],
                "etat_civil_centre_ids": [(6, 0, [cls.centre.id])],
            }
        )
        cls.officier = cls.env["res.users"].create(
            {
                "name": "Officier Test Reports",
                "login": "officier_test_report@example.com",
                "email": "officier_test_report@example.com",
                "groups_id": [(6, 0, [officier_group.id, cls.env.ref("base.group_user").id])],
                "etat_civil_centre_ids": [(6, 0, [cls.centre.id])],
            }
        )
        cls.admin = cls.env["res.users"].create({
            "name": "Administrateur Test Reports",
            "login": "admin_test_report@example.com",
            "email": "admin_test_report@example.com",
            "groups_id": [(6, 0, [
                cls.env.ref("etat_civil.group_etat_civil_admin").id,
            ])],
        })

    def _transmettre_a_officier(self, acte):
        acte.piece_ids.with_user(self.agent).write({"etat": "recu"})
        acte.with_user(self.agent).action_envoyer_validation(
            officier=self.officier
        )

    def _valider_par_le_workflow(self, acte):
        acte.piece_ids.with_user(self.agent).write({"etat": "recu"})
        acte.with_user(self.agent).action_envoyer_validation(officier=self.officier)
        acte.piece_ids.with_user(self.officier).write({"etat": "verifie"})
        acte.with_user(self.officier).action_valider_acte()

    def _render_report(self, xmlid, record_ids):
        """Helper compatible Odoo 17 pour rendre un rapport QWeb en HTML."""
        report = self.env.ref(xmlid)
        html, _ = report._render_qweb_html(report.id, record_ids)
        return html.decode("utf-8") if isinstance(html, bytes) else html

    def _render_report_pdf(self, report, record_ids, artifact_name=None):
        pdf, content_type = report.with_context(
            force_report_rendering=True
        )._render_qweb_pdf(report.id, record_ids)
        self.assertEqual(content_type, "pdf")
        self.assertTrue(pdf.startswith(b"%PDF"))
        output_dir = os.environ.get("ETAT_CIVIL_REPORT_OUTPUT_DIR")
        if output_dir and artifact_name:
            path = Path(output_dir) / artifact_name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(pdf)
        return pdf

    def test_civil_admin_can_render_report_without_system_or_officer_group(self):
        admin = self.env["res.users"].sudo().create(
            {
                "name": "Administrateur civil rapport",
                "login": "civil-admin-report",
                "groups_id": [
                    (6, 0, [self.env.ref("etat_civil.group_etat_civil_admin").id])
                ],
            }
        )
        self.assertFalse(admin.has_group("etat_civil.group_etat_civil_officier"))
        self.assertFalse(admin.has_group("base.group_system"))

        acte = self.env["etat.civil.acte.naissance"].with_user(admin).create(
            {
                "registre_id": self.registre_naissance.id,
                "enfant_id": self.enfant.id,
                "mere_id": self.mere.id,
                "lieu_naissance": "Fianarantsoa",
                "texte_integral_acte": "Acte de naissance pour test administrateur.",
            }
        )
        self._valider_par_le_workflow(acte)
        report = self.env.ref("etat_civil.action_report_acte_naissance").with_user(admin)
        html, _ = report._render_qweb_html(report.id, [acte.id])

        html_str = html.decode("utf-8") if isinstance(html, bytes) else html
        self.assertIn("FARITRA", html_str)
        self.assertIn("Fianarantsoa", html_str)
        self.assertIn("ec_birth_qr_area", html_str)
        self.assertNotIn("CODE QR", html_str)

    def test_report_naissance_rendering_with_missing_optional_fields(self):
        """L'extrait validé doit préserver les champs facultatifs absents."""
        acte = self.env["etat.civil.acte.naissance"].create(
            {
                "registre_id": self.registre_naissance.id,
                "enfant_id": self.enfant.id,
                "mere_id": self.mere.id,
                # pere_id volontairement absent
                "lieu_naissance": "Fianarantsoa",
                "filiation": "illegitime",
                "lieu_accouchement": "hopital",
                "texte_integral_acte": (
                    "Tamin'ny voalohan'ny volana Janoary taona roa arivo sy enina "
                    "amby roapolo no teraka tao Fianarantsoa, Soa Kely Rakoto, "
                    "zazavavy, zanak'i Rasoa Bakoly."
                ),
            }
        )
        self._valider_par_le_workflow(acte)

        html_str = self._render_report("etat_civil.action_report_acte_naissance", [acte.id])

        self.assertIn("Nalaina tamin'ny bokim-piankohonana", html_str)
        self.assertIn("Kaominina", html_str)
        self.assertIn("ec_birth_qr_area", html_str)
        self.assertNotIn("CODE QR", html_str)
        self.assertNotIn("KOPIA VOALOHANY", html_str)
        self.assertIn("Rakoto", html_str)
        self.assertIn("Soa Kely", html_str)
        self.assertIn("Rasoa", html_str)
        self.assertIn("Tamin'ny voalohan'ny volana Janoary", unescape(html_str))
        self.assertNotIn("Ray :", html_str)
        report = self.env.ref("etat_civil.action_report_acte_naissance")
        self._render_report_pdf(report, [acte.id], "acte-naissance-demo.pdf")

    def test_report_mariage_rendering(self):
        """Le rapport de mariage doit se générer correctement avec tous les champs requis."""
        acte = self.env["etat.civil.acte.mariage"].create(
            {
                "registre_id": self.registre_mariage.id,
                "conjoint_1_id": self.conjoint1.id,
                "conjoint_2_id": self.conjoint2.id,
                "temoin_1_id": self.temoin1.id,
                "temoin_2_id": self.temoin2.id,
                "date_mariage": "2026-06-15",
                "lieu_mariage": "Mairie de Fianarantsoa",
                "regime_matrimonial": "communaute_biens",
                "texte_integral_acte": "Devant nous ont comparu publiquement...",
            }
        )

        html_str = self._render_report("etat_civil.action_report_acte_mariage", [acte.id])

        self.assertIn("Soratra momba ny fanambadiana", html_str)
        self.assertIn("Rabe", html_str)
        self.assertIn("Razafy", html_str)
        self.assertIn("KOPIAN'NY SORA-PIANKOHONANA", html_str)
        self.assertIn("15/06/2026", html_str)
        self.assertIn("15/03/1990", html_str)
        self.assertNotIn("06/15/2026", html_str)
        self.assertNotIn("03/15/1990", html_str)
        report = self.env.ref("etat_civil.action_report_acte_mariage")
        self._render_report_pdf(report, [acte.id], "acte-mariage-demo.pdf")

    def test_report_deces_rendering(self):
        """Le rapport de décès doit se générer avec déclarant requis."""
        acte = self.env["etat.civil.acte.deces"].create(
            {
                "registre_id": self.registre_deces.id,
                "defunt_id": self.defunt.id,
                "declarant_id": self.declarant_deces.id,
                "date_deces": "2026-10-10",
                "lieu_deces": "Hôpital Tambohobe",
                "texte_integral_acte": "Le dix octobre deux mille vingt-six est décédé Paul Rakotomalala.",
            }
        )

        html_str = self._render_report("etat_civil.action_report_acte_deces", [acte.id])

        self.assertIn("Soratra momba ny fahafatesana", html_str)
        self.assertIn("Rakotomalala", html_str)
        self.assertIn("KOPIAN'NY SORA-PIANKOHONANA", html_str)
        self.assertIn("10/10/2026", html_str)
        self.assertIn("10/06/1975", html_str)
        self.assertNotIn("06/10/1975", html_str)
        report = self.env.ref("etat_civil.action_report_acte_deces")
        self._render_report_pdf(report, [acte.id], "acte-deces-demo.pdf")

    def test_each_document_has_its_own_a4_report_action(self):
        report_ids = (
            "etat_civil.action_report_acte_naissance",
            "etat_civil.action_report_acte_mariage",
            "etat_civil.action_report_acte_deces",
            "etat_civil.action_report_mention_marginale",
        )
        reports = [self.env.ref(xmlid) for xmlid in report_ids]
        self.assertEqual(len({report.report_name for report in reports}), 4)
        for report in reports:
            self.assertEqual(report.report_type, "qweb-pdf")
            self.assertEqual(report.paperformat_id.format, "A4")
            self.assertFalse(report.paperformat_id.orientation == "Landscape")
        birth_format = self.env.ref(
            "etat_civil.action_report_acte_naissance"
        ).paperformat_id
        self.assertEqual(birth_format.margin_top, 20)
        self.assertEqual(birth_format.margin_bottom, 20)
        self.assertEqual(birth_format.margin_left, 20)
        self.assertEqual(birth_format.margin_right, 20)

        self.assertTrue(
            self.env.ref("etat_civil.action_report_mention_marginale").groups_id
            & self.env.ref("etat_civil.group_etat_civil_officier")
        )
        self.assertFalse(
            self.env.ref("etat_civil.action_report_mention_marginale").groups_id
            & self.env.ref("etat_civil.group_etat_civil_agent")
        )

    def test_long_names_apostrophes_and_optional_fields_render_without_fallbacks(self):
        person = self.env["etat.civil.individu"].create({
            "nom": "D'Andriamihaja-Rakotondramanana",
            "prenoms": "Tiana-Mialy",
            "sexe": "F",
            "date_naissance": "2026-04-15",
            "domicile_actuel": "Lot II B 417, quartier très long, commune de démonstration",
        })
        acte = self.env["etat.civil.acte.naissance"].create({
            "registre_id": self.registre_naissance.id,
            "enfant_id": person.id,
            "mere_id": self.mere.id,
            "lieu_naissance": "Centre de santé de démonstration, adresse longue",
            "texte_integral_acte": "Texte généré en français qui ne doit pas être ajouté deux fois.",
            "texte_integral_acte_auto": True,
        })
        report = self.env.ref("etat_civil.action_report_acte_naissance")
        with self.assertRaisesRegex(UserError, "après validation"):
            report._render_qweb_html(report.id, [acte.id])

        self._valider_par_le_workflow(acte)
        html, _ = report._render_qweb_html(report.id, [acte.id])
        html = html.decode("utf-8") if isinstance(html, bytes) else html

        rendered_text = unescape(html)
        self.assertIn("D'Andriamihaja-Rakotondramanana", rendered_text)
        self.assertIn("Tiana-Mialy", rendered_text)
        self.assertIn("adresse longue", rendered_text)
        self.assertIn("15/04/2026", rendered_text)
        self.assertNotIn("00:00", rendered_text)
        self.assertNotIn("Texte généré en français", rendered_text)
        self.assertNotIn("[date à compléter]", rendered_text)
        self.assertNotIn("Texte intégral en cours de génération.", rendered_text)

        self._render_report_pdf(
            report, [acte.id], "acte-naissance-long-names-demo.pdf"
        )
        self.assertEqual(acte.statut, "valide")

    def test_mention_report_uses_linked_act_and_is_not_available_to_agent(self):
        acte = self.env["etat.civil.acte.naissance"].create({
            "registre_id": self.registre_naissance.id,
            "enfant_id": self.enfant.id,
            "mere_id": self.mere.id,
            "lieu_naissance": "Fianarantsoa",
            "texte_integral_acte": "Mention de test liée à l'acte.",
        })
        self._transmettre_a_officier(acte)
        mention = self.env["etat.civil.mention.marginale"].with_user(
            self.admin
        ).create({
            "type_mention": "reconnaissance",
            "date_mention": "2026-07-12",
            "contenu": "Contenu réel de la mention de test.",
            "acte_naissance_id": acte.id,
        })
        report = self.env.ref("etat_civil.action_report_mention_marginale")
        html, _ = report.with_user(self.officier)._render_qweb_html(
            report.id, [mention.id]
        )
        html = html.decode("utf-8") if isinstance(html, bytes) else html

        self.assertIn("FILAZANA SORATRA AN-TSISINY", html)
        self.assertIn("ec_marginal_full", html)
        self.assertIn("CODE QR", html)
        self.assertIn(mention.name, html)
        self.assertIn(acte.numero_acte, html)
        self.assertIn("Contenu réel de la mention de test.", html)
        self._render_report_pdf(
            report.with_user(self.officier),
            [mention.id],
            "avis-mention-marginale-demo.pdf",
        )
        with self.assertRaises(AccessError):
            report.with_user(self.agent)._render_qweb_html(report.id, [mention.id])

    def test_report_access_obeys_center_rules(self):
        acte = self.env["etat.civil.acte.naissance"].create({
            "registre_id": self.registre_naissance.id,
            "enfant_id": self.enfant.id,
            "mere_id": self.mere.id,
            "lieu_naissance": "Fianarantsoa",
            "texte_integral_acte": "Acte du premier centre.",
        })
        other_center = self.env["etat.civil.centre"].create({
            "code_centre": "REPORT-OTHER-CENTER",
            "nom_centre": "Autre centre pour contrôle",
            "commune": "Autre commune",
        })
        other_officer = self.env["res.users"].create({
            "name": "Officier autre centre rapports",
            "login": "officier-autre-centre-report",
            "groups_id": [(6, 0, [
                self.env.ref("etat_civil.group_etat_civil_officier").id,
                self.env.ref("base.group_user").id,
            ])],
            "etat_civil_centre_ids": [(6, 0, [other_center.id])],
        })
        report = self.env.ref("etat_civil.action_report_acte_naissance")
        with self.assertRaises(AccessError):
            report.with_user(other_officer)._render_qweb_html(
                report.id, [acte.id]
            )

    def test_print_actions_remain_available_before_validation(self):
        examples = (
            (
                "etat.civil.acte.naissance",
                "etat_civil.action_report_acte_naissance",
                {
                    "registre_id": self.registre_naissance.id,
                    "enfant_id": self.enfant.id,
                    "mere_id": self.mere.id,
                    "texte_integral_acte": "Acte imprimable avant validation.",
                },
            ),
            (
                "etat.civil.acte.mariage",
                "etat_civil.action_report_acte_mariage",
                {
                    "registre_id": self.registre_mariage.id,
                    "conjoint_1_id": self.conjoint1.id,
                    "conjoint_2_id": self.conjoint2.id,
                    "temoin_1_id": self.temoin1.id,
                    "temoin_2_id": self.temoin2.id,
                    "date_mariage": "2026-06-15",
                    "lieu_mariage": "Mairie de Fianarantsoa",
                    "regime_matrimonial": "communaute_biens",
                    "texte_integral_acte": "Acte imprimable avant validation.",
                },
            ),
            (
                "etat.civil.acte.deces",
                "etat_civil.action_report_acte_deces",
                {
                    "registre_id": self.registre_deces.id,
                    "defunt_id": self.defunt.id,
                    "declarant_id": self.declarant_deces.id,
                    "date_deces": "2026-10-10",
                    "lieu_deces": "Hôpital Tambohobe",
                    "texte_integral_acte": "Acte imprimable avant validation.",
                },
            ),
        )
        for model_name, report_xmlid, values in examples:
            with self.subTest(model=model_name):
                acte = self.env[model_name].create(values)
                self.assertEqual(acte.statut, "brouillon")
                report = self.env.ref(report_xmlid)
                self.assertEqual(report.paperformat_id.format, "A4")
                expected_margins = (20, 20, 20, 20) if model_name == "etat.civil.acte.naissance" else (8, 10, 15, 15)
                self.assertEqual(
                    (
                        report.paperformat_id.margin_top,
                        report.paperformat_id.margin_bottom,
                        report.paperformat_id.margin_left,
                        report.paperformat_id.margin_right,
                    ),
                    expected_margins,
                )
                self.assertEqual(report.paperformat_id.header_spacing, 0)
                self.assertTrue(report.groups_id & self.env.ref(
                    "etat_civil.group_etat_civil_agent"
                ))
                self.assertTrue(report.groups_id & self.env.ref(
                    "etat_civil.group_etat_civil_officier"
                ))

                report.with_user(self.agent).report_action(acte)
                self.assertEqual(acte.statut, "brouillon")

                if model_name == "etat.civil.acte.naissance":
                    with self.assertRaisesRegex(UserError, "après validation"):
                        report.with_user(self.agent)._render_qweb_html(
                            report.id, [acte.id]
                        )
                else:
                    self._transmettre_a_officier(acte)
                    html, _ = report.with_user(self.agent)._render_qweb_html(
                        report.id, [acte.id]
                    )
                    html_str = html.decode("utf-8") if isinstance(html, bytes) else html
                    self.assertIn("NON VALIDÉ", html_str)
                    self.assertIn("NY MPIANDRAIKITRA NY SORA-PIANKOHONANA", html_str)
                    officer_html, _ = report.with_user(self.officier)._render_qweb_html(
                        report.id, [acte.id]
                    )
                    self.assertTrue(officer_html)

    def test_qr_code_and_hash_generation_without_extra_verification_banner(self):
        """Le hash et le QR sont produits, mais l'extrait suit le modèle sans bannière ajoutée."""
        acte = self.env["etat.civil.acte.naissance"].create(
            {
                "registre_id": self.registre_naissance.id,
                "enfant_id": self.enfant.id,
                "mere_id": self.mere.id,
                "lieu_naissance": "Fianarantsoa",
                "texte_integral_acte": "Texte officiel certifié pour validation du test.",
            }
        )

        # Avant validation : hash et QR absents
        self.assertFalse(acte.hash_empreinte_num)
        self.assertFalse(acte.qr_code_image)

        # L'officier vérifie les pièces puis valide
        self._valider_par_le_workflow(acte)

        # Après validation
        self.assertEqual(acte.statut, "valide")
        self.assertTrue(acte.hash_empreinte_num)
        self.assertEqual(len(acte.hash_empreinte_num), 64, "L'empreinte SHA-256 doit faire 64 caractères hex")
        self.assertTrue(acte.qr_code_image)

        # Le code QR reste visible, mais les détails techniques ne figurent pas sur l'extrait.
        html_str = self._render_report("etat_civil.action_report_acte_naissance", [acte.id])

        self.assertIn("ec_birth_qr_area", html_str)
        self.assertNotIn("CODE QR", html_str)
        self.assertIn("data:image/png;base64,", html_str)
        self.assertNotIn(acte.hash_empreinte_num, html_str)
        self.assertNotIn("NON VALIDÉ", html_str)
        self._render_report_pdf(
            self.env.ref("etat_civil.action_report_acte_naissance"),
            [acte.id],
            "acte-naissance-valide-qr-demo.pdf",
        )

    def test_chatter_and_messages(self):
        """Vérifie que mail.thread fonctionne : message_post crée bien un message dans le chatter."""
        acte = self.env["etat.civil.acte.naissance"].create(
            {
                "registre_id": self.registre_naissance.id,
                "enfant_id": self.enfant.id,
                "mere_id": self.mere.id,
                "lieu_naissance": "Fianarantsoa",
                "texte_integral_acte": "Texte officiel pour test du chatter.",
            }
        )

        msg = acte.message_post(
            body="Dossier vérifié par l'agent d'état civil.",
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )
        self.assertTrue(msg)
        self.assertIn("Dossier vérifié", msg.body)
        comment_msgs = acte.message_ids.filtered(lambda m: m.message_type == "comment")
        self.assertEqual(len(comment_msgs), 1)

    # =========================================================================
    # P0 — Tests critiques ajoutés lors de la revue finale (Brique 7)
    # =========================================================================

    def test_integrity_hash_detects_tampering(self):
        """P0.2 — verify_integrity_hash() doit détecter toute altération du contenu après validation."""
        acte = self.env["etat.civil.acte.naissance"].create(
            {
                "registre_id": self.registre_naissance.id,
                "enfant_id": self.enfant.id,
                "mere_id": self.mere.id,
                "lieu_naissance": "Fianarantsoa",
                "texte_integral_acte": "Texte original officiel pour test d'intégrité.",
            }
        )
        # Valider l'acte pour générer le hash
        self._valider_par_le_workflow(acte)

        self.assertEqual(acte.statut, "valide")
        self.assertTrue(acte.hash_empreinte_num)
        original_hash = acte.hash_empreinte_num

        # Vérification positive : l'intégrité est confirmée
        is_valid, msg = acte.verify_integrity_hash()
        self.assertTrue(is_valid, "Le hash doit correspondre juste après validation")

        # Altération directe en base (simule une falsification)
        self.env.cr.execute(
            "UPDATE etat_civil_acte_naissance SET texte_integral_acte = %s WHERE id = %s",
            ("CONTENU FALSIFIÉ PAR UN ATTAQUANT", acte.id),
        )
        acte.invalidate_recordset(["texte_integral_acte"])

        # Vérification négative : la falsification doit être détectée
        is_valid_after, msg_after = acte.verify_integrity_hash()
        self.assertFalse(is_valid_after, "Le hash DOIT détecter la falsification du texte")
        self.assertIn("discordance", msg_after)

        # Le hash stocké ne doit pas avoir changé
        self.assertEqual(acte.hash_empreinte_num, original_hash)

    def test_historical_marriage_without_witnesses(self):
        """P0.1 — Un mariage historique avec donnees_historiques_incompletes=True
        peut exister sans témoins et son rapport doit se générer sans erreur."""
        acte_historique = self.env["etat.civil.acte.mariage"].create(
            {
                "registre_id": self.registre_mariage.id,
                "conjoint_1_id": self.conjoint1.id,
                "conjoint_2_id": self.conjoint2.id,
                # Pas de témoin : données historiques lacunaires
                "temoin_1_id": False,
                "temoin_2_id": False,
                "donnees_historiques_incompletes": True,
                "motif_regularisation": "Acte issu de la migration Odoo 18 : témoins non renseignés.",
                "date_mariage": "2011-03-15",
                "lieu_mariage": "Mairie Ancienne",
                "regime_matrimonial": "communaute_biens",
                "texte_integral_acte": "Acte historique incomplet transféré sans falsification.",
            }
        )

        # L'acte doit exister en base avec les témoins à False
        self.assertFalse(acte_historique.temoin_1_id)
        self.assertFalse(acte_historique.temoin_2_id)
        self.assertTrue(acte_historique.donnees_historiques_incompletes)

        # Le rapport doit se générer sans erreur
        html_str = self._render_report("etat_civil.action_report_acte_mariage", [acte_historique.id])
        self.assertIn("Soratra momba ny fanambadiana", html_str)

        # En revanche, un acte NORMAL sans témoins ne doit PAS pouvoir être transmis
        acte_normal = self.env["etat.civil.acte.mariage"].create(
            {
                "registre_id": self.registre_mariage.id,
                "conjoint_1_id": self.temoin1.id,  # Réutiliser d'autres individus
                "conjoint_2_id": self.temoin2.id,
                "temoin_1_id": False,
                "temoin_2_id": False,
                "date_mariage": "2026-06-15",
                "lieu_mariage": "Mairie Moderne",
                "regime_matrimonial": "separation_biens",
                "texte_integral_acte": "Acte normal sans témoins.",
            }
        )
        errors = acte_normal._check_specific_transmission_requirements()
        self.assertTrue(
            any("témoin" in e.lower() for e in errors),
            "Un acte normal sans témoins doit bloquer la transmission",
        )

    def test_territorial_security_isolation(self):
        """P0.3 — Un officier du Centre B ne peut ni lire ni valider un acte du Centre A."""
        centre_b = self.env["etat.civil.centre"].create(
            {
                "code_centre": "CTR-B-ISO",
                "nom_centre": "Centre Isolé B",
                "commune": "Autre Commune",
            }
        )
        officier_b = self.env["res.users"].create(
            {
                "name": "Officier Centre B",
                "login": "officier_centre_b_iso@test.com",
                "email": "officier_centre_b_iso@test.com",
                "groups_id": [
                    (6, 0, [self.env.ref("etat_civil.group_etat_civil_officier").id,
                             self.env.ref("base.group_user").id]),
                ],
                "etat_civil_centre_ids": [(6, 0, [centre_b.id])],
            }
        )

        # Créer un acte dans le Centre A (cls.centre)
        acte_a = self.env["etat.civil.acte.naissance"].create(
            {
                "registre_id": self.registre_naissance.id,
                "enfant_id": self.enfant.id,
                "mere_id": self.mere.id,
                "lieu_naissance": "Fianarantsoa",
                "texte_integral_acte": "Acte du centre A pour test d'isolation.",
            }
        )

        # L'officier B ne doit pas voir l'acte du Centre A (record rule)
        visible = self.env["etat.civil.acte.naissance"].with_user(officier_b).search(
            [("id", "=", acte_a.id)]
        )
        self.assertFalse(visible, "L'officier du Centre B ne doit pas voir les actes du Centre A")

        acte_a.piece_ids.with_user(self.agent).write({"etat": "recu"})
        acte_a.with_user(self.agent).action_envoyer_validation(officier=self.officier)
        acte_a.piece_ids.with_user(self.officier).write({"etat": "verifie"})

        # Tentative de validation directe doit lever AccessError (compétence territoriale)
        with self.assertRaises(AccessError):
            acte_a.with_user(officier_b).action_valider_acte()
