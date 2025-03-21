# iotc-python-rest-api
This project is the Python interface for IoTConnect REST API.

The project provides a limited set of essential Python interfaces for the IoTConnect REST API.
with the primary focus on to providing architecture that can be easily expanded by future 
feature additions. Additional REST API interfaces can be easily implemented 
by your custom applications when using the provided facilities.

The project provides a reference CLI implementation as well, with reduced
functionality when compared to the native python API support.

At this stage, the Python interface covers the following set of features 
with partial implementations covering most common use cases:
* Obtaining details about devices, templates, entities, IoTConnect users and OTA Firmware upgrades.
* Creating and Deleting templates based on template JSON and x509 authentication based devices.
* Managing OTA firmware and firmware upgrades, uploading files, scheduling and publishing OTA to devices.
* Sending commands to devices.
* Uploading and managing files IoTConnect File Storage.
* Creating and Deleting x509 authentication based devices.
* Generating an ECC x509 self-signed certificate and a matching private key
* Generating iotcDeviceConfig.json which can be used along with certificates
to provide streamlined configuration for our Python SDK MQTT clients, 
like the [Python Lite SDK](https://github.com/avnet-iotconnect/iotc-python-lite-sdk). 

At the architecture level, the project infrastructure provides:
* A uniform way to configure REST API endpoints based on your account settings.
* Authenticate, refresh and store the credentials into the OS user's home directories.
* Streamlined REST API calls and error reporting.


### Rest API Credentials

This REST API implementation requires the user to authenticate with their IoTConnect
credentials, which in turn will store the session token into your 
home directory of your operating system. 

This token will be valid for 24 hours, unless it is extended automatically
for another 24 hours when you use the API (see the section below).


### Automatic Token Refresh

By default, the API will attempt to refresh your session token, which is stored in your 
home directory, whenever you use any API calls. This refresh will trigger as long as the 
last refresh occurred at least one hour (default) since the last time it was refreshed.


### Installing

Install this package by running this command:

```shell
python3 -m pip install iotconnect-rest-api
```


### Getting Started

This package will install the **iotconnect-cli** utility, which can be invoked from command line.

This utility may be installed into different places depending on whether you install this package for all users, 
your user, or whether the package is installed from a Python virtual environment.
Therefore, ensure that the iotconnect-cli location is in the PATH environment variable.

To get familiar with supported commands, first run the iotconnect-cli script with --help parameter:

```shell
iotconnect-cli --help
```

Values can be specified explicitly on the command line, or as environment variables 
described in the [environment variables](#configuration-environment-variables) section:

```shell
iotconnect-cli configure --help
usage: iotconnect-cli configure [-h] [-u USERNAME] [-p PASSWORD] [-s SKEY] [--pf {aws,az}] [-e {poc,prod,avnet}]

Configure IoTConnect credentials. Credentials from the environment will be used if arguments are not supplied. This action will store these settings configuration file and allow you
to run this tool without authenticating for 24 hours since last authentication token (automatic) refresh. All arguments are required, but environment variables can be used instead.

options:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Your account username (email). IOTC_USER environment variable can be used instead.
  -p PASSWORD, --password PASSWORD
                        Your account password. IOTC_PASS environment variable can be used instead.
  -s SKEY, --skey SKEY  Your solution key. IOTC_SKEY environment variable can be used instead.
  --pf {aws,az}, --platform {aws,az}
                        account platform ("aws" for AWS, or "az" for Azure). IOTC_PF environment variable can be used instead.
  -e {poc,prod,avnet}, --env {poc,prod,avnet}
                        account environment - From settings -> Key Vault in the Web UI. IOTC_ENV environment variable can be used instead
```

IoTConnect Solution Key is required to use the API. You will need to request the solution key for your account
via the IoTConnect support ticket system available in the main menu of the IoTConnect web page.

Use your credentials to configure the API:

```shell
# On Linux and similar, for security reasons, ensure this variable is set accordingly.
# We don't want our password to be stored in history, so this is the safest way to avoid having the password stored in plain text.
# Alternatively, though this is still not a very secure approach, you can also export IOTC_PASS in 
# your .profile or windows environment variables panel for convenience.
export HISTCONTROL=ignoreboth
 
# ... then add space in front of the line below:
 iotconnect-cli configure -u my@email.com -p "MyPassword" --pf az --env avnet --skey=MYSOLUTIONKEY  
```

### Examples

Once the CLI is configured, API can be invoked to create a device in your account for example.

```shell
# ensure that sample-device-template.json from example is in the current directory
# clone this repo or copy the file locally
cd examples
# create the template and use a different template code and name than the one in the template json:
iotconnect-cli create-template ./sample-device-template.json --code=apidemo --name=apidemo
# prepare a new automatically generated certificate for our device that we will create
# this step creates device-cert.pem and device-pkey.pem
iotconnect-cli generate-cert apidemo-device01
# create a new device apidemo-device01 with the generated cert (default cert from previous step picked up)
iotconnect-cli create-device apidemo apidemo-device01
```

Now that our device is fully configured, we can install run the python SDK:

```shell
# ensure that sample-device-template.json from example is in the current directory
# clone this repo or copy the file locally
cd examples
python3 -m pip install iotconnect-sdk-lite
python3 lite-sdk-example.py
```

When done testing or evaluating, the device should be deleted, as it will not be possible
to use the IoTConnect Web UI to delete it:

```shell
iotconnect-cli delete-device apidemo-device01
iotconnect-cli delete-template apidemo-device01
```

### API Usage with Python

To learn how to use the API, is suggested to start with the [examples/basic-api-example.py](examples/basic-api-example.py),
and then get familiar with the [unit tests](./tests).


### Configuration Environment Variables

These variables can be used to store your credentials permanently:

| Name      | Description                                                                                       |
|-----------|---------------------------------------------------------------------------------------------------|
| IOTC_PF   | Platform of your IoTConnect account "aws" for AWS and "az" for Azure                              |
| IOTC_ENV  | Environment IoTconnect account. It can be found at Settings -> Key Vault in the IoTConnect Web UI |
| IOTC_SKEY | Your Solution Key                                                                                 |
| IOTC_USER | Your IoTconnect username (email)                                                                  |
| IOTC_PASS | Your IoTconnect password                                                                          |


### Special Environment Variables 

| Name                      | Description                                                                                        |
|---------------------------|----------------------------------------------------------------------------------------------------|
| IOTC_API_TRACE            | Setting this to any value will add add extra information to REST calls and some debug information. |
| IOTC_API_NO_TOKEN_REFRESH | Setting this to any value will disable the automatic token refresh.                                |
