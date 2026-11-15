from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEtatCivilPosBillingSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agent = cls.env["res.users"].sudo().create({
            "name": "Agent POS test",
            "login": "agent-pos-billing-test",
            "groups_id": [(6, 0, [cls.env.ref("etat_civil.group_etat_civil_agent").id])],
        })
        cls.regisseur = cls.env["res.users"].sudo().create({
            "name": "Régisseur POS test",
            "login": "regisseur-pos-billing-test",
            "groups_id": [(
                6, 0, [cls.env.ref("etat_civil_account.group_etat_civil_regisseur").id]
            )],
        })

    def test_agent_cannot_list_pos_copy_requests(self):
        request_model = self.env["etat.civil.copy.request"].with_user(self.agent)
        with self.assertRaises(AccessError):
            request_model.pos_get_pending_copy_requests(0)

    def test_agent_cannot_link_pos_order_to_copy_request(self):
        order_model = self.env["pos.order"].with_user(self.agent)
        with self.assertRaises(AccessError):
            order_model._order_fields({"etat_civil_copy_request_id": 1})

    def test_regisseur_does_not_receive_general_accounting_privileges(self):
        self.assertTrue(
            self.regisseur.has_group("etat_civil_account.group_etat_civil_regisseur")
        )
        self.assertTrue(self.regisseur.has_group("point_of_sale.group_pos_user"))
        self.assertFalse(self.regisseur.has_group("account.group_account_invoice"))
        self.assertFalse(self.regisseur.has_group("base.group_system"))
        self.assertFalse(self.regisseur.has_group("etat_civil.group_etat_civil_officier"))
