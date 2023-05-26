'''
Template Component main class.

'''
import logging

# configuration variables
import snowflake
from keboola.component import UserException
from keboola.component.base import ComponentBase
from snowflake.connector import SnowflakeConnection

from configuration import Configuration

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

            logging.info(f'Executing procedure: {query}')

            res = self.run_query(query, self._configuration.procedure_parameters)
            logging.info(res)
        finally:
            self._connection.close()

    def _create_connection(self):
        self._connection = snowflake.connector.connect(
            user=self._configuration.username,
            password=self._configuration.pswd_password,
            account=self._configuration.account,
            database=self._configuration.database,
            schema=self._configuration.schema,
            warehouse=self._configuration.warehouse
        )

    def _init_configuration(self) -> None:
        self.validate_configuration_parameters(Configuration.get_dataclass_required_parameters())
        self._configuration: Configuration = Configuration.load_from_dict(self.configuration.parameters)

    def _build_exec_query(self, procedure_name: str, parameters):
        # validate
        errors = set()
        errors.add(self._validate_procedure_argument(procedure_name))

        query = f'CALL {procedure_name}'
        if parameters:
            par_arr_string = ', '.join([f':{i+1}' for i, p in enumerate(parameters)])
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
