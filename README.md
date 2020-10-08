# API für Rechtsinformationen des Bundes
![Tests](https://github.com/tech4germany/rechtsinfo_api/workflows/Tests/badge.svg)

Entstanden im Rahmen des [Tech4Germany Fellowship 2020](https://tech.4germany.org/) im [Projekt Rechtsinformationsportal](https://tech.4germany.org/project/rechtsinformationsportal/).

-- TODO:  BILD einfügen und alle 4 taggen --

Mit diesem API-Projekt machen wir Rechtsinformationen des Bundes unter https://api.rechtsinformationsportal.de/ verfügbar. Dokumentation unter https://api.rechtsinformationsportal.de/docs.

Aktuell enthalten sind alle Bundesgesetze und -verordnungen in ihrer aktuellen Fassung.  
(Noch) nicht verfügbar: Rechtsprechung, Verwaltungsvorschriften, Europa- und Landesrecht


## TODO: Architektur
TODO: Kurzbeschreibung Architektur

- TODO: Diagramm AWS Infra für API
- TODO: Diagramm Datenmodell
- TODO: Flussdiagram tägliche Updates

Beschreibung Komponenten u. Tools
- TODO: fastapi -> openapi plus docs
- TODO: Lambda - 3 Funktionen: API, Download, Ingest
- TODO: API Gateway - Eingangspunkt und Throttler
- TODO: RDS / Postgres für DB und Suche
- TODO: S3 - was und wo
- TODO: terraform - link zu einem getting started
- TODO: Logging - wo man in AWS logs findet


## Installation

### Voraussetzungen
Für die lokale Entwicklung sind notwendig:
- Python 3.8 mit [pip](https://pip.pypa.io/en/stable/installing/) und [pipenv](https://pipenv.pypa.io/en/latest/#install-pipenv-today)
  - Ubuntu: `sudo apt update && sudo apt install software-properties-common && sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.8 && pip3 install --user pipenv`
  - macOS: `brew install python@3.8 pipenv`
- PostgreSQL 12+
  - Ubuntu: `sudo apt install postgresql`
  - macOS: `brew install postgresql`
- Systemabhängigkeiten der Python-Pakete [lxml](https://lxml.de/installation.html) und [psycopg2](https://www.psycopg.org/docs/install.html):
  - Ubuntu: `sudo apt install libxml2-dev libxslt-dev libpq-dev`
  - macOS: `brew install libxml2 libxslt`

### Repo klonen

```
git clone https://github.com/tech4germany/rechtsinfo_api.git
```

### Projektabhängigkeiten mit pipenv installieren
```sh
cd rechtsinfo_api
pipenv install --dev
```

### Datenbank initialisieren

```sh
# Leere Datenbank erzeugen.
createdb rip_api
# Shell öffnen, in der alle Python-Abhängigkeiten des Projekts verfügbar sind.
pipenv shell
# Datenbank URL setzen. Format ist: postgresql://$username:$password@$host:$port/$database.
export DB_URL="postgresql://localhost:5432/rip_api"
# Datenbanktabellen initialisieren
invoke database.init
```

### Tests ausführen

In einer `pipenv shell`:
```sh
invoke tests
```

### `invoke`?

Die für's Projekt wichtigsten Tasks können mit [`invoke`](http://www.pyinvoke.org/) ausgeführt werden. Einen Überblick der verfügbaren Tasks gibt:

```sh
invoke --list
```

Tasks sind definiert in [tasks.py](tasks.py).


### Daten importieren

Die Abhängigkeiten sind installiert, die Datenbank aufgesetzt - Zeit, sie mit Daten zu befüllen:

```sh
# Daten von gesetze-im-internet.de herunterladen
invoke ingest.download-laws ./downloads/gii/
# Heruntergeladene Daten parsen und in die Datenbank importieren
invoke ingest.ingest-data-from-location ./downloads/gii/
```

Die Daten werden in `./downloads/gii/` gespeichert und dabei mit Timestamps versehen, so dass bei späterem Ausführen nur diejenigen Gesetze aktualisiert werden, für die es Änderungen auf gesetze-im-internet.de gibt.

Beide Tasks akzeptieren anstelle eines lokalen Pfades auch eine S3 URL in der Form `s3://bucket-name/key-prefix`. In der Produktivumgebung werden die Tasks zB mit `s3://fellows-2020-rechtsinfo-assets/public/gesetze_im_internet` ausgeführt.


### Lokalen API Server starten

Ein lokaler Entwicklungsserver lässt sich starten mit:

```sh
invoke dev.start-api-server &
```

Die API samt Dokumentation ist dann verfügbar unter http://127.0.0.1:5000.

Oder mit curl:
```sh
# zB die Liste aller Gesetze abrufen:
curl http://127.0.0.1:5000/laws
```

## Neue Versionen deployen

Für einfache Code-Updates genügt es, eine neue ZIP-Datei auf S3 hochzuladen und die Lambda-Funktionen darüber upzudaten:

```sh
invoke deploy.build-and-upload-lambda-function
```

Haben sich die Python-Abhängigkeiten in der `Pipfile` geändert, muss das Abhängigkeits-Layer neu gebaut werden. Für Layer-Updates muss eine neue Version des Layers erzeugt die Konfiguration der Lambda-Funktionen aktualisiert werden. Dafür setzen wir terraform ein:

```sh
invoke deploy.build-and-upload-lambda-deps-layer
```
