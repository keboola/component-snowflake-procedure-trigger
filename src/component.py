'''
Template Component main class.

'''
import logging

import snowflake.connector
from keboola.component import UserException
from keboola.component.base import ComponentBase
# configuration variables
from snowflake.connector import SnowflakeConnection

from configuration import Configuration

KEY_DATABASE = 'database'
KEY_USER = 'user_name'
KEY_PASSWORD = '#password'
KEY_SERVER = 'server'

KEY_NAME = 'name'
KEY_VALUE = 'value'
KEY_PROC_PARAMETERS = 'procedure_parameters'

# list of mandatory parameters => if some is missing,
# component will fail with readable message on initialization.
REQUIRED_PARAMETERS = [KEY_DATABASE,
                       KEY_USER,
                       KEY_PASSWORD,
                       KEY_SERVER]
REQUIRED_IMAGE_PARS = []

# Set your account and login information (replace the variables with the necessary values).
ACCOUNT = '<account_identifier>'
USER = '<login_name>'
PASSWORD = '<password>'


class Component(ComponentBase):
    """
        Extends base class for general Python components. Initializes the CommonInterface
        and performs configuration validation.

        For easier debugging the data folder is picked up by default from `../data` path,
        relative to working directory.

        If `debug` parameter is present in the `config.json`, the default logger is set to verbose DEBUG mode.
    """

    def __init__(self):
        super().__init__(required_parameters=REQUIRED_PARAMETERS,
                         required_image_parameters=REQUIRED_IMAGE_PARS)

        self._connection: SnowflakeConnection

    def run(self):
        '''
        Main execution code
        '''
        params = self.configuration.parameters

        self._init_configuration()

        proc_params = self._get_parameters()

        self._create_connection()
        try:
            query = self._build_exec_query(params[KEY_NAME], **proc_params)

            logging.info(f'Executing procedure: {query}')

            res = self.run_query(query)
            logging.info(res)
        finally:
            self._connection.close()

    def _create_connection(self):
        self._connection = snowflake.connector.connect(
            user=self._configuration.username,
            password=self._configuration.pswd_password,
            account=self._configuration.account,
            warehouse=self._configuration.warehouse
        )

    def _init_configuration(self) -> None:
        self.validate_configuration_parameters(Configuration.get_dataclass_required_parameters())
        self._configuration: Configuration = Configuration.load_from_dict(self.configuration.parameters)

    def _get_parameters(self):
        parameters = self._configuration.procedure_parameters
        parameters_dict = {}
        for par in parameters:
            parameters_dict[par.name] = par.value
        return parameters_dict

    def _build_exec_query(self, procedure_name: str, **parameters):
        # validate
        errors = set()
        errors.add(self._validate_procedure_argument(procedure_name))

        query = ['EXEC', procedure_name]
        procedure_arguments = []
        for par in parameters:
            # validate
            errors.add(self._validate_procedure_argument(par))
            errors.add(self._validate_procedure_argument(parameters[par]))

            procedure_arguments.append(f'@{par} = {parameters[par]}')
        query.append(', '.join(procedure_arguments))
        query.append(';')

        # remove Nones
        errors.discard(None)
        if errors:
            raise UserException(f'{"; ".join(errors)}')

        return ' '.join(query)

    def _validate_procedure_argument(self, arg):
        invalid_characters = [' ', ';']
        error = None
        if any(char in arg for char in invalid_characters):
            error = f'Invalid argument {arg}!'
        return error

    def run_query(self, query):
        results = []
        cur = self._connection.cursor()
        try:
            cur.execute(query)
            columns = [column[0] for column in cur.description]
            for row in cur.fetchall():
                results.append(dict(zip(columns, row)))
        except Exception as e:
            raise UserException(e) from e
        finally:
            cur.close()

        return results


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
