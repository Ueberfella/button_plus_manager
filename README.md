# Button Plus Manager (Custom Integration für Home Assistant)

Ordnet deine Button Plus Tasten und Relais/Schalter komplett per GUI zu
und erzeugt daraus automatisch ein Lovelace-Dashboard. Keine manuelle
YAML-Bearbeitung für Tasten/Schalter-Zuordnungen nötig.

## Was macht die Integration?

1. **Einrichtung (Config Flow):** Name, **Geräte-ID** deines Button Plus
   (findest du in den MQTT-Topics deines Geräts, z. B. `btn_03a45c` aus
   `buttonplus/btn_03a45c/...`) + Anzahl Tasten/Relais.
2. **Optionen (Options Flow)** – aufgeteilt in 3 Bereiche über ein Menü:
   - **Schalter/Relais zuordnen:** Entität, Name, Icon je Relais.
   - **Tasten & Aktionen zuordnen:** Position (1-8, siehe Geräte-Oberfläche:
     "1 = oberer Connector links" bis "8 = unterer Connector rechts"),
     Seite, Event-Typ (`click`/`shortpress`/`longpress`/`release`), Name,
     Icon **und eine Aktion** (beliebiger Service-Aufruf). Die Integration
     hört dafür **direkt** das MQTT-Topic
     `buttonplus/<geräte-id>/button/<position>-<seite>/pushbutton` ab –
     keine zusätzliche Helfer-Entity in Home Assistant nötig.
   - **Display-Zeilen konfigurieren:** 3 Zeilen, je mit Display-Item-Index
     (0, 1, 2, ... – entspricht `buttonplus/<geräte-id>/displayitem/<i>/...`),
     einer Quell-Entität und optional einer Vorlage (Template) zur
     Formatierung. Die Integration sendet den Wert automatisch an
     `buttonplus/<geräte-id>/displayitem/<i>/value/set`, sobald sich die
     Quell-Entität ändert, und setzt den Zeilennamen einmalig über
     `.../label/set`.
3. Bei jeder Änderung wird automatisch die Datei
   `config/dashboards/button_plus_<name>.yaml` neu geschrieben – mit
   Kacheln (Tiles) für alle zugeordneten Schalter und Tasten (Tasten-Kacheln
   lösen per Klick zusätzlich dieselbe Aktion aus wie der physische Knopf).
4. Nach dem ersten Setup zeigt Home Assistant dir per Benachrichtigung
   den (einmaligen) `configuration.yaml`-Schnipsel an, um das Dashboard
   in der Seitenleiste sichtbar zu machen.

### Wo finde ich Geräte-ID, Position und Display-Item-Index?

Öffne die Konfigurationsoberfläche deines Button Plus im Browser
(die Seite, die du mir als HTML geschickt hast) und klapp die Abschnitte
**"General MQTT Topics"**, **"Buttons Configuration"** und
**"Display Configuration"** auf. Dort stehen die exakten Topics, z. B.
`buttonplus/btn_03a45c/button/2-1/pushbutton` → Geräte-ID `btn_03a45c`,
Position `2`, Seite `1`.

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
