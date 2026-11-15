#!/usr/bin/env bash

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$BASE_DIR/config/odoo17.conf"
LOG_DIR="$BASE_DIR/logs"

usage() {
    cat <<'EOF'
Usage: ./scripts/cleanup_odoo17.sh [OPTION]

Script d'audit non destructif pour l'environnement Odoo 17.

Options:
  --list-databases  Lister les bases PostgreSQL accessibles par l'utilisateur odoo17
  --verify-backups  Vérifier les archives ZIP et l'index des dumps PostgreSQL
  --help            Afficher cette aide

Ce script ne supprime ni base, ni filestore, ni fichier de sauvegarde.
EOF
}

list_databases() {
    local db_password
    db_password="$(sed -n 's/^db_password[[:space:]]*=//p' "$CONFIG" | xargs)"
    if [[ -z "$db_password" ]]; then
        echo "Erreur : db_password introuvable dans $CONFIG" >&2
        return 2
    fi

    PGPASSWORD="$db_password" psql -X -h 127.0.0.1 -U odoo17 -d postgres -v ON_ERROR_STOP=1 -c \
        "select datname, pg_get_userbyid(datdba) as owner, pg_size_pretty(pg_database_size(datname)) as size from pg_database where datistemplate=false order by datname;"
}

verify_backups() {
    local failed=0
    local file

    while IFS= read -r -d '' file; do
        if unzip -tqq "$file" >/dev/null 2>&1; then
            echo "OK ZIP $file"
        else
            echo "ERREUR ZIP $file"
            failed=1
        fi
    done < <(find "$LOG_DIR" -type f -iname '*.zip' -print0 2>/dev/null)

    while IFS= read -r -d '' file; do
        if pg_restore --list "$file" >/dev/null 2>&1; then
            echo "OK DUMP $file"
        else
            echo "ERREUR DUMP $file"
            failed=1
        fi
    done < <( { find "$LOG_DIR" -type f -iname '*.dump' -print0 2>/dev/null; find "$BASE_DIR" -maxdepth 1 -type f -iname '*.dump' -print0 2>/dev/null; } )

    return "$failed"
}

case "${1:---list-databases}" in
    --list-databases)
        list_databases
        ;;
    --verify-backups)
        verify_backups
        ;;
    --help|-h)
        usage
        ;;
    *)
        echo "Option inconnue: $1" >&2
        usage >&2
        exit 2
        ;;
esac
