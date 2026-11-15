from odoo.tests import TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval


@tagged("post_install", "-at_install")
class TestEtatCivilUserDirectory(TransactionCase):
    def test_role_is_derived_from_existing_groups(self):
        user = self.env["res.users"].create(
            {
                "name": "User directory role test",
                "login": "user-directory-role-test",
                "groups_id": [
                    (6, 0, [self.env.ref("etat_civil.group_etat_civil_officier").id])
                ],
            }
        )
        self.assertEqual(user.etat_civil_role, "officier")

        user.write(
            {
                "groups_id": [
                    (6, 0, [self.env.ref("etat_civil.group_etat_civil_agent").id])
                ]
            }
        )
        self.assertEqual(user.etat_civil_role, "agent")

    def test_user_directory_action_is_read_only_and_restricted(self):
        action = self.env.ref("etat_civil.action_etat_civil_res_users")
        allowed_groups = action.groups_id
        self.assertIn(self.env.ref("etat_civil.group_etat_civil_admin"), allowed_groups)
        self.assertIn(self.env.ref("base.group_system"), allowed_groups)
        self.assertEqual(action.domain, "[('share', '=', False)]")
        context = safe_eval(action.context)
        self.assertFalse(context["create"])
        self.assertFalse(context["edit"])
        self.assertFalse(context["delete"])

    def test_user_directory_menu_uses_native_user_model(self):
        menu = self.env.ref("etat_civil.menu_etat_civil_users_list")
        self.assertEqual(menu.action.res_model, "res.users")
