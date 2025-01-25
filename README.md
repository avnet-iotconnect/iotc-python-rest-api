# iotc-python-rest-api
This project is the Python interface for 
IoTConnect REST API. 
The goal of this project, at this stage, is to provide an initial 
design and infrastructure that the future
tasks will expand upon, in order to provide a larger set of API support.

At this stage, the API supports this set of basic features:
* Obtaining details about devices, templates, entities, your IoTConnect user, OTA firmwares and firmware upgrades.
* Creating and deleting templates based on template JSON and x509 authentication based devices.
* Creating and deleting OTA firmware and firmware upgrade entries, along with the ability to upload firmware files
  in order to upgrade firmware on your devices. 
* Generating an ECC x509 self-signed certificate and a matching private key.

At the design level, the project infrastructure provides:
* A uniform way to configure REST API endpoints based on your account settings.
* Authenticate, refresh and store the credentials into the OS user's home directories.
* Streamlined REST API calls and error reporting. 

### Rest API Credentials

This REST API implementation requires the user to authenticate with their IoTConnect
credentials, which in turn will store the session token into your 
home directory of your operating system. 

This token will be valid for 24 hours, unless it is extended automatically
when you use the API (see the section below).

### Automatic Token Refresh
By default, the API will attempt to refresh your session token (which is stored in your 
home directory) whenever you use any API calls. This refresh will as long as the 
last refresh occurred at least one hour (default) since the last time it was refreshed.

### Environment Variables Setup

In order to run this project, it is recommended to set the environment variables per table below:

| Name      | Description                                                                                       |
|-----------|---------------------------------------------------------------------------------------------------|
| IOTC_PF   | Platform of your IoTConnect account "aws" for AWS and "az" for Azure                              |
| IOTC_ENV  | Environment IoTconnect account. It can be found at Settings -> Key Vault in the IoTConnect Web UI |
| IOTC_SKEY | Your Solution Key                                                                                 |
| IOTC_USER | Your IoTconnect username (email)                                                                  |
| IOTC_PASS | Your IoTconnect password                                                                          |


With this, you can simply run the cmd.py script form the examples with:

```shell
python3 iotccli.py
```

You can specify explicitly, or override the environment values by passing command line arguments to the configure tool. See:

```shell
python3 iotccli.py configure --help
```

Or even invoke the basic CLI with a simple python3 command without a script, for example to get help on the CLI interface and list available commands:

```shell
python3 -c "import sys; import avnet.iotconnect.restapi.cli.main as cli; cli.process(sys.argv[1:])" --help
```

Once the CLI is configured, you can run this basic example to create and device in your account:
```shell
TODO
```
It is still advisable to use the environment variable for your password 
on Linux systems. Commands would be recorded in your shell history by default,
which could present a security risk.


### Special Environment Variables 

| Name                      | Description                                                                                  |
|---------------------------|----------------------------------------------------------------------------------------------|
| IOTC_API_TRACE            | Setting this to any value will add add extra information to REST calls and some debug info.  |
| IOTC_API_NO_TOKEN_REFRESH | Setting this to any value will disable the automatic token refresh                           |
