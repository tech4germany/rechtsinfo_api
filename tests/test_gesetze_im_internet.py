from unittest import mock

from rip_api.gesetze_im_internet import find_models_for_laws


def mock_session_returning(slugs):
    session = mock.Mock()
    laws = [
        mock.Mock(name=f'Law_{slug}', gii_slug=slug)
        for slug in slugs
    ]
    session.query().options().all.return_value = laws
    return session


def test_find_models_for_laws():
    slugs = ['a', 'b']
    session = mock_session_returning(['b', 'c'])

    existing, removed, new_slugs = find_models_for_laws(session, slugs)
    existing_slugs = { law.gii_slug for law in existing }
    removed_slugs = { law.gii_slug for law in removed }
    assert existing_slugs == {'b'}
    assert removed_slugs == {'c'}
    assert new_slugs == {'a'}
