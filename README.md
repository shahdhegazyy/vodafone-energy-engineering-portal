# Vodafone Energy Engineering Portal

One Django website containing two Vodafone data-centre engineering dashboards:

1. **DC Cable Design Tool** — conductor-temperature resistivity correction, voltage-drop calculation, circuit-breaker selection, approved cable checks and batch Excel reports.
2. **AC/DC Rack Design Tool** — mixed 48 V DC and 220 V AC device loading, rack-capacity checks, current per PSU, breaker checks and circuit mapping.

## Routes

- `/` — shared home page
- `/dc-cable/` — DC cable design dashboard
- `/rack-design/` — AC/DC rack design dashboard
- `/history/` — saved cable selections and rack designs
- `/admin/` — Django administration

## Database records

The project uses Django models to store completed engineering work:

- `CableSelection` stores project details, design inputs, four conductor temperatures, selected CB, recommended cable, worst voltage drop and calculation details.
- `RackDesign` stores project details, rack capacity, AC/DC voltages, device data, power, rack usage, circuit count and result status.

SQLite is used for local development. The same models can be connected to PostgreSQL for normal deployment.

## Run in Visual Studio Code

Open the extracted `Vodafone_Energy_Engineering_Portal` folder, then run:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

On Windows, activate the environment with `venv\Scripts\activate`.

## Run tests

```bash
python manage.py test
```

The rack calculator runs in the browser using JavaScript. The cable calculator and Excel downloads are handled through Django.
