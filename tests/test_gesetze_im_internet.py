from unittest import mock

from rip_api.gesetze_im_internet import find_models_for_laws


def test_find_models_for_laws():
    slugs = ['a', 'b']
    law_mocks = [mock.Mock(name=f'Law_{slug}', gii_slug=slug) for slug in ['b', 'c']]
    session = mock.Mock()
    query_mock = mock.Mock(return_value=law_mocks)

    with mock.patch('rip_api.db.all_laws_load_only_gii_slug_and_source_timestamp', query_mock):
        existing, removed, new_slugs = find_models_for_laws(session, slugs)

    existing_slugs = { law.gii_slug for law in existing }
    removed_slugs = { law.gii_slug for law in removed }
    assert existing_slugs == {'b'}
    assert removed_slugs == {'c'}
    assert new_slugs == {'a'}
