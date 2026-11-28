"""ipmag private MagIC contribution functions, with the EarthRef API mocked.

The EarthRef API (https://api.earthref.org/v1/openapi.yaml) takes uploads to a private contribution as
multipart/form-data in a field named "file"; a text/plain body is rejected with HTTP 500.
"""
from unittest.mock import Mock, patch

import pytest
import requests

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
        res = ipmag.upload_to_private_contribution(1, upload_file(tmp_path), 'user', 'pass', wait=0)
    assert res['status_code']
    assert res['errors'] is None
    kwargs = put.call_args.kwargs
    assert kwargs['files']['file'][0] == 'magic_contribution_test.txt'
    assert 'data' not in kwargs
    assert kwargs['params'] == {'id': 1}
    assert res['id'] == 1


def test_upload_returns_the_id_of_a_newly_created_private_contribution(tmp_path):
    # uploading to a public contribution's ID makes a new private one
    with patch('pmagpy.ipmag.requests.put', return_value=fake_response(202, {'id': 2})):
        res = ipmag.upload_to_private_contribution(1, upload_file(tmp_path), 'user', 'pass', wait=0)
    assert res['status_code']
    assert res['id'] == 2


def test_a_204_names_the_missing_private_contribution(tmp_path):
    response = fake_response(204, None)
    response.json.side_effect = ValueError('no body')
    with patch('pmagpy.ipmag.requests.delete', return_value=response):
        res = ipmag.delete_private_contribution(1, 'user', 'pass')
    assert not res['status_code']
    assert 'No private contribution with ID 1' in res['errors']


def test_validate_returns_errors_and_warnings():
    errors = [{'table': 'contribution', 'column': 'lab_names', 'message': 'missing', 'rows': [1]}]
    warnings = [{'table': 'sites', 'column': 'age', 'message': 'odd', 'rows': [2]}]
    response = fake_response(200, {'validation': {'errors': errors, 'warnings': warnings}})
    with patch('pmagpy.ipmag.requests.put', return_value=response):
        res = ipmag.validate_private_contribution(1, 'user', 'pass', verbose=False)
    assert res['status_code']
    assert res['errors'] is None
    assert res['validation_results'] == errors
    assert res['validation_warnings'] == warnings


def test_validate_null_errors_and_warnings_are_empty_lists():
    response = fake_response(200, {'validation': {'errors': None, 'warnings': None}})
    with patch('pmagpy.ipmag.requests.put', return_value=response):
        res = ipmag.validate_private_contribution(1, 'user', 'pass', verbose=False)
    assert res['status_code']
    assert res['validation_results'] == []
    assert res['validation_warnings'] == []


@pytest.mark.parametrize('status, body', [
    (200, ValueError('not JSON')),
    (200, {'validation': None}),
    (200, {'validation': ['not', 'a', 'dict']}),
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


def test_upload_waits_for_processing_only_after_success(tmp_path):
    with patch('pmagpy.ipmag.requests.put', return_value=fake_response(202, {'id': 1})), \
         patch('pmagpy.ipmag.time.sleep') as sleep:
        ipmag.upload_to_private_contribution(1, upload_file(tmp_path), 'user', 'pass', wait=7)
    sleep.assert_called_once_with(7)
    with patch('pmagpy.ipmag.requests.put', return_value=fake_response(500, {})), \
         patch('pmagpy.ipmag.time.sleep') as sleep:
        ipmag.upload_to_private_contribution(1, upload_file(tmp_path), 'user', 'pass', wait=7)
    sleep.assert_not_called()


@pytest.mark.parametrize('status', [401, 500])
def test_upload_failure_has_id_none(tmp_path, status):
    body = {'errors': [{'message': 'nope'}]}
    with patch('pmagpy.ipmag.requests.put', return_value=fake_response(status, body)):
        res = ipmag.upload_to_private_contribution(1, upload_file(tmp_path), 'user', 'pass', wait=0)
    assert not res['status_code']
    assert res['id'] is None
    assert res['errors'] == 'nope'


def test_upload_missing_file_has_id_none(tmp_path):
    with patch('pmagpy.ipmag.requests.put') as put:
        res = ipmag.upload_to_private_contribution(1, str(tmp_path / 'missing.txt'), 'user', 'pass')
    put.assert_not_called()
    assert not res['status_code']
    assert res['id'] is None
    assert res['errors']


def test_delete_success_errors_is_none():
    with patch('pmagpy.ipmag.requests.delete', return_value=fake_response(200, {'rowsDeleted': 3})):
        res = ipmag.delete_private_contribution(1, 'user', 'pass')
    assert res['status_code']
    assert res['errors'] is None
    assert res['id'] == 1


@pytest.mark.parametrize('method, call', [
    ('post', lambda: ipmag.create_private_contribution('user', 'pass')),
    ('delete', lambda: ipmag.delete_private_contribution(1, 'user', 'pass')),
    ('put', lambda: ipmag.validate_private_contribution(1, 'user', 'pass', verbose=False)),
])
def test_requests_have_a_timeout_and_a_timeout_returns_an_error(method, call):
    with patch('pmagpy.ipmag.requests.' + method,
               side_effect=requests.exceptions.Timeout('timed out')) as request:
        res = call()
    assert request.call_args.kwargs['timeout'] == ipmag.EARTHREF_TIMEOUT
    assert not res['status_code']
    assert res['errors'] == 'timed out'


def test_upload_request_has_a_timeout(tmp_path):
    with patch('pmagpy.ipmag.requests.put', return_value=fake_response(202, {'id': 1})) as put:
        ipmag.upload_to_private_contribution(1, upload_file(tmp_path), 'user', 'pass', wait=0)
    assert put.call_args.kwargs['timeout'] == ipmag.EARTHREF_TIMEOUT
