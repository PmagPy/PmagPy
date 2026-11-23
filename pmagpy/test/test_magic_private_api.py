"""ipmag private MagIC contribution functions, with the EarthRef API mocked.

The EarthRef API (https://api.earthref.org/v1/openapi.yaml) takes uploads to a private contribution as
multipart/form-data in a field named "file"; a text/plain body is rejected with HTTP 500.
"""
from unittest.mock import Mock, patch

import pytest

from pmagpy import ipmag


def fake_response(status, body):
    response = Mock()
    response.status_code = status
    response.json.return_value = body
    response.request.url = 'https://api.earthref.org/v1/MagIC/private?id=1'
    return response


def upload_file(tmp_path):
    path = tmp_path / 'magic_contribution_test.txt'
    path.write_text('tab delimited\tlocations\nlocation\nTest\n')
    return str(path)


def test_upload_sends_multipart_file_field(tmp_path):
    with patch('pmagpy.ipmag.requests.put', return_value=fake_response(202, {'id': 1})) as put:
        res = ipmag.upload_to_private_contribution(1, upload_file(tmp_path), 'user', 'pass')
    assert res['status_code']
    kwargs = put.call_args.kwargs
    assert kwargs['files']['file'][0] == 'magic_contribution_test.txt'
    assert 'data' not in kwargs
    assert kwargs['params'] == {'id': 1}
    assert res['id'] == 1


def test_upload_returns_the_id_of_a_newly_created_private_contribution(tmp_path):
    # uploading to a public contribution's ID makes a new private one
    with patch('pmagpy.ipmag.requests.put', return_value=fake_response(202, {'id': 2})):
        res = ipmag.upload_to_private_contribution(1, upload_file(tmp_path), 'user', 'pass')
    assert res['status_code']
    assert res['id'] == 2


def test_a_204_names_the_missing_private_contribution(tmp_path):
    response = fake_response(204, None)
    response.json.side_effect = ValueError('no body')
    with patch('pmagpy.ipmag.requests.delete', return_value=response):
        res = ipmag.delete_private_contribution(1, 'user', 'pass')
    assert not res['status_code']
    assert 'No private contribution' in res['errors']


def test_validate_returns_errors_and_warnings():
    errors = [{'table': 'contribution', 'column': 'lab_names', 'message': 'missing', 'rows': [1]}]
    warnings = [{'table': 'sites', 'column': 'age', 'message': 'odd', 'rows': [2]}]
    response = fake_response(200, {'validation': {'errors': errors, 'warnings': warnings}})
    with patch('pmagpy.ipmag.requests.put', return_value=response):
        res = ipmag.validate_private_contribution(1, 'user', 'pass', verbose=False)
    assert res['status_code']
    assert res['validation_results'] == errors
    assert res['validation_warnings'] == warnings


@pytest.mark.parametrize('status, body', [
    (200, ValueError('not JSON')),
    (200, {'validation': None}),
    (204, None),
    (500, ValueError('not JSON')),
])
def test_validate_failure_returns_dict(status, body):
    response = fake_response(status, body)
    if isinstance(body, Exception):
        response.json.side_effect = body
    with patch('pmagpy.ipmag.requests.put', return_value=response):
        res = ipmag.validate_private_contribution(1, 'user', 'pass', verbose=False)
    assert not res['status_code']
    assert res['validation_results'] is None
    assert res['errors']
