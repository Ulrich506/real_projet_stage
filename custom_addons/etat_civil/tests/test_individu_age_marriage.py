from datetime import date
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestIndividuAgeMarriage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Person = cls.env["etat.civil.individu"].sudo()
        cls.centre = cls.env["etat.civil.centre"].sudo().create({
            "code_centre": "AGE-TEST",
            "nom_centre": "Centre test âge",
            "commune": "Commune de test",
        })
        cls.registre = cls.env["etat.civil.registre"].sudo().create({
            "annee": 2026,
            "type_registre": "mariage",
            "numero_volume": 1,
            "centre_id": cls.centre.id,
        })

    def _person(self, suffix, birth):
        return self.Person.create({
            "nom": suffix,
            "sexe": "M" if suffix.endswith("1") else "F",
            "date_naissance": birth,
        })

    def _marriage(self, spouse_1, spouse_2):
        return self.env["etat.civil.acte.mariage"].sudo().create({
            "registre_id": self.registre.id,
            "conjoint_1_id": spouse_1.id,
            "conjoint_2_id": spouse_2.id,
            "lieu_mariage": "Commune de test",
            "regime_matrimonial": "communaute_biens",
            "texte_integral_acte": "Test mariage et catégorie d'âge.",
        })

    def test_categories_and_eligibility(self):
        cases = (
            ("2026-07-01", "nourrisson", False),
            ("2022-01-01", "enfant", False),
            ("2014-01-01", "adolescent", False),
            ("2008-01-01", "adulte", True),
            ("1966-01-01", "senior", True),
        )
        with patch.object(fields.Date, "context_today", return_value=date(2026, 11, 6)):
            for index, (birth, category, eligible) in enumerate(cases):
                person = self._person(f"Age{index}1", birth)
                person.invalidate_recordset(["categorie_age", "eligible_conjoint"])
                self.assertEqual(person.categorie_age, category)
                self.assertEqual(person.eligible_conjoint, eligible)

    def test_unknown_birth_is_not_determined_and_not_eligible(self):
        person = self._person("Unknown1", False)
        self.assertEqual(person.categorie_age, "indetermine")
        self.assertFalse(person.eligible_conjoint)

    def test_birthday_and_non_birthday(self):
        with patch.object(fields.Date, "context_today", return_value=date(2026, 11, 6)):
            before = self._person("Before1", "2008-11-07")
            reached = self._person("Reached1", "2008-11-06")
            self.assertEqual(before._get_age_years(), 17)
            self.assertEqual(reached._get_age_years(), 18)
            self.assertFalse(before.eligible_conjoint)
            self.assertTrue(reached.eligible_conjoint)

    def test_leap_day_birthday(self):
        with patch.object(fields.Date, "context_today", return_value=date(2026, 2, 28)):
            person = self._person("Leap1", "2008-02-29")
            self.assertEqual(person._get_age_years(), 17)
            self.assertFalse(person.eligible_conjoint)
        with patch.object(fields.Date, "context_today", return_value=date(2026, 3, 1)):
            person.invalidate_recordset(["categorie_age", "eligible_conjoint"])
            self.assertEqual(person._get_age_years(), 18)
            self.assertTrue(person.eligible_conjoint)

    def test_marriage_rejects_missing_minor_and_duplicate(self):
        adult_1 = self._person("Adult11", "2000-01-01")
        adult_2 = self._person("Adult22", "2001-01-01")
        minor = self._person("Minor12", "2010-01-01")
        unknown = self._person("Unknown1", False)

        with self.assertRaisesRegex(ValidationError, "date de naissance"):
            self._marriage(unknown, adult_2)
        with self.assertRaisesRegex(ValidationError, "moins de 18 ans"):
            self._marriage(minor, adult_2)
        with self.assertRaisesRegex(ValidationError, "deux individus différents"):
            self._marriage(adult_1, adult_1)
        act = self._marriage(adult_1, adult_2)
        self.assertTrue(act)

    def test_birth_change_is_checked_against_existing_marriage(self):
        adult_1 = self._person("Change11", "2000-01-01")
        adult_2 = self._person("Change22", "2001-01-01")
        act = self._marriage(adult_1, adult_2)
        with self.assertRaisesRegex(ValidationError, "moins de 18 ans"):
            adult_1.write({"date_naissance": "2020-01-01"})
        self.assertTrue(act.exists())
