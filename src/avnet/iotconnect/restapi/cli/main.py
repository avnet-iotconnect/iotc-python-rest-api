import argparse

from avnet.iotconnect.restapi import CliCredentials


class CliApp:

    def __init__(self):
        main_help = \
            """ 
            Use IoTConnect REST API to perform account and device operations.
            Call iotccli authenticate first to log. This will create a session token which will be stored
            in your account. This token will be used and refreshed automatically in subsequent CLI invocations.
            """
        parser = argparse.ArgumentParser(
            prog='iotccli',
            description=help_text
        )

        self.register_configure(parser)
        CliCredentials.register_refresh(parser)

    @classmethod
    def _register_authenticate(self, ap: argparse.ArgumentParser) -> None:
        main_help = \
            """ 
            Configure IoTConnect credentials.
            Credentials from the environment will be used if arguments are not supplied.
            """
        ap.description = main_help
        ap.add_argument(
            "-u", "--username", dest="username", default=os.environ.get("IOTC_USER"),
            help="Your username/email - or use the IOTC_USER environment variable."
        )
        ap.add_argument(
            "-p", "--password", dest="password", default=os.environ.get("IOTC_PASSWORD"),
            help="your password. Be mindful of leaving this password in your OS command history and pass it as IOTC_PASSWORD environment variable instead."
        )
        ap.add_argument(
            "-pf", "--platform", dest="platform", choices=api_url.PF_CHOICES, default=os.environ.get("IOTC_PF") or apiurl.PF_AWS,
            help='account platform ("aws" for AWS, or "az" for azure) - or use the IOTC_ENV environment variable.'
        )
        ap.add_argument(
            "--env", dest="env", choices=api_url.ENV_CHOICES, default=os.environ.get("IOTC_ENV") or api_url.ENV_UAT,
            help='account solution environment - or use IOTC_ENV environment variable. NOTE: "poc" environment is usually "uat"'
        )

    @classmethod
    def _register_refresh(self, ap: argparse.ArgumentParser):
        main_help = \
            """ 
            Todo
            """
        ap.description = main_help

    @classmethod
    def _process_authenticate(self, a: argparse.Namespace) -> None:
        api_url.configure(api_url.default_endpoint_mapper(a.platform, a.env))
        c.authenticate(username=a.username, password=a.password)
        c.refresh_token()
        c.refresh_token()

    @classmethod
    def process_refresh(self, a: argparse.Namespace) -> None:
        c.refresh_token()



