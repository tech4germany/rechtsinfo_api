import glob
import os

from invoke import task
import tqdm

from rip_api import gesetze_im_internet
from rip_api.gesetze_im_internet.db import Session


@task
def ingest_law(c, data_dir, law_slug):
    """
    Process a single law's directory and store it in the DB.
    """
    session = Session()
    try:
        gesetze_im_internet.ingest_law(session, os.path.join(data_dir, law_slug))
        session.commit()
    except:
        session.rollback()
        raise


@task
def ingest_data_dir(c, data_dir):
    """
    Process a whole data directory of laws and store them in the DB.
    """
    session = Session()
    try:
        for law_dir in tqdm.tqdm(glob.glob(f'{data_dir}/*/')):
            gesetze_im_internet.ingest_law(session, law_dir)
            session.commit()
    except:
        session.rollback()
        raise


@task(
    help={
        'law-abbr': 'The abbreviation of the law you want to generate (slugified)'
    }
)
def generate_json_example(c, law_abbr):
    """
    Generate JSON response for a single law and store it in the `example_json` directory.
    """
    session = Session()
    json = gesetze_im_internet.law_json_from_slug(session, law_abbr.lower(), pretty=True)
    session.close()

    with open(f'example_json/{law_abbr.lower()}.json', 'w') as f:
        f.write(json + '\n')


@task
def generate_json_examples(c):
    """
    Generate JSON response for a predefined set of laws and store them in the `example_json` directory.
    """
    for law_abbr in [
        'a_kae', 'aag', 'aaueg_aendg', 'abfaev', 'abv', 'abwv', 'agg', 'aktg', 'alg', 'amg', 'ao',
        'arbgg', 'arbschg', 'arbzg', 'asylg', 'aufenthg', 'aufenthv', 'baeausbv_2004',
        'baederfangausbv', 'bafoeg', 'bahnvorschranwg', 'bakredsitzbek', 'bapostg', 'bartschv',
        'baugb', 'baunvo', 'bbg', 'bdsg', 'beeg', 'betrvg', 'bgb', 'bgbeg', 'burlg', 'erbstdv',
        'estg', 'gastg', 'gbo', 'gg', 'gkg', 'gmbhg', 'gvg', 'gwb', 'gwg', 'haftpflg',
        'heizkostenv', 'hgb', 'hwo', 'ifg', 'ifsg', 'inso', 'irg', 'jfdg', 'juschg', 'krwg',
        'kschg', 'kunsturhg', 'kwg', 'luftsig', 'mabv', 'markeng', 'muschg', 'owig', 'partg',
        'patg', 'pferdewmeistprv', 'prodhaftg', 'puag', 'rog', 'rpflg', 'scheckg', 'sgb_1',
        'sgb_2', 'sgb_3', 'sgb_4', 'sgb_5', 'sgb_6', 'skaufg', 'stgb', 'stpo', 'stvo', 'stvollzg',
        'tierschg', 'tkg', 'tmg', 'tvg', 'urhg', 'uschadg', 'ustdv', 'uwg', 'vag', 'vereinsg',
        'vgv', 'vvg_infov', 'vwvfg', 'waffg', 'wistrg_1954', 'wogg', 'zpo', 'zvg', 'zwvwv'
    ]:
        generate_json_example(c, law_abbr)
