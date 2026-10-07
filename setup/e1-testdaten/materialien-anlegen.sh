#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# Baustein:    e1-testdaten – weitere Materialien (Entscheidung 2026-10-07: 20)
# Zweck:       Legt die Materialien aus materialien.tsv in einem PURIS an.
#              supplier: Produkt, Beziehung (Customer kauft), Bestand 100 Stück
#              customer: Material, Beziehung (Supplier liefert)
#              Zuerst supplier, dann customer: Beim Anlegen der Beziehung holt
#              der Customer die Teileinformation vom Zwilling des Suppliers.
# Vorlagen:    die JSON-Dateien dieses Ordners (Material 01); ersetzt werden nur
#              Materialnummern, Catena-X-Nummer und Name.
# Idempotent:  vorhandene Materialien und Bestände werden übersprungen; HTTP 409
#              bei einer Beziehung gilt als „schon vorhanden“.
# Wartet:      nach jedem Material, bis der Zwilling im DTR der Firma steht
#              (Supplier: Anzahl der Zwillinge; Customer: Zwilling mit der
#              Catena-X-Nummer des Suppliers), höchstens WAIT_S Sekunden.
#
# Aufruf [Mac] (vorher: puris; Port-Forwards 18181 Customer / 18182 Supplier
# und API-Keys in CK/SK wie in AUFBAU.md, e1 – Keys werden nie ausgegeben):
#   CK="$CK" SK="$SK" setup/e1-testdaten/materialien-anlegen.sh supplier
#   CK="$CK" SK="$SK" setup/e1-testdaten/materialien-anlegen.sh customer
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

ROLE="${1:?Aufruf: materialien-anlegen.sh supplier|customer}"
DIR="$(cd "$(dirname "$0")" && pwd)"
WAIT_S="${WAIT_S:-180}"

case "$ROLE" in
  supplier) BASE="http://127.0.0.1:18182/catena"; KEY="${SK:?SK fehlt}" ;;
  customer) BASE="http://127.0.0.1:18181/catena"; KEY="${CK:?CK fehlt}" ;;
  *) echo "Rolle muss supplier oder customer sein" >&2; exit 2 ;;
esac
DTR="/api/v1/namespaces/$ROLE/services/http:dtr:8080/proxy/api/v3/shell-descriptors?limit=1000"

# POST mit JSON aus stdin; gibt den HTTP-Code aus, Antwort nur bei Fehlern.
post() {
  local path="$1" out code
  out="$(mktemp)"
  code="$(curl -s -o "$out" -w '%{http_code}' -X POST -H "X-API-KEY: $KEY" \
    -H "Content-Type: application/json" --data-binary @- "$BASE/$path")"
  if [ "$code" != 200 ] && [ "$code" != 409 ]; then
    echo "  FEHLER $path -> HTTP $code: $(head -c 300 "$out")" >&2; rm -f "$out"; exit 1
  fi
  rm -f "$out"; echo "$code"
}
get() { curl -sf -H "X-API-KEY: $KEY" "$BASE/$1"; }
b64() { printf %s "$1" | base64; }
twins() { kubectl get --raw "$DTR" | jq '.result | length'; }

k=0
while IFS=$'\t' read -r nr mc ms cx name; do
  case "$nr" in ''|\#*|nr) continue ;; esac
  k=$((k + 1))
  t0=$(date +%s)
  if [ "$ROLE" = supplier ]; then
    own="$ms"
    if get materials/all | jq -e --arg m "$ms" 'any(.[]; .ownMaterialNumber == $m)' >/dev/null; then
      c_mat="vorhanden"
    else
      c_mat=$(jq --arg m "$ms" --arg cx "$cx" --arg n "$name" \
        '.ownMaterialNumber=$m | .materialNumberCx=$cx | .name=$n' "$DIR/supplier/2-material.json" | post materials)
    fi
    c_rel=$(jq --arg m "$ms" --arg p "$mc" '.ownMaterialNumber=$m | .partnerMaterialNumber=$p' \
      "$DIR/supplier/3-relation.json" | post materialpartnerrelations)
    if [ "$(get "stockView/product-stocks?ownMaterialNumber=$(b64 "$ms")" | jq length)" -gt 0 ]; then
      c_stk="vorhanden"
    else
      c_stk=$(jq --arg c "$mc" --arg s "$ms" --arg cx "$cx" --arg n "$name" \
        '.material.materialNumberCustomer=$c | .material.materialNumberSupplier=$s | .material.materialNumberCx=$cx | .material.name=$n' \
        "$DIR/supplier/4-product-stock.json" | post stockView/product-stocks)
    fi
    # Zwilling: Anzahl im DTR des Suppliers >= laufende Nummer
    until [ "$(twins)" -ge "$k" ] || [ $(( $(date +%s) - t0 )) -ge "$WAIT_S" ]; do sleep 3; done
    ok=$([ "$(twins)" -ge "$k" ] && echo ja || echo NEIN)
    echo "$nr $own: Material $c_mat, Beziehung $c_rel, Bestand $c_stk, Zwilling $ok ($(( $(date +%s) - t0 )) s)"
  else
    own="$mc"
    if get materials/all | jq -e --arg m "$mc" 'any(.[]; .ownMaterialNumber == $m)' >/dev/null; then
      c_mat="vorhanden"
    else
      c_mat=$(jq --arg m "$mc" --arg n "$name" '.ownMaterialNumber=$m | .name=$n' \
        "$DIR/customer/2-material.json" | post materials)
    fi
    c_rel=$(jq --arg m "$mc" --arg p "$ms" '.ownMaterialNumber=$m | .partnerMaterialNumber=$p' \
      "$DIR/customer/3-relation.json" | post materialpartnerrelations)
    # Zwilling des Customers trägt die Catena-X-Nummer des Suppliers als id
    has() { kubectl get --raw "$DTR" | jq -e --arg id "$cx" 'any(.result[]; .id == $id)' >/dev/null; }
    until has || [ $(( $(date +%s) - t0 )) -ge "$WAIT_S" ]; do sleep 3; done
    ok=$(has && echo ja || echo NEIN)
    echo "$nr $own: Material $c_mat, Beziehung $c_rel, Zwilling $ok ($(( $(date +%s) - t0 )) s)"
  fi
done < "$DIR/materialien.tsv"

echo "Zwillinge im DTR ($ROLE): $(twins)"
