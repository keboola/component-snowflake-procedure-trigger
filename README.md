# Snowflake Procedure Trigger


=============

Application capable of executing stored procedures in Snowflake DWH.

**Table of contents:**

[TOC]


Configuration
=============

##Connection Parameters
 - Account (account) - [REQ] Account identifier of the Snowflake instance. This is a prefix of your Snowflake instance URL, e.g. <strong>keboola.eu-central-1</strong>.</br>See <a href='https://docs.snowflake.com/en/user-guide/connecting.html#your-snowflake-account-name'>the documentation for more information</a>.
 - Username (username) - [REQ] Snowflake user, which will be used to run queries.
 - Password (#password) - [REQ] A password authenticating the Snowflake user.
 - Warehouse (warehouse) - [REQ] Name of the Snowflake warehouse to be used.


##Parameters
 - Procedure name (name) - [REQ] Name of the procedure to execute.
 - Procedure Arguments (procedure_parameters) - [REQ] Arguments to passed to procedure.
   - Value - Arguments will be sent as string and the implicit conversion left to Snowflake engine. E.g. numbers, or dates YYYY-MM-DD are allowed
   - Nullable - Convert empty value to NULL

Sample Configuration
=============
```json
{
    "storage": {
        "input": {
            "files": [],
            "tables": [
                {
                    "source": "in.c-test.test",
                    "destination": "test.csv",
                    "limit": 50,
                    "columns": [],
                    "where_values": [],
                    "where_operator": "eq"
                }
            ]
        },
        "output": {
            "files": [],
            "tables": []
        }
    },
    "parameters": {
        "account": "keboola",
        "username": "SAPI_WORKSPACE_909662313",
        "#password": "SECRET_VALUE",
        "database": "SAPI_9239",
        "schema": "WORKSPACE_909662313",
        "warehouse": "KEBOOLA_PROD_SMALL",
        "name": "example_procedure",
        "procedure_parameters": [
            {
                "value": "23",
                "nullable": true
            },
            {
                "value": "\"Rubber); select 1; call sss(\"",
                "nullable": true
            },
            {
                "value": "",
                "nullable": true
            }
        ],
        "debug": true
    },
    "action": "run",
    "image_parameters": {
        "syrup_url": "https://syrup.keboola.com/"
    },
    "authorization": {
        "oauth_api": {
            "id": "OAUTH_API_ID",
            "credentials": {
                "id": "main",
                "authorizedFor": "Myself",
                "creator": {
                    "id": "1234",
                    "description": "me@keboola.com"
                },
                "created": "2016-01-31 00:13:30",
                "#data": "{\"refresh_token\":\"XXXXX-TOKEN\"}",
                "oauthVersion": "2.0",
                "appKey": "12345",
                "#appSecret": "123qwe-CiN"
            }
        }
    }
}
```

Output
======

List of tables, foreign keys, schema.

Development
-----------

If required, change local data folder (the `CUSTOM_FOLDER` placeholder) path to your custom path in
the `docker-compose.yml` file:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    volumes:
      - ./:/code
      - ./CUSTOM_FOLDER:/data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clone this repository, init the workspace and run the component with following command:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker-compose build
docker-compose run --rm dev
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the test suite and lint check using this command:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker-compose run --rm test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration
===========

For information about deployment and integration with KBC, please refer to the
[deployment section of developers documentation](https://developers.keboola.com/extend/component/deployment/)