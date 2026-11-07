#!/usr/bin/env bash

# ==================================================
# Gestionnaire Odoo 17 - Projet Stage L3
# ==================================================

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ODOO_BIN="$BASE_DIR/odoo/odoo-bin"
VENV_PYTHON="$BASE_DIR/venv/bin/python"
CONFIG="$BASE_DIR/config/odoo17.conf"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/odoo17.log"
PID_FILE="$LOG_DIR/odoo17.pid"

mkdir -p "$LOG_DIR"

# Vérification de l'installation
check_installation() {
    if [[ ! -x "$VENV_PYTHON" ]]; then
        echo "Erreur : environnement virtuel introuvable."
        exit 1
    fi

    if [[ ! -f "$ODOO_BIN" || ! -f "$CONFIG" ]]; then
        echo "Erreur : Odoo ou son fichier de configuration est introuvable."
        exit 1
    fi
}

# Recherche du processus correspondant à cette configuration
find_odoo_pid() {
    pgrep -f '[o]doo-bin.*config/odoo17.conf' | head -n 1
}

# Démarrage
start_odoo() {
    local pid
    pid=$(find_odoo_pid)

    if [[ -n "$pid" ]]; then
        echo "Odoo 17 fonctionne déjà (PID : $pid)."
        echo "Adresse : http://127.0.0.1:8071"
        return
    fi

    echo "Démarrage d'Odoo 17..."

    nohup "$VENV_PYTHON" "$ODOO_BIN" \
        -c "$CONFIG" \
        --logfile="$LOG_FILE" \
        >> "$LOG_DIR/console.log" 2>&1 &

    echo $! > "$PID_FILE"

    sleep 3

    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Odoo 17 démarré."
        echo "Adresse : http://127.0.0.1:8071"
        echo "PID : $(cat "$PID_FILE")"
    else
        echo "Échec du démarrage. Consultez les journaux :"
        tail -n 40 "$LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Arrêt
stop_odoo() {
    local pid
    pid=$(find_odoo_pid)

    if [[ -z "$pid" ]]; then
        echo "Odoo 17 n'est pas en cours d'exécution."
        rm -f "$PID_FILE"
        return
    fi

    echo "Arrêt d'Odoo 17 (PID : $pid)..."
    kill -TERM "$pid"

    for i in {1..30}; do
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "Odoo 17 arrêté correctement."
            rm -f "$PID_FILE"
            return
        fi
        sleep 1
    done

    echo "Le processus ne s'est pas arrêté dans les 30 secondes."
    echo "Aucun arrêt forcé n'a été effectué."
    return 1
}

# État
status_odoo() {
    local pid
    pid=$(find_odoo_pid)

    if [[ -n "$pid" ]]; then
        echo "Odoo 17 : EN COURS D'EXÉCUTION"
        echo "PID : $pid"
        echo "URL : http://127.0.0.1:8071"
    else
        echo "Odoo 17 : ARRÊTÉ"
    fi
}

# Redémarrage
restart_odoo() {
    stop_odoo || return 1
    sleep 2
    start_odoo
}

# Identification d'une base Odoo unique depuis sa configuration
get_default_database() {
    local db_name=""
    local db_name_count=0
    local key value

    while IFS='=' read -r key value; do
        key="$(echo "$key" | xargs)"
        value="${value%%#*}"
        value="$(echo "$value" | xargs)"

        case "$key" in
            db_name)
                ((db_name_count++))
                db_name="$value"
                ;;
        esac
    done < "$CONFIG"

    if [[ $db_name_count -eq 0 || -z "$db_name" ]]; then
        echo "Erreur : aucune base unique n'est configurée dans $CONFIG." >&2
        echo "Ajoutez explicitement: db_name = NOM_BASE" >&2
        echo "dbfilter ne désigne pas automatiquement une base de mise à jour." >&2
        return 2
    fi

    if [[ $db_name_count -ne 1 ]]; then
        echo "Erreur : db_name apparaît plusieurs fois dans $CONFIG." >&2
        echo "Configurez une seule base avec db_name = NOM_BASE" >&2
        return 2
    fi

    if [[ ! "$db_name" =~ ^[A-Za-z0-9_]+$ ]]; then
        echo "Erreur : db_name doit désigner une seule base valide." >&2
        echo "Valeurs multiples ou caractères invalides non autorisés. Configurez une seule base avec db_name = NOM_BASE" >&2
        return 2
    fi

    printf '%s\n' "$db_name"
}

# Mise à jour de modules
update_module() {
    local module="${1:-all}"
    local target_db

    if [[ ! "$module" =~ ^[A-Za-z0-9_]+(,[A-Za-z0-9_]+)*$ ]]; then
        echo "Erreur : les modules doivent contenir uniquement lettres, chiffres et underscores; les modules peuvent être séparés par des virgules."
        return 2
    fi

    target_db="$(get_default_database)" || return 2

    local pid
    pid=$(find_odoo_pid)
    if [[ -n "$pid" ]]; then
        echo "Refus : Odoo 17 fonctionne déjà (PID : $pid)."
        echo "Aucun service n'a été arrêté et aucune base n'a été modifiée."
        echo "Effectuez la mise à jour pendant une fenêtre de maintenance, service arrêté manuellement."
        return 1
    fi

    if [[ "$module" == "all" ]]; then
        echo "Mise à jour de tous les modules déjà installés sur la base configurée : $target_db"
    else
        echo "Mise à jour du ou des modules $module sur la base configurée : $target_db"
    fi
    "$VENV_PYTHON" "$ODOO_BIN" \
        -c "$CONFIG" \
        -d "$target_db" \
        -u "$module" \
        --stop-after-init \
        --no-http \
        --log-level=info \
        --logfile="$LOG_DIR/update_${target_db}_${module}.log"

    local result=$?

    if [[ $result -eq 0 ]]; then
        echo "Mise à jour terminée avec succès."
    else
        echo "Échec de la mise à jour."
        echo "Consultez : $LOG_DIR/update_${target_db}_${module}.log"
    fi

    return "$result"
}

# ==================================================
# Commandes
# ==================================================

check_installation

case "${1:-}" in
    start)
        start_odoo
        ;;
    stop)
        stop_odoo
        ;;
    restart)
        restart_odoo
        ;;
    status)
        status_odoo
        ;;
    update)
        update_module "${2:-all}"
        ;;
    logs)
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "Gestionnaire Odoo 17"
        echo ""
        echo "Utilisation : ./odoo17.sh [commande]"
        echo "odoo17 update [MODULE|all]"
        echo ""
        echo "Commandes disponibles :"
        echo "  start              Démarrer Odoo"
        echo "  stop               Arrêter Odoo"
        echo "  restart            Redémarrer Odoo"
        echo "  status             Vérifier son état"
        echo "  update [MODULE|all] Mettre à jour des modules dans la base db_name configurée"
        echo "  L'omission de MODULE signifie la mise à jour de tous les modules déjà installés."
        echo "  logs               Afficher les journaux en direct"
        ;;
esac
