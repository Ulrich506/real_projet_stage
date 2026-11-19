import re

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class EtatCivilDemandeGuichet(models.Model):
    _name = "etat.civil.demande.guichet"
    _inherit = "etat.civil.audit.mixin"
    _description = "Demande au guichet d'état civil"
    _order = "priorite desc, create_date asc, id asc"

    def _check_agent_or_admin(self, operation):
        """Vérifie que l'utilisateur est agent ou admin. Lève AccessError sinon."""
        user = self.env.user
        is_agent = user.has_group('etat_civil.group_etat_civil_agent')
        is_admin = user.has_group('etat_civil.group_etat_civil_admin')
        if not (is_agent or is_admin):
            raise AccessError(
                f"Impossible de {operation} : cette action est réservée aux agents et aux "
                f"administrateurs. Votre profil ne permet pas cette opération."
            )

    def _check_admin_only(self, operation):
        """Vérifie que l'utilisateur est administrateur. Lève AccessError sinon."""
        user = self.env.user
        is_admin = user.has_group('etat_civil.group_etat_civil_admin')
        if not is_admin:
            raise AccessError(
                f"Impossible de {operation} : cette action est réservée aux administrateurs. "
                f"Votre profil ne permet pas cette opération."
            )

    def _check_regisseur(self, operation):
        """Vérifie que l'utilisateur est régisseur. Lève AccessError sinon."""
        user = self.env.user
        is_regisseur = user.has_group('etat_civil_account.group_etat_civil_regisseur')
        if not is_regisseur:
            raise AccessError(
                f"Impossible de {operation} : cette action est réservée aux régisseurs. "
                f"Votre profil ne permet pas cette opération."
            )

    ticket_numero = fields.Char(
        string="Numéro de ticket",
        required=True,
        readonly=True,
        copy=False,
        default="/",
    )
    citoyen_nom = fields.Char(string="Nom du citoyen", required=True)
    citoyen_cin = fields.Char(string="CIN")
    citoyen_id = fields.Many2one(
        "etat.civil.individu",
        string="Citoyen",
        compute="_compute_citoyen",
        store=True,
        readonly=True,
        help="Individu recherché automatiquement à partir du nom et du CIN.",
    )

    # Actes disponibles pour l'impression
    has_acte_naissance = fields.Boolean(
        string="Acte de naissance disponible",
        compute="_compute_actes_disponibles",
    )
    acte_naissance_id = fields.Many2one(
        "etat.civil.acte.naissance",
        string="Acte de naissance",
        compute="_compute_actes_disponibles",
    )
    has_acte_mariage = fields.Boolean(
        string="Acte de mariage disponible",
        compute="_compute_actes_disponibles",
    )
    acte_mariage_id = fields.Many2one(
        "etat.civil.acte.mariage",
        string="Acte de mariage",
        compute="_compute_actes_disponibles",
    )
    has_acte_deces = fields.Boolean(
        string="Acte de décès disponible",
        compute="_compute_actes_disponibles",
    )
    acte_deces_id = fields.Many2one(
        "etat.civil.acte.deces",
        string="Acte de décès",
        compute="_compute_actes_disponibles",
    )

    @api.depends("citoyen_nom", "citoyen_cin")
    def _compute_citoyen(self):
        """Rechercher l'individu à partir du nom et/ou CIN du ticket."""
        for record in self:
            individu = False
            if record.citoyen_cin and record.citoyen_cin.strip():
                individu = self.env["etat.civil.individu"].search(
                    [("cin", "=", record.citoyen_cin.strip())],
                    limit=1,
                )
            if not individu and record.citoyen_nom and record.citoyen_nom.strip():
                individu = self.env["etat.civil.individu"].search(
                    [("nom", "ilike", record.citoyen_nom.strip())],
                    limit=1,
                )
            record.citoyen_id = individu

    @api.depends("citoyen_id", "citoyen_id.statut_vital", "citoyen_id.situation_matrimoniale")
    def _compute_actes_disponibles(self):
        """Calculer les actes disponibles pour l'impression selon le statut du citoyen."""
        for record in self:
            individu = record.citoyen_id
            if not individu:
                record.has_acte_naissance = False
                record.acte_naissance_id = False
                record.has_acte_mariage = False
                record.acte_mariage_id = False
                record.has_acte_deces = False
                record.acte_deces_id = False
                continue

            # Acte de naissance — toujours disponible si l'individu a un acte validé
            naissance = individu.acte_naissance_enfant_ids.sorted("id", reverse=True)[:1]
            naissance_valide = naissance.filtered(lambda a: a.statut in ("valide", "rectifie", "archive"))
            record.has_acte_naissance = bool(naissance_valide)
            record.acte_naissance_id = naissance_valide[:1] if naissance_valide else False

            # Acte de mariage — disponible si le citoyen est marié (ou a été marié)
            if individu.situation_matrimoniale in ("marie", "divorce", "veuf"):
                mariage = individu.acte_mariage_conjoint_1_ids.sorted("id", reverse=True)[:1]
                if not mariage:
                    mariage = individu.acte_mariage_conjoint_2_ids.sorted("id", reverse=True)[:1]
                mariage_valide = mariage.filtered(lambda a: a.statut in ("valide", "rectifie", "archive"))
                record.has_acte_mariage = bool(mariage_valide)
                record.acte_mariage_id = mariage_valide[:1] if mariage_valide else False
            else:
                record.has_acte_mariage = False
                record.acte_mariage_id = False

            # Acte de décès — disponible si le citoyen est décédé
            if individu.statut_vital == "decede":
                deces = individu.acte_deces_defunt_ids.sorted("id", reverse=True)[:1]
                deces_valide = deces.filtered(lambda a: a.statut in ("valide", "rectifie", "archive"))
                record.has_acte_deces = bool(deces_valide)
                record.acte_deces_id = deces_valide[:1] if deces_valide else False
            else:
                record.has_acte_deces = False
                record.acte_deces_id = False
    type_acte = fields.Selection(
        [
            ("naissance", "Naissance"),
            ("mariage", "Mariage"),
            ("deces", "Décès"),
        ],
        string="Type d'acte",
        required=True,
    )
    type_demande = fields.Selection(
        [
            ("copie_integrale", "Copie intégrale"),
            ("extrait", "Extrait d'acte"),
            ("declaration_immediate", "Déclaration immédiate"),
        ],
        string="Type de demande",
        required=True,
    )
    statut = fields.Selection(
        [
            ("en_attente", "En attente"),
            ("en_cours", "Au guichet"),
            ("traite", "Traité"),
            ("annule", "Annulé"),
        ],
        string="Statut",
        required=True,
        default="en_attente",
    )
    priorite = fields.Selection(
        [
            ("normale", "Normale"),
            ("prioritaire", "Prioritaire"),
            ("urgente", "Urgente"),
        ],
        string="Priorité",
        required=True,
        default="normale",
    )
    processed_at = fields.Datetime(string="Date de traitement", readonly=True)

    _sql_constraints = [
        (
            "ticket_numero_unique",
            "unique(ticket_numero)",
            "Le numéro de ticket doit être unique.",
        ),
    ]

    @api.constrains("citoyen_nom", "citoyen_cin")
    def _check_citizen_data(self):
        for record in self:
            if not (record.citoyen_nom or "").strip():
                raise ValidationError(
                    "Impossible d'enregistrer la demande : le nom du citoyen est obligatoire. "
                    "Veuillez saisir le nom complet du demandeur avant de continuer."
                )
            if record.citoyen_cin and not re.fullmatch(r"\d{12}", record.citoyen_cin):
                raise ValidationError(
                    "Impossible d'enregistrer la demande : le numéro de CIN fourni est invalide. "
                    "Le CIN doit comporter exactement 12 chiffres. Vérifiez le numéro saisi."
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            legacy_cin = vals.pop("citoyen_nin", None)
            if legacy_cin is not None:
                if vals.get("citoyen_cin") not in (None, legacy_cin):
                    raise ValidationError("Les valeurs CIN reçues ne correspondent pas.")
                vals["citoyen_cin"] = legacy_cin
        return self._create_tickets(vals_list)

    def _create_tickets(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            vals["statut"] = "en_attente"
            vals["processed_at"] = False
            if vals.get("ticket_numero", "/") == "/":
                vals["ticket_numero"] = (
                    sequence.next_by_code("etat.civil.demande.guichet") or "/"
                )
        return super().create(vals_list)

    def action_set_status(self, status):
        allowed = {"en_attente", "en_cours", "traite", "annule"}
        if status not in allowed:
            raise ValidationError(
                f"Impossible de modifier le statut : la valeur « {status} » n'est pas reconnue. "
                f"Les statuts autorisés sont : en attente, au guichet, traité, annulé."
            )
        for record in self:
            if record.statut in ("traite", "annule"):
                raise UserError(
                    f"Impossible de modifier le ticket {record.ticket_numero} : "
                    f"ce ticket est déjà clôturé (statut « {record.statut} »). "
                    f"Un ticket clôturé ne peut plus être modifié."
                )
            if status == "en_attente" and record.statut != "en_attente":
                raise UserError(
                    f"Impossible de remettre le ticket {record.ticket_numero} en attente : "
                    f"ce ticket a déjà été appelé au guichet (statut « {record.statut} »). "
                    f"Seul un ticket en attente peut rester en attente."
                )
            record.sudo().write({
                "statut": status,
                "processed_at": fields.Datetime.now() if status == "traite" else False,
            })
        return True

    def action_appeler_au_guichet(self):
        return self.action_set_status("en_cours")

    def action_marquer_traite(self):
        """Marquer une demande comme traitée — réservé aux agents et administrateurs.
        Utilise sudo() uniquement pour écrire le statut et la date, sans ouvrir les droits d'écriture."""
        self._check_agent_or_admin("marquer la demande comme traitée")
        for record in self:
            if record.statut in ("traite", "annule"):
                raise UserError(
                    f"Impossible de marquer le ticket {record.ticket_numero} comme traité : "
                    f"ce ticket est déjà clôturé (statut « {record.statut} »)."
                )
            # sudo() uniquement pour les champs de statut, avec l'utilisateur réel dans l'audit
            record.sudo().write({
                "statut": "traite",
                "processed_at": fields.Datetime.now(),
            })
            # Trace dans l'audit log avec l'utilisateur réel
            record._record_event(
                action_type="status_changed",
                info=f"Ticket {record.ticket_numero} marqué comme traité par {self.env.user.name}"
            )
        return True

    def action_annuler_ticket(self):
        """Annuler une demande — réservé aux administrateurs."""
        self._check_admin_only("annuler la demande")
        for record in self:
            if record.statut in ("traite", "annule"):
                raise UserError(
                    f"Impossible d'annuler le ticket {record.ticket_numero} : "
                    f"ce ticket est déjà clôturé (statut « {record.statut} »)."
                )
            record.sudo().write({
                "statut": "annule",
                "processed_at": fields.Datetime.now(),
            })
            record._record_event(
                action_type="status_changed",
                info=f"Ticket {record.ticket_numero} annulé par {self.env.user.name}"
            )
        return True

    def action_preview_ticket(self):
        """Voir le ticket — affiche le contenu du ticket dans une fenêtre modale.
        Utilise le même template QWeb que le PDF pour que l'aperçu soit identique au fichier téléchargeable."""
        self.ensure_one()
        # Le template guichet_ticket utilise t-foreach="docs" t-as="ticket"
        # Il faut donc passer {"docs": self} comme le fait le rapport PDF
        html = self.env["ir.actions.report"]._render_template(
            "etat_civil_pos.guichet_ticket", {"docs": self}
        )
        # Décoder les bytes si nécessaire
        if isinstance(html, bytes):
            html = html.decode('utf-8')
        # Créer un enregistrement temporaire dans le wizard d'aperçu
        preview = self.env["etat.civil.ticket.preview"].sudo().create({
            "ticket_id": self.id,
            "html_content": html,
        })
        return {
            "name": "Aperçu du ticket %s" % self.ticket_numero,
            "type": "ir.actions.act_window",
            "res_model": "etat.civil.ticket.preview",
            "view_mode": "form",
            "target": "new",
            "res_id": preview.id,
        }

    def action_download_ticket(self):
        """Télécharger le ticket en PDF.
        Génère le PDF et le télécharge avec un nom de fichier explicite basé sur la référence du ticket."""
        self.ensure_one()
        report = self.env.ref("etat_civil_pos.action_report_guichet_ticket", raise_if_not_found=False)
        if report:
            # Utiliser _render_qweb_pdf qui accepte (report_name, res_ids) comme deux arguments
            pdf_content, _ = self.env["ir.actions.report"]._render_qweb_pdf(
                report.report_name, self.ids
            )
            from base64 import b64encode
            pdf_base64 = b64encode(pdf_content).decode('utf-8')
            # Construire le nom de fichier
            filename = "ticket_%s.pdf" % self.ticket_numero.replace(' ', '_').replace('-', '_')
            return {
                "type": "ir.actions.act_url",
                "target": "self",
                "url": f"data:application/pdf;base64,{pdf_base64}#filename={filename}",
            }
        return {"type": "ir.actions.act_window_close"}

    def action_print_ticket(self):
        """Imprimer le ticket — lance une vraie impression via la boîte de dialogue d'impression du navigateur.
        Réservé aux administrateurs et régisseurs."""
        self.ensure_one()
        user = self.env.user
        is_admin = user.has_group('etat_civil.group_etat_civil_admin')
        is_regisseur = user.has_group('etat_civil_account.group_etat_civil_regisseur')
        if not (is_admin or is_regisseur):
            raise AccessError(
                "Impossible d'imprimer le ticket : cette action est réservée aux administrateurs "
                "et aux régisseurs. Votre profil ne permet pas cette opération."
            )
        # Le template guichet_ticket utilise t-foreach="docs" t-as="ticket"
        html = self.env["ir.actions.report"]._render_template(
            "etat_civil_pos.guichet_ticket", {"docs": self}
        )
        if isinstance(html, bytes):
            html = html.decode('utf-8')
        # Construire une page HTML avec un bouton d'impression automatique
        print_page = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Impression du ticket {self.ticket_numero}</title>
            <style>
                @media print {{
                    body {{ margin: 0; padding: 0; }}
                    .no-print {{ display: none !important; }}
                }}
                body {{ margin: 0; padding: 10mm; font-family: "DejaVu Sans", sans-serif; }}
            </style>
            <script>
                window.onload = function() {{
                    window.print();
                    window.close();
                }};
            </script>
        </head>
        <body>
            <div class="no-print" style="text-align:center; padding: 20px;">
                <p>La boîte de dialogue d'impression va s'ouvrir automatiquement.</p>
                <p>Si elle ne s'ouvre pas, cliquez sur le bouton ci-dessous :</p>
                <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; cursor: pointer;">
                    Imprimer
                </button>
            </div>
            {html}
        </body>
        </html>
        """
        return {
            "type": "ir.actions.act_url",
            "target": "new",
            "url": f"data:text/html;charset=utf-8,{print_page}",
        }

    def _check_agent_or_admin_for_print(self):
        """Vérifie que l'utilisateur est agent ou admin pour imprimer un acte."""
        user = self.env.user
        is_agent = user.has_group('etat_civil.group_etat_civil_agent')
        is_admin = user.has_group('etat_civil.group_etat_civil_admin')
        if not (is_agent or is_admin):
            raise AccessError(
                "Impossible d'imprimer un acte : cette action est réservée aux agents "
                "et aux administrateurs. Votre profil ne permet pas cette opération."
            )

    def action_imprimer_acte_naissance(self):
        """Imprimer l'acte de naissance du citoyen. Réservé aux agents et administrateurs."""
        self._check_agent_or_admin_for_print()
        for record in self:
            if not record.acte_naissance_id:
                raise UserError(
                    f"Aucun acte de naissance valide n'est trouvé pour le citoyen "
                    f"« {record.citoyen_nom} ». Vérifiez que l'acte a bien été enregistré "
                    f"et validé."
                )
            return record.acte_naissance_id.action_imprimer_acte()
        return True

    def action_imprimer_acte_mariage(self):
        """Imprimer l'acte de mariage du citoyen. Réservé aux agents et administrateurs."""
        self._check_agent_or_admin_for_print()
        for record in self:
            if not record.acte_mariage_id:
                raise UserError(
                    f"Aucun acte de mariage valide n'est trouvé pour le citoyen "
                    f"« {record.citoyen_nom} ». Ce citoyen n'est pas enregistré comme marié, "
                    f"ou son acte de mariage n'a pas été validé."
                )
            return record.acte_mariage_id.action_imprimer_acte()
        return True

    def action_imprimer_acte_deces(self):
        """Imprimer l'acte de décès du citoyen. Réservé aux agents et administrateurs."""
        self._check_agent_or_admin_for_print()
        for record in self:
            if not record.acte_deces_id:
                raise UserError(
                    f"Aucun acte de décès valide n'est trouvé pour le citoyen "
                    f"« {record.citoyen_nom} ». Vérifiez que l'acte a bien été enregistré "
                    f"et validé."
                )
            return record.acte_deces_id.action_imprimer_acte()
        return True

    def write(self, vals):
        vals = dict(vals)
        legacy_cin = vals.pop("citoyen_nin", None)
        if legacy_cin is not None:
            if vals.get("citoyen_cin") not in (None, legacy_cin):
                raise ValidationError(
                    "Impossible de modifier la demande : les valeurs du numéro de CIN reçues "
                    "ne correspondent pas. Vérifiez la cohérence des données avant de continuer."
                )
            vals["citoyen_cin"] = legacy_cin

        # Bloquer la modification directe du statut par RPC — seul action_set_status peut le faire via sudo()
        if "statut" in vals:
            # Permettre si c'est un appel sudo() depuis action_set_status, action_marquer_traite, ou action_annuler_ticket
            if not self.env.user.has_group('etat_civil.group_etat_civil_admin'):
                raise UserError(
                    "Impossible de modifier le statut du ticket directement : "
                    "utilisez les boutons « Marquer traité » ou « Annuler » disponibles dans "
                    "l'en-tête du formulaire."
                )

        # Bloquer la modification directe de processed_at
        if "processed_at" in vals:
            if not self.env.user.has_group('etat_civil.group_etat_civil_admin'):
                raise UserError(
                    "Impossible de modifier la date de traitement manuellement : "
                    "cette date est enregistrée automatiquement lors du traitement du ticket."
                )

        # Traçabilité des modifications dans l'audit log
        if vals and "statut" not in vals and "processed_at" not in vals:
            user = self.env.user
            is_agent = user.has_group('etat_civil.group_etat_civil_agent')
            # L'agent ne peut modifier aucun champ par RPC
            if is_agent:
                raise AccessError(
                    f"Impossible de modifier la demande : votre profil « Agent » ne permet pas "
                    f"de modifier les champs d'une demande. Seul le bouton « Marquer traité » est autorisé."
                )
            # Tracer les modifications par le régisseur ou l'admin
            for record in self:
                old_vals = {f: record[f] for f in vals.keys() if f in record._fields}
                changes = []
                for field_name, new_val in vals.items():
                    old_val = old_vals.get(field_name)
                    if old_val != new_val:
                        field_label = record._fields.get(field_name, {}).get('string', field_name)
                        changes.append(f"{field_label}: {old_val} → {new_val}")
                if changes:
                    record._record_event(
                        action_type="update",
                        info=f"Modification de la demande {record.ticket_numero} par {user.name}: "
                             + "; ".join(changes)
                    )

        return super().write(vals)
