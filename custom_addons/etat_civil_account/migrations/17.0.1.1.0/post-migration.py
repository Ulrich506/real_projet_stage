def migrate(cr, version):
    cr.execute(
        """
        UPDATE etat_civil_copy_request AS request
           SET entitlement_individu_id = act.enfant_id
          FROM etat_civil_acte_naissance AS act
         WHERE request.acte_naissance_id = act.id
           AND request.entitlement_individu_id IS NULL
        """
    )
