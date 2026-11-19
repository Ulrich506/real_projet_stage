from odoo import api, http, _
from odoo.addons.web.controllers.binary import Binary
from odoo.http import request
from odoo.tools import str2bool
from odoo.exceptions import AccessError


class EtatCivilAuditBinaryController(Binary):
    @http.route(
        [
            "/web/content",
            "/web/content/<string:xmlid>",
            "/web/content/<string:xmlid>/<string:filename>",
            "/web/content/<int:id>",
            "/web/content/<int:id>/<string:filename>",
            "/web/content/<string:model>/<int:id>/<string:field>",
            "/web/content/<string:model>/<int:id>/<string:field>/<string:filename>",
        ],
        type="http",
        auth="public",
        readonly=True,
    )
    def content_common(
        self,
        xmlid=None,
        model="ir.attachment",
        id=None,
        field="raw",
        filename=None,
        filename_field="name",
        mimetype=None,
        unique=False,
        download=False,
        access_token=None,
        nocache=False,
    ):
        # VULN-02 fix: vérifier l'accès aux pièces justificatives AVANT le téléchargement
        # Empêche le téléchargement de pièces d'une autre commune même en connaissant l'ID
        if str2bool(download) and request.env.user.is_authenticated():
            attachment = request.env["ir.binary"]._find_record(
                xmlid, model, id and int(id), access_token, field=field
            )
            if (
                attachment._name == "ir.attachment"
                and attachment.res_model == "etat.civil.piece.justificative"
                and attachment.res_id
            ):
                # VULN-02 fix: utiliser browse() au lieu de sudo().browse()
                # pour appliquer les record rules de l'utilisateur courant
                piece = request.env["etat.civil.piece.justificative"].browse(
                    attachment.res_id
                ).exists()

                # VULN-02 fix: si la pièce n'est pas accessible via les record rules,
                # refuser le téléchargement
                if not piece:
                    raise AccessError(
                        _("Vous n'avez pas l'autorisation de télécharger cette pièce justificative.")
                    )

                # VULN-02 fix: vérifier la compétence territoriale sur l'acte propriétaire
                owner = (
                    piece.acte_naissance_id
                    or piece.acte_mariage_id
                    or piece.acte_deces_id
                    or piece.mention_id
                )
                if owner and hasattr(owner, '_ensure_competence_territoriale'):
                    owner._ensure_competence_territoriale()

                # Journaliser le téléchargement autorisé
                user_id = request.env.uid
                with request.env.registry.cursor() as cr:
                    env = api.Environment(cr, user_id, {})
                    env["etat.civil.audit.log"]._record_event(
                        "download",
                        record=piece,
                    )
                    cr.commit()

        response = super().content_common(
            xmlid=xmlid,
            model=model,
            id=id,
            field=field,
            filename=filename,
            filename_field=filename_field,
            mimetype=mimetype,
            unique=unique,
            download=download,
            access_token=access_token,
            nocache=nocache,
        )
        return response
