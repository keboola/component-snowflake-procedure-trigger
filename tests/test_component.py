'''
Created on 12. 11. 2018

@author: esner
'''
import unittest
import mock
import os
from freezegun import freeze_time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from component import Component
from configuration import Configuration
from keboola.component import UserException


def _generate_private_key_pem(passphrase: str = None) -> str:
    """Generate a throwaway RSA private key as a PEM (PKCS#8) string, optionally encrypted."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    if passphrase:
        encryption = serialization.BestAvailableEncryption(passphrase.encode('utf-8'))
    else:
        encryption = serialization.NoEncryption()
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption
    )
    return pem.decode('utf-8')


def _make_component(configuration: Configuration) -> Component:
    """Build a Component instance without the full ComponentBase datadir bootstrap and inject config."""
    comp = Component.__new__(Component)
    comp._configuration = configuration
    return comp


def _base_config(**overrides) -> Configuration:
    params = dict(account='acc', username='user', warehouse='wh', name='PROC')
    params.update(overrides)
    return Configuration(**params)


class TestComponent(unittest.TestCase):

    # set global time to 2010-10-10 - affects functions like datetime.now()
    @freeze_time("2010-10-10")
    # set KBC_DATADIR env to non-existing dir
    @mock.patch.dict(os.environ, {'KBC_DATADIR': './non-existing-dir'})
    def test_run_no_cfg_fails(self):
        with self.assertRaises(ValueError):
            comp = Component()
            comp.run()

    @mock.patch('snowflake.connector.connect')
    def test_password_auth_unchanged(self, m_connect):
        """The original password authentication path is preserved (auth_type defaults to 'password')."""
        comp = _make_component(_base_config(pswd_password='secret'))
        comp._create_connection()

        _, kwargs = m_connect.call_args
        self.assertEqual(kwargs['password'], 'secret')
        self.assertEqual(kwargs['user'], 'user')
        self.assertEqual(kwargs['account'], 'acc')
        self.assertEqual(kwargs['warehouse'], 'wh')
        self.assertNotIn('private_key', kwargs)
        self.assertNotIn('authenticator', kwargs)

    @mock.patch('snowflake.connector.connect')
    def test_password_auth_missing_password_raises(self, m_connect):
        """auth_type 'password' with no password configured is a clear user error."""
        comp = _make_component(_base_config(auth_type='password'))
        with self.assertRaises(UserException):
            comp._create_connection()
        m_connect.assert_not_called()

    @mock.patch('snowflake.connector.connect')
    def test_keypair_auth(self, m_connect):
        """auth_type 'key_pair' switches to JWT auth with DER key bytes and no password."""
        comp = _make_component(_base_config(auth_type='key_pair',
                                            pswd_private_key=_generate_private_key_pem()))
        comp._create_connection()

        _, kwargs = m_connect.call_args
        self.assertIsInstance(kwargs['private_key'], bytes)
        self.assertEqual(kwargs['authenticator'], 'SNOWFLAKE_JWT')
        self.assertNotIn('password', kwargs)

    @mock.patch('snowflake.connector.connect')
    def test_keypair_auth_encrypted_key(self, m_connect):
        """An encrypted private key is unlocked with the configured passphrase."""
        pem = _generate_private_key_pem(passphrase='topsecret')
        comp = _make_component(_base_config(auth_type='key_pair', pswd_private_key=pem,
                                            pswd_private_key_passphrase='topsecret'))
        comp._create_connection()

        _, kwargs = m_connect.call_args
        self.assertIsInstance(kwargs['private_key'], bytes)
        self.assertEqual(kwargs['authenticator'], 'SNOWFLAKE_JWT')

    @mock.patch('snowflake.connector.connect')
    def test_keypair_missing_key_raises(self, m_connect):
        """auth_type 'key_pair' with no private key configured is a clear user error."""
        comp = _make_component(_base_config(auth_type='key_pair'))
        with self.assertRaises(UserException):
            comp._create_connection()
        m_connect.assert_not_called()

    @mock.patch('snowflake.connector.connect')
    def test_auth_type_password_ignores_private_key(self, m_connect):
        """auth_type drives the choice: 'password' uses the password even if a key is also present."""
        comp = _make_component(_base_config(auth_type='password', pswd_password='secret',
                                            pswd_private_key=_generate_private_key_pem()))
        comp._create_connection()

        _, kwargs = m_connect.call_args
        self.assertEqual(kwargs['password'], 'secret')
        self.assertNotIn('private_key', kwargs)

    @mock.patch('snowflake.connector.connect')
    def test_invalid_private_key_raises(self, m_connect):
        """A malformed private key raises a UserException rather than an opaque crash."""
        comp = _make_component(_base_config(auth_type='key_pair', pswd_private_key='not-a-real-key'))
        with self.assertRaises(UserException):
            comp._create_connection()
        m_connect.assert_not_called()

    @mock.patch('snowflake.connector.connect')
    def test_wrong_passphrase_raises(self, m_connect):
        """A wrong passphrase for an encrypted key raises a UserException."""
        pem = _generate_private_key_pem(passphrase='correct')
        comp = _make_component(_base_config(auth_type='key_pair', pswd_private_key=pem,
                                            pswd_private_key_passphrase='wrong'))
        with self.assertRaises(UserException):
            comp._create_connection()
        m_connect.assert_not_called()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
