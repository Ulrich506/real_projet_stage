from odoo import api, http
from odoo.addons.web.controllers.binary import Binary
from odoo.http import request
from odoo.tools import str2bool


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
        if str2bool(download):
            attachment = request.env["ir.binary"]._find_record(
                xmlid, model, id and int(id), access_token, field=field
            )
            if (
                attachment._name == "ir.attachment"
                and attachment.res_model == "etat.civil.piece.justificative"
                and attachment.res_id
            ):
                user_id = request.env.uid
                with request.env.registry.cursor() as cr:
                    env = api.Environment(cr, user_id, {})
                    piece = env["etat.civil.piece.justificative"].sudo().browse(
                        attachment.res_id
                    ).exists()
                    env["etat.civil.audit.log"]._record_event(
                        "download",
                        record=piece if piece else None,
                        record_model=(
                            "etat.civil.piece.justificative" if not piece else None
                        ),
                        record_id=attachment.res_id if not piece else None,
                        user_id=user_id,
                    )
                    cr.commit()
        return response
