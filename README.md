# rdm2geosjon

Simple script used to parse RDM database and create geojson for desired instance types.
Pleace existing geojsons to `customs` directory to append them to the final geojson by enabling `-c` flag.

## Required

- Python 3.8 +,  virtualenv
- Packages from `requirements.txt`

## Getting Started

1. Clone `git clone https://github.com/Pupitar/rdm2geojson.git && cd rdm2geojson` repository and enter directory
2. Copy config template `cp config.example.yml config.yml`
3. Make changes in `config.yml`
4. Create python3 virtualenv `virtualenv -p python3 env`
5. Activate virtual env `source env/bin/activate`
6. Run `pip3 install -r requirements.txt`
7. Execute `./env/bin/python main.py -h` to show script help


## Example commands

1. `main.py -qco /tmp/areas.json` - Append a content of all geojsons from `customs` directory, fetch quest type instances and save to `/tmp/areas.json`
2. `main.py -qrio /tmp/areas.json` - Fetch quest, raid and IV types instances and save to `/tmp/areas.json`
