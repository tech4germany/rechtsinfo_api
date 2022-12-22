# Rechtsinfo API

![Tests](https://github.com/tech4germany/rechtsinfo_api/workflows/Tests/badge.svg) [![license](https://img.shields.io/github/license/tech4germany/rechtsinfo_api.svg)](LICENSE)

API Prototyp für Rechtsinformationen des Bundes.

> :warning: Dieser Prototyp ist nicht mehr online verfügbar. Der [DigitalService](https://digitalservice.bund.de) arbeitet an einer [vollumfänglichen, offiziellen Lösung](https://digitalservice.bund.de/blog/neues-rechtsinformationssystem). Für die zwischenzeitliche Überbrückung ist möglicherweise dieses Open-Source Projekt hilfreich: https://github.com/nfelger/gadi.

## Tech4Germany Projekt

Entstanden innerhalb der 12 Wochen des [Tech4Germany Fellowships 2020](https://tech.4germany.org/), entwickelt vom [Team Rechtsinformationsportal](https://tech.4germany.org/project/rechtsinformationsportal/) in Kollaboration mit dem [Bundesministerium der Justiz und für Verbraucherschutz](https://www.bmjv.de).

:wave:

![Teamfoto](docs/team.jpg)

_von links nach rechts_:
[Greta Fest](https://www.linkedin.com/in/greta-fest-722a73122/) –
[Niko Felger](https://www.linkedin.com/in/nfelger/) –
[Tito Rodriguez](https://www.linkedin.com/in/joseernestorodriguez/) –
[Conrad Schlenkhoff](https://www.linkedin.com/in/conrad-schlenkhoff/)


## Hintergrund
> _Rechtsinformationen für alle_
 
Jeder hat das Recht auf Zugang zu den Gesetzen und Gerichtsentscheidungen, die unser Zusammenleben in der Gesellschaft regeln. Bisher sind die Rechtsinformationen des Bundes in maschinenlesbarer Form nur als umständlich zu verarbeitende Sammlung einzelner, in Teilen kryptischer XML-Dateien auf [gesetze-im-internet.de](http://www.gesetze-im-internet.de/) und [rechtsprechung-im-internet.de](http://www.rechtsprechung-im-internet.de/) verfügbar. Wir wollen das ändern, indem wir diese Daten aufbereiten und in einem selbsterklärenden JSON-Format über eine Standards-konforme API der Öffentlichkeit zur Verfügung stellen.

## Die API im Projektkontext

![Projektüberblick](docs/project_context.svg)

## Stand

Aktuell enthalten sind alle Bundesgesetze und -verordnungen in ihrer aktuellen Fassung.  
(Noch) nicht verfügbar: Rechtsprechung, Verwaltungsvorschriften, Europa- und Landesrecht

## Nutzung

~Wer die API nutzen möchte, findet auf https://api.rechtsinformationsportal.de/ detaillierte Dokumentation.~

Die API ist nicht mehr online. Wer maschinenlesbare Gesetze sucht, wird hier fündig: https://github.com/nfelger/gadi

## Installation lokal

Für die lokale Entwicklung benötigt man:
- Python 3.8 mit [pip](https://pip.pypa.io/en/stable/installing/) und [pipenv](https://pipenv.pypa.io/en/latest/#install-pipenv-today)
  - Ubuntu:  
  `sudo apt update && \`  
  `sudo apt install software-properties-common && \`  
  `sudo add-apt-repository ppa:deadsnakes/ppa && \`  
  `sudo apt install python3.8 python3-dev python3-pip python3-venv python3-wheel && \`  
  `sudo pip3 install pipenv`
  - macOS:  
  `brew install python@3.8 pipenv`
- [PostgreSQL](https://www.postgresql.org/) 12+
  - Ubuntu:
    - `sudo apt install postgresql postgresql-contrib`
    - Zugang konfigurieren, z.B. Passwort für den postgres User setzen:
      - `sudo -u postgres psql postgres`
      - Am psql Prompt: `\password postgres`
      - Für Alternativen siehe: https://help.ubuntu.com/community/PostgreSQL
  - macOS:  
  `brew install postgresql`
- Systemabhängigkeiten der Python-Pakete [lxml](https://lxml.de/installation.html) und [psycopg2](https://www.psycopg.org/docs/install.html):
  - Ubuntu:  
  `sudo apt install libxml2-dev libxslt-dev libpq-dev`
  - macOS:  
  `brew install libxml2 libxslt`
- Für Deployments in die Produktivumgebung: [terraform](https://www.terraform.io/), [docker](https://www.docker.com/), zip
  - Ubuntu:
    - Terraform apt repo hinzufügen:  
    `curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add - && \`  
    `sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"`
    - Docker apt repo hinzufügen:  
    `curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - && \`  
    `sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"`
    - Pakete installieren:  
    `sudo apt install terraform docker-ce zip`
    - Nutzer zur "docker" Gruppe hinzufügen (anschliessend aus- und wieder einloggen):  
    `sudo usermod -aG docker ${USER}`
  - macOS:  
  `brew tap hashicorp/tap && \`  
  `brew install hashicorp/tap/terraform && \`  
  `brew cask install docker`

### Repo klonen und Projektabhängigkeiten installieren

```sh
git clone https://github.com/tech4germany/rechtsinfo_api.git
cd rechtsinfo_api
pipenv install --dev
```

### Tool: `pipenv shell`

`pipenv shell` öffnet eine Shell, in der alle Python-Abhängigkeiten des Projekts verfügbar sind.

Alles Folgende wird in einer solchen Shell ausgeführt.

### Datenbank initialisieren

```sh
# Postgres Datenbank erzeugen, z.B. mit:
createdb rip_api  # Ubuntu: sudo -u postgres createdb rip_api
# Datenbank URI setzen. Format ist: postgresql://$username:$password@$host:$port/$database. Z.B.:
export DB_URI="postgresql://localhost:5432/rip_api"   # Ubuntu: postgresql://postgres:p4ssw0rt@127.0.0.1:5432/rip_api
# Datenbanktabellen initialisieren
invoke database.init
```

### Tests ausführen

```sh
invoke tests
```

### Tool: `invoke`

Mit [`invoke`](http://www.pyinvoke.org/) lassen sich alle wichtigen Tasks ausführen. Einen Überblick gibt:

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
invoke ingest.ingest-data ./downloads/gii/
```

Die Daten werden in `./downloads/gii/` gespeichert und mit Timestamps versehen, so dass bei späterem Ausführen nur diejenigen Gesetze aktualisiert werden, für die es Änderungen auf gesetze-im-internet.de gibt.

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

## Produktivumgebung und Architektur

![Systemkontext](docs/context.svg)

### Überblick

Die API besteht aus einem Server, zwei Hintergrundtasks sowie zwei Datenspeichern. Der API Server beantwortet HTTP-Requests, die Hintergrundtasks aktualisieren täglich die Datenbank.

Sie wird in einer "serverless"-Architektur mit [AWS Lambda](https://aws.amazon.com/lambda/) und [Amazon API Gateway](https://aws.amazon.com/api-gateway/) betrieben.

Daten werden in [Amazon S3](https://aws.amazon.com/s3/) und [Amazon RDS](https://aws.amazon.com/rds/) gespeichert.

![Architekturüberblick](docs/container.svg)

### API Server
Der API Server basiert auf dem [fastapi](https://fastapi.tiangolo.com/) Framework, welches den [OpenAPI Standard](https://github.com/OAI/OpenAPI-Specification) implementiert. Es liefert automatisch generierte, interaktive Dokumentation und eine maschinenlesbare API-Spezifikation unter https://api.rechtsinformationsportal.de/v1/openapi.json.

Die fastapi App wird innerhalb einer Lambda-Funktion aufgerufen, welche hinter einem API Gateway sitzt. Letzeres ist das alleinige öffentliche Interface und kontrolliert den Zugriff von außen. Dieser Ansatz bietet eine eingriffslose Skalierungsfähigkeit, bei der die Kosten bedarfsabhängig bleiben.

### Hintergrundtasks
gesetze-im-internet.de wird täglich aktualisiert. Zwei Hintergrundtasks sorgen dafür, dass die API diese Updates stets reflektiert. Ein "Download" Task prüft, welche Daten aktualisiert wurden, lädt neue herunter, ersetzt veraltete und löscht entfernte. Ein "Ingest" Task liest die neuen Daten, verarbeitet sie vor und importiert sie in die Datenbank.

Der "Download" Task wird einmal täglich über einen CloudWatch Event angestossen. Nach erfolgreichem Abschluss ruft er den "Ingest" Task auf.

### Datenspeicher
Als primäre Datenbank dient eine PostgreSQL Datenbank, die über Amazon RDS verwaltet und bereitgestellt wird. Vereinfachtes Datenmodell:

![ER Diagramm](docs/erd.svg)

Für Assets wie Bilder und Dateianhänge zu Gesetzen werden auf Amazon S3 im Bucket "fellows-2020-rechtsinfo-assets" gespeichert. Hier werden ausserdem von gesetze-im-internet.de heruntergeladene Daten zwischengespeichert.

### Infrastruktur
Die verwendeten AWS-Komponenten werden über das Infrastructure-as-Code Tool terraform verwaltet. Hiermit sind alle Komponenten dokumentiert und können nach Bedarf angepasst und erweitert werden. [Terraform Überblick](https://www.terraform.io/intro/index.html), [Anleitung](https://learn.hashicorp.com/collections/terraform/aws-get-started)

Logging aus API Server und Hintergrundtasks wird in CloudWatch Logs festgehalten. Die Logeinträge sind über [Logs Insights](https://eu-central-1.console.aws.amazon.com/cloudwatch/home?region=eu-central-1#logsV2:logs-insights) komfortabel durchsuchbar.

### Neue Versionen deployen

Als erstes AWS Credentials setzen:
```sh
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE  # eigene access key ID einsetzen
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY  # eigenen secret key einsetzen
export AWS_DEFAULT_REGION=eu-central-1
```

Für einfache Code-Updates genügt es, eine neue ZIP-Datei auf S3 hochzuladen und die Lambda-Funktionen darüber upzudaten:

```sh
invoke deploy.update-lambda-function
```

Haben sich die Python-Abhängigkeiten in der `Pipfile` geändert, muss das Abhängigkeits-Layer neu gebaut werden. Für Layer-Updates muss eine neue Version des Layers erzeugt die Konfiguration der Lambda-Funktionen aktualisiert werden. Dafür werden die Abhängigkeiten in einem [lambci/docker-lambda](https://github.com/lambci/docker-lambda/) Docker-Container gebaut, der die AWS Lambda Umgebung simuliert, und anschliessend werden die Lambda-Funktionen mit terraform aktualisiert:

```sh
invoke deploy.update-lambda-deps-layer
```
