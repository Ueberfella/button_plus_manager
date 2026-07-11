# Button Plus Manager (Custom Integration für Home Assistant)

Ordnet deine Button Plus Tasten und Relais/Schalter komplett per GUI zu
und erzeugt daraus automatisch ein Lovelace-Dashboard. Keine manuelle
YAML-Bearbeitung für Tasten/Schalter-Zuordnungen nötig.

## Was macht die Integration?

1. **Einrichtung (Config Flow):** Name des Dashboards + Anzahl Tasten/Relais.
2. **Optionen (Options Flow)** – aufgeteilt in 3 Bereiche über ein Menü:
   - **Schalter/Relais zuordnen:** Entität, Name, Icon je Relais.
   - **Tasten & Aktionen zuordnen:** die vom Button Plus per MQTT-Discovery
     erzeugte **`event.`-Entität** der Taste (z. B.
     `event.btn_03a45c_button_3_1`), den Event-Typ (`click` / `shortpress` /
     `longpress` / `release`), Name, Icon **und eine Aktion** (beliebiger
     Service-Aufruf, z. B. "Licht an"), die automatisch ausgeführt wird,
     sobald die Taste in genau dieser Art gedrückt wird.
   - **Display-Zeilen konfigurieren:** 3 Zeilen, je mit der **Ziel-Text-
     Entität** des Displays (z. B. `text.btn_03a45c_displayitem_0_value`),
     einer **Quell-Entität**, deren Zustand automatisch dort hineingeschrieben
     wird, optional einer Vorlage (Template) zur Formatierung, sowie optional
     einer Label-Text-Entität mit festem Zeilennamen (z. B.
     `text.btn_03a45c_displayitem_0_label`).
3. Bei jeder Änderung wird automatisch die Datei
   `config/dashboards/button_plus_<name>.yaml` neu geschrieben – mit
   Kacheln (Tiles) für alle zugeordneten Schalter und Tasten (Tasten-Kacheln
   lösen per Klick zusätzlich dieselbe Aktion aus wie der physische Knopf).
4. Nach dem ersten Setup zeigt Home Assistant dir per Benachrichtigung
   den (einmaligen) `configuration.yaml`-Schnipsel an, um das Dashboard
   in der Seitenleiste sichtbar zu machen.

### Wie finde ich die richtigen Entities?

Einstellungen → Geräte & Dienste → Entitäten → nach deiner Geräte-ID
filtern (z. B. `btn_03a45c`). Für Tasten interessieren dich die
`event.*`-Entitäten, für das Display die `text.*_displayitem_*`-Entitäten.
Alles läuft über normale Home-Assistant-Entities und -Services (`text.set_value`)
– keine rohen MQTT-Topics mehr nötig.

## Installation über HACS (empfohlen)

HACS kann nur Integrationen aus einem GitHub-Repository laden. Du musst
diesen Ordner daher einmalig in ein eigenes GitHub-Repo pushen:

```bash
cd button_plus_manager
git init
git add .
git commit -m "Button Plus Manager"
git remote add origin https://github.com/DEINUSERNAME/button_plus_manager.git
git push -u origin main
```

Dann in Home Assistant:

1. HACS → Integrationen → Menü (⋮) → *Benutzerdefinierte Repositories*
2. URL deines Repos eintragen, Kategorie **Integration**
3. "Button Plus Manager" installieren
4. Home Assistant neu starten

## Alternative: manuelle Installation

Ordner `custom_components/button_plus_manager` direkt nach
`<config>/custom_components/button_plus_manager` kopieren und Home
Assistant neu starten.

## Einrichtung in Home Assistant

1. Einstellungen → Geräte & Dienste → Integration hinzufügen →
   "Button Plus Manager"
2. Namen vergeben, Anzahl Tasten/Relais bestätigen
3. Auf der Integrationskarte → *Konfigurieren* (Zahnrad) → alle Tasten
   und Schalter per Dropdown den echten Entities zuordnen, Name + Icon
   vergeben
4. Speichern – das Dashboard-YAML wird sofort neu erzeugt
5. Einmalig den in der Benachrichtigung angezeigten Block in
   `configuration.yaml` einfügen und neu starten, danach erscheint das
   Dashboard in der Seitenleiste

Spätere Änderungen an der Zuordnung (erneut über *Konfigurieren*)
aktualisieren das Dashboard automatisch, ohne weiteren Neustart.

## Service

`button_plus_manager.regenerate_dashboard` – erzeugt alle Dashboards
manuell neu, z. B. per Automatisierung.
