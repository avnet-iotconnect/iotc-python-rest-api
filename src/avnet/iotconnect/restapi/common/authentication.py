"""This module provides IoTConnect authentication functionality."""

import argparse
import requests
from .constants import API_AUTH_URL, BASIC_TOKEN, LOGIN
from .check_status import check_status


class Credentials:
    """This class allows storing IoTConnect credentials."""

    def __init__(self, username, password, solution_key):
        self.__username = username
        self.__password = password
        self.__solution_key = solution_key
    
    def get_username(self) -> str:
        """username getter"""
        return self.__username

    def get_password(self) -> str:
        """password getter"""
        return self.__password

    def get_solution_key(self) -> str:
        """solution key getter"""
        return self.__solution_key


def get_basic_token() -> str:
    """Get basic token from the IoT Connect and return it."""
    response = requests.get(API_AUTH_URL + BASIC_TOKEN)
    check_status(response)
    response_json = response.json()
    # print(response_json)
    basic_token = response_json["data"]
    print("Basic token: " + basic_token)
    return basic_token

def get_credentials(username: str, password: str, solution_key: str) -> Credentials:
    """
    Get credentials from CLI arguments
     - username
     - password
     - solution key
    """
    print("Parse command line arguments")
    credentials = Credentials(username, password, solution_key)
    return credentials

def authenticate(username: str, password: str, solution_key: str) -> str:
    """Get access token from IoT Connect and return it. Entrance point to this module"""
    credentials = get_credentials(username, password, solution_key)
    print(f"Authenticate with Username which starts with: {credentials.get_username()[:5]}")
    basic_token = get_basic_token()
    headers = {
        "Content-type": "application/json",
        "Accept": "*/*",
        "Authorization": 'Basic %s' % basic_token,
        "Solution-key": credentials.get_solution_key()
    }
    login_creds = {
        "username": credentials.get_username(),
        "password": credentials.get_password()
    }
    response = requests.post(API_AUTH_URL + LOGIN, json = login_creds, headers = headers)
    check_status(response)
    response_json = response.json()
    access_token = str('Bearer %s' % response_json["access_token"])
    refresh_token = response_json["refresh_token"]
    print("refresh token: " + refresh_token)
    print("Successful authentication. Access Token:\r\n" + access_token)
    return access_token
