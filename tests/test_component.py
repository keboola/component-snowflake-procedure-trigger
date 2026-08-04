'''
Created on 12. 11. 2018

@author: esner
'''
import unittest
import mock
import os
from freezegun import freeze_time
from keboola.component import UserException
from snowflake.connector.errors import OperationalError

from component import Component
from configuration import Configuration


class TestComponent(unittest.TestCase):

    # set global time to 2010-10-10 - affects functions like datetime.now()
    @freeze_time("2010-10-10")
    # set KBC_DATADIR env to non-existing dir
    @mock.patch.dict(os.environ, {'KBC_DATADIR': './non-existing-dir'})
    def test_run_no_cfg_fails(self):
        with self.assertRaises(ValueError):
            comp = Component()
            comp.run()


class TestCreateConnection(unittest.TestCase):
    """Covers the connection boundary without touching the KBC data dir."""

    @staticmethod
    def _configured_component() -> Component:
        component = Component.__new__(Component)
        component._configuration = Configuration(
            account='test-account',
            username='test-user',
            pswd_password='test-password',
            warehouse='test-warehouse',
            name='TEST_PROCEDURE',
            database='test-database',
            schema='test-schema'
        )
        return component

    @mock.patch('snowflake.connector.connect')
    def test_connect_succeeds_passes_configuration_through(self, mock_connect):
        component = self._configured_component()

        component._create_connection()

        self.assertIs(mock_connect.return_value, component._connection)
        mock_connect.assert_called_once_with(
            user='test-user',
            password='test-password',
            account='test-account',
            database='test-database',
            schema='test-schema',
            warehouse='test-warehouse'
        )

    @mock.patch('snowflake.connector.connect')
    def test_connect_failure_raises_user_exception(self, mock_connect):
        mock_connect.side_effect = OperationalError(
            msg='Failed to connect to DB. Incorrect username or password was specified.',
            errno=250001
        )
        component = self._configured_component()

        with self.assertRaises(UserException) as context:
            component._create_connection()

        message = str(context.exception)
        self.assertIn('Failed to connect to Snowflake', message)
        self.assertIn('Incorrect username or password was specified.', message)
        self.assertIsInstance(context.exception.__cause__, OperationalError)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
