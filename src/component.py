'''
Template Component main class.

'''
import logging

# configuration variables
import snowflake
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from keboola.component import UserException
from keboola.component.base import ComponentBase
from snowflake.connector import SnowflakeConnection

from configuration import Configuration, ProcedureParameters

REQUIRED_IMAGE_PARS = []


class Component(ComponentBase):

    def __init__(self):
        super().__init__()
        self._connection: SnowflakeConnection

    def run(self):
        '''
        Main execution code
        '''

        self._init_configuration()

        self._create_connection()
        try:
            query = self._build_exec_query(self._configuration.name, self._configuration.procedure_parameters)

            parameters = self._get_parameters()

            logging.info(f'Executing procedure: {query}, parameters: {parameters}')
            res = self.run_query(query, parameters)

            logging.info(f"The result of the call is: {res}")
        finally:
            self._connection.close()

    def _create_connection(self):
        self._connection = snowflake.connector.connect(
            user=self._configuration.username,
            account=self._configuration.account,
            database=self._configuration.database,
            schema=self._configuration.schema,
            warehouse=self._configuration.warehouse,
            **self._get_auth_parameters()
        )

    def _get_auth_parameters(self) -> dict:
        """Build the auth-specific ``connect()`` kwargs based on ``auth_type``.

        'key_pair' loads the configured private key and connects with JWT authentication;
        'password' (the default) keeps the original password authentication. The field for
        the selected type must be set, otherwise it is a user error.
        """
        if self._configuration.auth_type == 'key_pair':
            if not self._configuration.pswd_private_key:
                raise UserException("Authentication Type is 'Key Pair' but no Private Key is "
                                    "configured in the connection settings.")
            private_key = self._load_private_key(self._configuration.pswd_private_key,
                                                 self._configuration.pswd_private_key_passphrase)
            return {'private_key': private_key, 'authenticator': 'SNOWFLAKE_JWT'}
        if not self._configuration.pswd_password:
            raise UserException("Authentication Type is 'Password' but no Password is "
                                "configured in the connection settings.")
        return {'password': self._configuration.pswd_password}

    @staticmethod
    def _load_private_key(private_key_pem: str, passphrase: str) -> bytes:
        """Parse a PEM (PKCS#8) private key and return it as DER bytes for the Snowflake connector."""
        try:
            p_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=passphrase.encode('utf-8') if passphrase else None
            )
        except (ValueError, TypeError, UnsupportedAlgorithm) as e:
            raise UserException('Failed to load the Snowflake private key. Ensure it is a valid '
                                'PEM-formatted PKCS#8 key and the passphrase (if any) is correct.') from e
        return p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    def _init_configuration(self) -> None:
        self.validate_configuration_parameters(Configuration.get_dataclass_required_parameters())
        self._configuration: Configuration = Configuration.load_from_dict(self.configuration.parameters)

    def _build_exec_query(self, procedure_name: str, parameters: list[ProcedureParameters]):
        # validate
        errors = set()
        errors.add(self._validate_procedure_argument(procedure_name))

        query = f'CALL {procedure_name}'
        if parameters:
            par_arr_string = ', '.join([' %s' for p in parameters])
            query += f'({par_arr_string})'
        else:
            query += '()'

        return query

    def _validate_procedure_argument(self, arg):
        invalid_characters = [' ', ';']
        error = None
        if any(char in arg for char in invalid_characters):
            error = f'Invalid argument {arg}!'
        return error

    def run_query(self, query: str, parameters: list):
        results = []
        cur = self._connection.cursor()
        try:
            cur.execute(query, tuple(parameters))
            columns = [column[0] for column in cur.description]
            for row in cur.fetchall():
                results.append(dict(zip(columns, row)))
        except Exception as e:
            raise UserException(e) from e
        finally:
            cur.close()

        return results

    def _get_parameters(self) -> list:
        parameters = []
        for p in self._configuration.procedure_parameters:
            value = p.value
            if not value and p.nullable:
                value = None
            parameters.append(value)
        return parameters


"""
        Main entrypoint
"""
if __name__ == "__main__":
    try:
        comp = Component()
        comp.run()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
