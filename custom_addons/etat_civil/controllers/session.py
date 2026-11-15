from odoo import http
from odoo.addons.web.controllers.session import Session
from odoo.http import request


class EtatCivilAuditSessionController(Session):
    @http.route("/web/session/destroy", type="json", auth="user")
    def destroy(self):
        request.env["etat.civil.audit.log"]._record_event("logout")
        return super().destroy()

    @http.route("/web/session/logout", type="http", auth="none")
    def logout(self, redirect="/web"):
        if request.session.uid:
            request.env["etat.civil.audit.log"].with_user(
                request.session.uid
            )._record_event("logout")
        return super().logout(redirect=redirect)
