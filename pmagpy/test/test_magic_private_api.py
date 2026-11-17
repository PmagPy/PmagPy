"""ipmag.upload_to_private_contribution, with the EarthRef API mocked.

The EarthRef API (https://api.earthref.org/v1/openapi.yaml) takes uploads to a private contribution as
multipart/form-data in a field named "file"; a text/plain body is rejected with HTTP 500.
"""
from unittest.mock import Mock, patch

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

