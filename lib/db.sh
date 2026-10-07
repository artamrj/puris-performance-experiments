# shellcheck shell=bash
# Gemeinsame Hilfsfunktionen: PostgreSQL-Datenbanken des Aufbaus (Stand sichern,
# Reset). Wird von `lab` eingebunden. Zugangsdaten werden im jeweiligen Pod aus
# dessen Umgebungsvariablen gelesen und verlassen den Cluster nicht (wie
# AUFBAU.md, e2, „Stand S0 sichern“).

# Ablage der Datenbank-Stände (nie in Git): auf der VM, Kopie auf dem Mac.
STATE_DIR="${STATE_DIR:-$HOME/puris-loadlab-state}"

# Namespace, Pod, Name, Variable Benutzer, Variable Passwort, Variable Datenbank
# (oder fest „postgres“) – gleiche Liste wie beim Sichern von S0.
DB_LIST='identity wallet-postgres-0 c1-wallet POSTGRES_USER POSTGRES_PASSWORD postgres
customer edc-postgresql-0 c2-customer-edc POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DATABASE
customer dtr-postgresql-0 c3-customer-dtr POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DATABASE
supplier edc-postgresql-0 c4-supplier-edc POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DATABASE
supplier dtr-postgresql-0 c5-supplier-dtr POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DATABASE
customer puris-postgresql-0 d1-puris-customer CUSTOM_USER CUSTOM_PASSWORD CUSTOM_DB
supplier puris-postgresql-0 d2-puris-supplier CUSTOM_USER CUSTOM_PASSWORD CUSTOM_DB'

# Datenbanken, die ein Messlauf verändert und der Reset zurücksetzt. Prüfung
# 2026-10-07 (Zeilen nach dem Probelauf gegen S0): nur die EDC-Datenbanken
# wuchsen; Wallet-Stub, DTRs und PURIS gleich. PURIS ersetzt bei jeder
# Transaktion die Bestandszeile (gleiche Zahl, neue Werte) und wird deshalb
# ebenfalls zurückgesetzt. Wallet-Stub und DTRs werden nur geprüft.
RESET_DBS="c2-customer-edc c4-supplier-edc d1-puris-customer d2-puris-supplier"

# Zeilen je Tabelle (gleiche Abfrage wie zeilen.sql beim Sichern von S0).
ZEILEN_SQL="select table_schema||'.'||table_name,
       (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I.%I', table_schema, table_name), false, true, '')))[1]::text
from information_schema.tables
where table_schema not in ('pg_catalog','information_schema') and table_type='BASE TABLE'
order by 1;"

db_names() { echo "$DB_LIST" | awk '{print $3}'; }

# db_cmd <name> <programm> "<weitere Argumente>": führt pg_dump, psql oder
# pg_restore im Datenbank-Pod aus; stdin und stdout werden durchgereicht.
db_cmd() {
  local name="$1" prog="$2" args="${3:-}" ns pod _n uv pv dv db
  read -r ns pod _n uv pv dv <<<"$(echo "$DB_LIST" | awk -v n="$name" '$3 == n')"
  [ -n "$pod" ] || { echo "Unbekannte Datenbank: $name" >&2; return 1; }
  if [ "$dv" = postgres ]; then db=postgres; else db="\$$dv"; fi
  kubectl exec -i -n "$ns" "$pod" -- sh -c \
    "PGPASSWORD=\"\$$pv\" exec $prog -h 127.0.0.1 -U \"\$$uv\" -d \"$db\" $args"
}

db_counts() { db_cmd "$1" psql "-At -F ' ' -f -" <<<"$ZEILEN_SQL"; }
