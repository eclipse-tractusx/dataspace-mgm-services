<!--
 Copyright (c) 2026 Contributors to the Eclipse Foundation

 See the NOTICE file(s) distributed with this work for additional
 information regarding copyright ownership.

 This program and the accompanying materials are made available under the
 terms of the Apache License, Version 2.0 which is available at
 https://www.apache.org/licenses/LICENSE-2.0.

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 License for the specific language governing permissions and limitations
 under the License.

 AI Disclosure: This file was entirely AI-generated.
 The AI-generated portions are made available under CC0-1.0 and not subject
 to the project's license. The human contributor has reviewed and verified
 that the content is correct.

 SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
 Assisted-By: Claude Code (claude-opus-5-5)
-->

# Data Space Management Portal auf einem Rechner (Community Days)

Das ganze Portal mit einem Befehl auf einem Laptop: Datenbank, Anmeldung (Keycloak), CSP-Stand-in, Backend
(OSP A) und Portal. Die Daten bleiben beim Neustart erhalten. Nur Testwerte, nicht für den Betrieb.

## Voraussetzungen

- **Docker Desktop** läuft (mit `docker compose`). Im Betrieb brauchen die Dienste gut 1 GB Speicher; für den
  ersten Build 4 GB für Docker einstellen.
- **Ports 3000 und 8080 sind frei.** Port 8080 ist fest (die Anmeldung hängt daran); 3000 lässt sich auf 8081
  ändern (siehe „Typische Fehler").
- **Drei Checkouts nebeneinander**, Ordnernamen wie hier:

  ```text
  <beliebiger Ordner>/
    dataspace-mgm-services/          Branch 7th-cmd
      spec/                          git clone https://github.com/tx-arena-events/portal-backend-spec.git spec
                                     (Stand der Tests: Commit 76587a6)
    dataspace-mgm-ui/                Branch 7th-cmd (ab dem Fix fix/review-api-live-in-image; ohne ihn zeigt
                                     die Antragsprüfung nur Beispieldaten)
  ```

- Windows: die Befehle in PowerShell gehen; `check.sh` braucht Git Bash oder WSL.

## Starten, prüfen, stoppen

Alle Befehle im Ordner `dataspace-mgm-services/deploy/community-days`:

```bash
docker compose up -d --build     # starten; beim ersten Mal 5-15 Minuten (Images werden gebaut)
sh check.sh                      # wartet, bis alles läuft, und prüft es; am Ende "Everything OK"
docker compose stop              # stoppen, Daten bleiben
docker compose up -d             # wieder starten, Daten sind noch da
```

Danach im Browser: **http://localhost:3000**

Startet Docker Desktop neu (z. B. nach einem Neustart des Laptops), kommen die Dienste von selbst wieder, solange sie
nicht mit `stop` angehalten wurden; sonst `docker compose up -d`.

## Anmelden

Das Portal leitet zur Anmeldeseite des **EBW-Connector-Stand-ins** weiter (eine Keycloak-Seite unter
`localhost:8080`, Realm `TEST-EBW`). Dort eintragen:

- **Benutzername:** der Kurzname der Person, klein geschrieben (z. B. `erika`)
- **Passwort:** für alle Personen gleich, der Wert `TEST_EBW_PASSWORD` in `iam/test/.env.test` dieses Repositorys

Danach landet man wieder im Portal.

**Person wechseln:** Abmelden im Portal reicht nicht, der Stand-in merkt sich die Person und meldet sie sofort
wieder an. Deshalb:

1. im Portal abmelden,
2. http://localhost:8080/auth/realms/TEST-EBW/protocol/openid-connect/logout öffnen und auf „Logout" klicken,
3. wieder http://localhost:3000 öffnen und als neue Person anmelden.

Einfacher bei der Vorführung: jede Person in einem eigenen Browser (z. B. Erika in Chrome, Rolf in Firefox,
Renate in Edge/Safari). Private Fenster desselben Browsers teilen sich die Anmeldung.

## Testpersonen (OSP A)

Aus `testdata/persons-osp-a.json` und dem Test-Realm (`iam/test/import/hackathon/`):

| Benutzername | Person | Rolle | Was sie zeigt |
|---|---|---|---|
| `erika` | Erika Mustermann | Antragstellerin ohne Firma | stellt den Antrag für „Beispiel Maschinenbau GmbH"; nach der Freigabe Company Admin dieser Firma |
| `hans` | Hans Beispiel | Antragsteller ohne Firma | zweiter Antrag (z. B. „Beispiel Logistik GmbH") |
| `rolf` | Rolf Prüfer | OSP Reviewer | erste Freigabe (Vier-Augen-Prinzip) |
| `renate` | Renate Prüfer | OSP Reviewer | zweite Freigabe |
| `otto` | Otto Normalverbraucher | OSP Admin | sieht alle Firmen der Installation |
| `pia` | Pia Provider | Company Admin der OSP-Firma | Company Admin einer bestehenden Firma |
| `lieschen` | Lieschen Müller | nur Antragstellerin | ohne Rechte (Fälle „nicht erlaubt") |

Rolf und Renate müssen beide freigeben. Gibt dieselbe Person ein zweites Mal frei, bleibt der Fall bei
„AWAITING_SECOND_APPROVAL" (wartet auf die zweite Person).

## Vorführung in fünf Schritten

1. Als `erika` anmelden, Onboarding starten, Firmendaten eintragen (Land DE, USt-IdNr. z. B. `DE123456789`).
2. Den Weg **mit Dokumenten** nehmen, ein PDF als Handelsregisterauszug hochladen, Bedingungen annehmen, absenden.
3. Person wechseln, als `rolf` die Prüfungen öffnen (http://localhost:3000/onboarding/reviews) und den Fall freigeben.
4. Person wechseln, als `renate` denselben Fall freigeben: Status „APPROVED".
5. Als `otto` die Firmenliste öffnen (http://localhost:3000/participants/companies): die Firma ist ACTIVE und hat
   eine BPN; `erika` ist nach ihrer nächsten Anmeldung Company Admin dieser Firma.

## Zurücksetzen auf den Anfangszustand

```bash
docker compose down -v
docker compose up -d --build
```

Das **löscht alles**, was in der Vorführung entstanden ist: Anträge, Dokumente, Prüffälle, Firmen, die
Zuordnung der Personen zu Firmen (Keycloak) und die Testschlüssel. Danach ist der Stand wie beim ersten Start:
nur die OSP-Firma existiert, alle Personen sind ohne Firma. Ohne `-v` (nur `docker compose down`) bleibt alles erhalten.

## Typische Fehler

| Was passiert | Lösung |
|---|---|
| `port is already allocated` für 3000 | Datei `.env` anlegen (Vorlage `.env.example`) mit `PORTAL_PORT=8081`, dann `docker compose up -d`; Portal unter http://localhost:8081. Andere Ports nimmt die Anmeldung nicht an. |
| `port is already allocated` für 8080 | Das Programm auf 8080 beenden (`docker ps` zeigt, ob es ein anderer Container ist). 8080 lässt sich nicht ändern. |
| Build bricht ab mit Zertifikats-/TLS-Fehler | Firmennetz mit TLS-Proxy. Anderes Netz (z. B. Hotspot) nehmen oder die IT fragen. |
| `check.sh` meldet `FAILED` oder hängt bei einem Dienst | `docker compose logs <dienst>` (z. B. `backend`) ansehen; oft hilft `docker compose up -d` noch einmal. |
| Backend startet nicht, im Log `spec` oder `openapi.yaml` | Der Ordner `spec/` fehlt oder ist leer: siehe Voraussetzungen. |
| Portal startet nicht, Build findet `dataspace-mgm-ui` nicht | Der UI-Checkout liegt nicht neben `dataspace-mgm-services`; Ordner verschieben oder `UI_PATH` in `.env` setzen. |
| Nach der Anmeldung eine Fehlerseite des Portals | Seite http://localhost:3000 neu öffnen und noch einmal anmelden (z. B. nach „Zurück" im Browser während der Anmeldung). |
| Man ist sofort als falsche Person angemeldet | Siehe „Person wechseln". |
| Nach dem Neustart des Portals ist man abgemeldet | Normal: die Sitzungen liegen im Speicher des Portals. Neu anmelden. |
| Alles kaputt | Zurücksetzen (siehe oben). |

## Grenzen

- **CSP-Stand-in im Speicher:** die simulierten Core Services des CSP vergessen beim Neustart, was sie wussten.
  Freigegebene Firmen im Portal bleiben, Vorgänge beim CSP, die gerade laufen, nicht.
- **Kein Wallet-Schritt:** der Weg mit Business Wallet (EUDI) geht hier nicht; nur der Weg mit Dokumenten.
- **Eine Installation (OSP A), je Dienst ein Container:** keine Ausfallsicherheit, nicht für viele Nutzer.
- **Anmeldung nur unter `localhost`:** das Portal läuft nur im Browser auf demselben Rechner, nicht im Netz.
- **Testwerte:** Passwörter und Schlüssel sind öffentlich. Nicht im Netz freigeben.

## Für Technik-Interessierte

- **Ein Issuer für alle:** Keycloak stellt Tokens für `http://localhost:8080/auth` aus; diese Adresse ist im
  Test-Realm fest (Identity Provider `ebw-connector`). Der Browser erreicht Keycloak dort direkt; im CSP-Stand-in,
  im Backend und im Portal leitet ein kleiner Forwarder (`localhost-link.py`, `localhost-link.mjs`)
  `localhost:8080` an den Keycloak-Container weiter. So stimmt `iss` überall überein.
- **Keycloak erreicht den CSP-Stand-in** unter `host.docker.internal:8100` (so steht es im Realm für die
  Dienstkonten `sa-csp*`): der Container `csp` hat diesen Namen als Netzwerk-Alias.
- **`TEST_TOOLS=true`:** Das Backend bringt seine Test-Doubles mit (EBW-Connector unter `/ebw`, Provider-System unter
  `/test-tools/provider`) und bedient `POST /scaffold/reset`, das die Installation **ohne Anmeldung** leert.
  Das ist hier vertretbar, weil der Backend-Port nicht nach außen geht und das Portal nur `/api/**` weiterleitet.
  Wer den Backend-Port veröffentlicht oder den Rechner im Netz erreichbar macht, setzt `TEST_TOOLS=false`
  (dann fehlen die Test-Doubles). `POST /scaffold/reset` ist ohnehin nicht der Weg zum Zurücksetzen: mit
  PostgreSQL scheitert es derzeit in App Access; `docker compose down -v` ist der Weg.
- **`RESET_ON_START=false`:** Daten bleiben über Neustarts (PostgreSQL-Volume `postgres-data`, Keycloak-Volume
  `keycloak-data`, Schlüssel im Volume `keys`).
- **Nicht veröffentlicht:** PostgreSQL, Backend und CSP-Stand-in sind nur im Docker-Netz erreichbar.
  Das Backend direkt prüfen: `docker compose exec backend wget -qO- http://127.0.0.1:8000/health`.
- Einstellungen: `.env.example`. Rechner hinter einem TLS-Proxy bauen mit einer eigenen, nicht eingecheckten
  Datei `docker-compose.local-ca.yml` (in `.gitignore`), die die Firmen-CA nur in den lokalen Build gibt.
