import os

from invoke import task

from rip_api import gesetze_im_internet


@task(
    help={
        'xml-dir': 'The path to the directory which holds the downloaded data from gesetze-im-internet.de',
        'law-slug': 'The abbreviation of the law you want to generate (as used in its directory name)'
    }
)
def generate_json_example(c, xml_dir, law_slug):
    """
    Generate JSON response for a single law and store it in the `example_json` directory.
    """
    json = gesetze_im_internet.law_json_from_slug(xml_dir, law_slug, pretty=True)
    with open(f'example_json/{law_slug}.json', 'w') as f:
        f.write(json + '\n')

@task(
    help={
        'xml-dir': 'The path to the directory which holds the downloaded data from gesetze-im-internet.de'
    }
)
def generate_json_examples(c, xml_dir):
    """
    Generate JSON response for a predefined set of laws and store them in the `example_json` directory.
    """
    for law_slug in [
        'aa_g_ndg', 'abfaev', 'abwv', 'agg', 'aktg', 'alg', 'amg_1976', 'ao_1977', 'arbgg', 'arbschg',
        'arbzg', 'asylvfg_1992', 'aufag', 'aufenthg_2004', 'aufenthv', 'b_ausbv_2004',
        'b_derfangausbv', 'baf_g', 'bahnvorschranwg', 'bakredsitzbek', 'bapostg', 'bartschv_2005',
        'baunvo', 'bbaug', 'bbg_2009', 'bdsg_2018', 'beeg', 'betrvg', 'bgb', 'bgbeg', 'blgabv',
        'burlg', 'erbstdv_1998', 'estg', 'gastg', 'gbo', 'gewo_34cdv', 'gg', 'gkg_2004', 'gmbhg',
        'gvg', 'gwb', 'gwg_2017', 'haftpflg', 'heizkostenv', 'hgb', 'hwo', 'ifg', 'ifsg', 'inso',
        'irg', 'jfdg', 'juschg', 'kaeaano', 'kredwg', 'krwg', 'kschg', 'kunsturhg', 'luftsig',
        'markeng', 'muschg_2018', 'owig_1968', 'partg', 'patg', 'pferdewmeistprv', 'prodhaftg',
        'puag', 'rog_2008', 'rpflg_1969', 'scheckg', 'sgb_1', 'sgb_2', 'sgb_3', 'sgb_4', 'sgb_5',
        'sgb_6', 'skaufg', 'stgb', 'stpo', 'stvo_2013', 'stvollzg', 'tierschg', 'tkg_2004', 'tmg',
        'tvg', 'urhg', 'uschadg', 'ustdv_1980', 'uwg_2004', 'vag_2016', 'vereinsg', 'vgv_2016',
        'vvg-infov', 'vwvfg', 'waffg_2002', 'wistrg_1954', 'wogg', 'zpo', 'zvg', 'zwvwv'
    ]:
        generate_json_example(c, xml_dir, law_slug)
