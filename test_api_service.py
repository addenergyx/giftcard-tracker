import pytest
from unittest.mock import Mock, patch

from common_shared_library import CaptchaBypass

from GiftCardAPIService import GiftCardAPIService


@pytest.fixture
def captcha_bypass_mock():
    captcha = Mock(spec=CaptchaBypass)
    captcha.bypass.return_value = 'dummy_captcha_response'
    return captcha

@pytest.fixture
def service(captcha_bypass_mock):
    return GiftCardAPIService(captcha_bypass=captcha_bypass_mock)

def test_get_balance_success(service):
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'response_code': '00',
            'new_balance': '00100'
        }
        balance = service.get_balance('1234567890123456', '1234')
        assert balance == 1.00

def test_get_balance_failure_status_code(service):
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 404
        balance = service.get_balance('1234567890123456', '1234')
        assert balance is None

def test_get_balance_invalid_response_code(service):
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'response_code': '01',
            'new_balance': '00100'
        }
        balance = service.get_balance('1234567890123456', '1234')
        assert balance is None
