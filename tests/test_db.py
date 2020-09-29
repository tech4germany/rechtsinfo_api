from unittest import mock

import pytest

from rip_api import db


def make_mock_query(page_items, total):
    mock_query = mock.Mock()
    mock_query.offset().limit().all.return_value = page_items
    mock_query.count.return_value = total
    return mock_query


class TestPaginate:
    def test_single_page(self):
        items = [mock.Mock()]
        mock_query = make_mock_query(page_items=items, total=1)
        page = 1
        per_page = 1

        pagination = db.paginate(mock_query, page, per_page)

        mock_query.offset.assert_called_with(0)
        mock_query.offset().limit.assert_called_with(1)

        assert pagination.page == page
        assert pagination.per_page == per_page
        assert pagination.total == 1
        assert pagination.prev_page is None
        assert pagination.next_page is None

    def test_first_page(self):
        items = [mock.Mock()] * 3
        total = 10
        mock_query = make_mock_query(page_items=items, total=total)
        page = 1
        per_page = 3

        pagination = db.paginate(mock_query, page, per_page)

        mock_query.offset.assert_called_with(0)
        mock_query.offset().limit.assert_called_with(3)

        assert pagination.page == page
        assert pagination.per_page == per_page
        assert pagination.total == 10
        assert pagination.prev_page is None
        assert pagination.next_page == 2

    def test_middle_page(self):
        items = [mock.Mock()] * 3
        total = 10
        mock_query = make_mock_query(page_items=items, total=total)
        page = 2
        per_page = 3

        pagination = db.paginate(mock_query, page, per_page)

        mock_query.offset.assert_called_with(3)
        mock_query.offset().limit.assert_called_with(3)

        assert pagination.page == page
        assert pagination.per_page == per_page
        assert pagination.total == 10
        assert pagination.prev_page == 1
        assert pagination.next_page == 3

    def test_page_way_out_should_link_to_last_page(self):
        items = mock.Mock()
        mock_query = make_mock_query(page_items=items, total=10)

        pagination = db.paginate(mock_query, page=2000, per_page=5)

        assert pagination.page == 2000
        assert pagination.prev_page == 2
        assert pagination.next_page is None

    def test_page_less_than_1_should_raise_error(self):
        with pytest.raises(ValueError):
            db.paginate(mock.Mock(), page=0, per_page=5)

    def test_per_page_less_than_1_should_raise_error(self):
        with pytest.raises(ValueError):
            db.paginate(mock.Mock(), page=1, per_page=0)
