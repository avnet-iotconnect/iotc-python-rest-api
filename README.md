# iotc-python-rest-api
This project is the Python interface for 
IoTConnect REST API. 
This project provides a limited set of essential REST API implementations,
but aims to provide a solid design that can be easily expanded by future 
feature additions or even customers to support additional REST API implementations.

The project provides a reference CLI implementation as well, with reduced
functionality when compared to the native python API support.

At this stage, the supports API cover the following set of basic features:
* Obtaining details about devices, templates, entities, IoTConnect users, OTA firmwares and firmware upgrades.
* Creating and deleting templates based on template JSON and x509 authentication based devices.
* Creating and deleting OTA firmware and firmware upgrade entries, along with the ability to upload firmware files
  in order to upgrade firmware on your devices. 
* Generating an ECC x509 self-signed certificate and a matching private key
* Generating iotcDeviceConfig.json which can be used along with certificates
to provide zero-touch configuration for our Python SDK MQTT clients, 
like the [Python Lite SDK](https://github.com/avnet-iotconnect/iotc-python-lite-sdk),
based on your account settings. 


At the design level, the project infrastructure provides:
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

### Getting Started

This package does not distribute these example scripts. These example scripts 
like *iotccli.py* and *iotccli.sh* would 
need to be cloned with Git or downloaded separately from this repository.

To get familiar with supported commands, first run the cmd.py script form the examples:

```shell
cd examples
python3 iotccli.py --help
```

You can specify explicitly, or override the environment values by passing command line arguments to the configure tool. 

Check the documentation for the main CLI and the configure command and choose your method to configure the REST API using
either command line arguments or [environment variables](#configuration-environment-variables):

```shell
python3 iotccli.py --help
python3 iotccli.py configure --help
```

Use your credentials to configure the API:

```shell
# On Linux and similar, for security reasons, ensure this variable is set accordingly.
# We don't want our password to be stored in history, so this is the safest way to avoid having the password stored in plain text.
# Alternatively you can also export IOTC_PASS in your .profile or windows environment variables panel.
export HISTCONTROL=ignoreboth
 
# ... then add space in front of the line below:
 python3 iotccli.py configure -u my@email.com -p "MyPassword" --pf az --env avnet --skey=MYSOLUTIONKEY  
```

You can also invoke the basic CLI with a simple python3 command without a script, for example to get help on the CLI interface and list available commands:

```shell
python3 -c "import sys; import avnet.iotconnect.restapi.cli.main as cli; cli.process(sys.argv[1:])" --help
```

Once the CLI is configured, API can be invoked to, for example, to create a device in your account.

*iotccli.sh* or the above python scripts and methods can be used interchangeably:

```shell
# create the template and use a different template code and name than the one in the template json:
./iotccli.sh create-template ./sample-device-template.json --code=apidemo --name=apidemo
# prepare a new automatically generated certificate for our device that we will create
# this step creates device-cert.pem and device-pkey.pem
./iotccli.sh generate-cert apidemo-device01
# create a new device apidemo-device01 with the generated cert (default cert from previous step picked up)
./iotccli.sh create-device apidemo apidemo-device01
```

Now that our device is fully configured, we can download run the python SDK:

```shell
# use curl or wget to download the SDK package
curl -sOJ 'https://downloads.iotconnect.io/sdk/python/iotconnect_sdk_lite-1.0.0-py3-none-any.whl
python3 -m pip install iotconnect_sdk_lite-1.0.0-py3-none-any.whl
python3 ./lite-sdk-example.py
```

When done testing or evaluating, the device should be deleted, as it  will not be possible
to use the IoTConnect Web UI to delete it:

```shell
./iotccli.sh delete-device apidemo-device01
./iotccli.sh delete-template apidemo-device01
```

### API Usage with Python

To learn how to use the API, is suggested to start with the [examples/basic-api-example.py](examples/basic-api-example.py),
and then it would be best to get familiar with the [unit tests](./tests).

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
