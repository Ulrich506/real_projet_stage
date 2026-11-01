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

# Mise à jour d'un module
update_module() {
    local module="${1:-etat_civil}"

    echo "Mise à jour du module : $module"
    echo "Arrêt temporaire d'Odoo 17..."

    stop_odoo || return 1

    echo "Exécution de la mise à jour..."

    "$VENV_PYTHON" "$ODOO_BIN" \
        -c "$CONFIG" \
        -d etat_civil_odoo17_test \
        -u "$module" \
        --stop-after-init \
        --log-level=info \
        --logfile="$LOG_DIR/update_${module}.log"

    local result=$?

    if [[ $result -eq 0 ]]; then
        echo "Mise à jour terminée avec succès."
    else
        echo "Échec de la mise à jour."
        echo "Consultez : $LOG_DIR/update_${module}.log"
    fi

    echo "Redémarrage d'Odoo 17..."
    start_odoo

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
        update_module "${2:-etat_civil}"
        ;;
    logs)
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "Gestionnaire Odoo 17"
        echo ""
        echo "Utilisation : ./odoo17.sh [commande]"
        echo ""
        echo "Commandes disponibles :"
        echo "  start              Démarrer Odoo"
        echo "  stop               Arrêter Odoo"
        echo "  restart            Redémarrer Odoo"
        echo "  status             Vérifier son état"
        echo "  update             Mettre à jour etat_civil"
        echo "  update NOM         Mettre à jour un autre module"
        echo "  logs               Afficher les journaux en direct"
        ;;
esac
