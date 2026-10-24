"""Regression checks for wrong-context execution and misleading success."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


browser = load('run_browser_use')
cdp = load('cdp_direct')
PAGES = [
    {'id': 'one', 'url': 'https://example.test/account'},
    {'id': 'two', 'url': 'https://example.test/settings'},
]


class TargetSelection(unittest.TestCase):
    def test_missing_match_cannot_execute_on_first_tab(self):
        with patch.object(cdp, 'targets', return_value=PAGES):
            with self.assertRaisesRegex(RuntimeError, 'no page matches'):
                cdp.pick('unused', match='missing')

    def test_ambiguous_match_is_refused(self):
        with patch.object(cdp, 'targets', return_value=PAGES):
            with self.assertRaisesRegex(RuntimeError, 'ambiguous'):
                cdp.pick('unused', match='example.test')

    def test_no_selector_requires_single_page(self):
        with patch.object(cdp, 'targets', return_value=PAGES):
            with self.assertRaisesRegex(RuntimeError, 'ambiguous'):
                cdp.pick('unused')

    def test_exact_id_selects_requested_tab(self):
        with patch.object(cdp, 'targets', return_value=PAGES):
            self.assertEqual(cdp.pick('unused', target_id='two'), PAGES[1])

    def test_protocol_error_cannot_look_like_successful_null(self):
        ws = MagicMock()
        ws.recv.return_value = '{"id":1,"error":{"message":"denied"}}'
        with patch.object(cdp, 'pick', return_value={'webSocketDebuggerUrl': 'unused'}), patch.object(cdp.websocket, 'create_connection', return_value=ws):
            with self.assertRaisesRegex(RuntimeError, 'protocol error'):
                cdp.evaluate('unused', '1')
        ws.close.assert_called_once()


class ProfileSelection(unittest.TestCase):
    def test_explicit_profile_arguments(self):
        for args in (['chrome.exe', '--user-data-dir=C:/isolated'], ['chrome.exe', '--user-data-dir', 'C:/isolated']):
            self.assertEqual(browser.profile_from_process('chrome.exe', args), Path('C:/isolated'))

    def test_non_browser_listener_is_refused(self):
        with self.assertRaises(RuntimeError):
            browser.profile_from_process('python.exe', ['python.exe', '--user-data-dir=C:/isolated'])

    def test_renderer_is_not_profile_owner(self):
        with self.assertRaises(RuntimeError):
            browser.profile_from_process('chrome.exe', ['chrome.exe', '--type=renderer'])

    def test_wrong_listener_profile_is_refused(self):
        import psutil
        listener = MagicMock(status=psutil.CONN_LISTEN, pid=123)
        listener.laddr.port = 12345
        listener.laddr.ip = '127.0.0.1'
        proc = MagicMock()
        proc.name.return_value = 'chrome.exe'
        proc.cmdline.return_value = ['chrome.exe', '--user-data-dir=C:/other']
        with patch.object(psutil, 'net_connections', return_value=[listener]), patch.object(psutil, 'Process', return_value=proc):
            with self.assertRaisesRegex(RuntimeError, 'different browser profile'):
                browser.listener_pid(12345, Path('C:/requested'))

    def test_endpoint_reuse_and_browser_restart(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(browser, 'listener_pid', return_value=123):
            profile = Path(directory)
            active = profile / 'DevToolsActivePort'
            active.write_text('12345\n/devtools/browser/abc-123\n')
            first = browser.endpoint_for_profile(profile)
            self.assertEqual(browser.endpoint_for_profile(profile)['daemon'], first['daemon'])
            active.write_text('12345\n/devtools/browser/def-456\n')
            self.assertNotEqual(browser.endpoint_for_profile(profile)['daemon'], first['daemon'])

    def test_missing_endpoint_fails_without_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, 'Do not retry with automatic discovery'):
                browser.endpoint_for_profile(Path(directory))

    def test_normal_chrome_uses_patient_local_handshake(self):
        inherited = {'BU_CDP_WS': 'wrong', 'BU_CDP_URL': 'wrong', 'BU_NAME': 'wrong',
                     'BU_AUTOSPAWN': '1', 'PYTHONPATH': 'wrong', 'PYTHONHOME': 'wrong'}
        with patch.dict(os.environ, inherited):
            env = browser.browser_env(
                {'websocket': 'selected', 'daemon': 'same-session'},
                normal_chrome=True,
            )
        self.assertEqual(env['BU_NAME'], 'same-session')
        for key in ('BU_CDP_WS', 'BU_CDP_URL', 'BU_AUTOSPAWN', 'PYTHONPATH', 'PYTHONHOME'):
            self.assertNotIn(key, env)
        self.assertEqual(env['BH_RUNTIME_DIR_SHARED'], '1')

    def test_isolated_profile_keeps_exact_websocket(self):
        env = browser.browser_env({'websocket': 'selected', 'daemon': 'same-session'})
        self.assertEqual(env['BU_CDP_WS'], 'selected')
        self.assertEqual(env['BU_NAME'], 'same-session')

    def test_normal_chrome_requires_verified_endpoint(self):
        with self.assertRaisesRegex(RuntimeError, 'verified endpoint'):
            browser.browser_env(None, normal_chrome=True)


if __name__ == '__main__':
    unittest.main()
