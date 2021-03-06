"""This allows authorized requests to the Hakai API using the requests library.

Written by: Taylor Denouden and Chris Davis
Last updated: June 2017
"""

from __future__ import print_function

import os
import pickle
from builtins import input
from datetime import datetime
from pytz import utc
from requests_oauthlib import OAuth2Session
from time import mktime

class Client(OAuth2Session):
    """docstring for Client."""

    def __init__(self, api_root='https://hecate.hakai.org/api'):
        """Create a new Client class with credentials.

        Params:
            api_root: The base url of the hakai api you want to call.
                      Defaults to the production server.
        """
        self._client_id = (
            '289782143400-1f4r7l823cqg8fthd31ch4ug0thpejme'
            '.apps.googleusercontent.com'
        )
        self._credentials_file = os.path.expanduser('~/.hakai-api-credentials')
        self._api_root = api_root
        self._authorization_base_url = '%s/auth/oauth2' % api_root
        self._token_url = '%s/auth/oauth2/token' % api_root

        # Try to get cached credentials
        credentials = self._try_to_load_credentials()
        if credentials:
            self._credentials = credentials
        else:
            # Acquire and store credentials from web sign-in.
            credentials = self._get_credentials_from_web()
            # Cache the credentials
            self._save_credentials(credentials)
            self._credentials = credentials

        # Init the OAuth2Session parent class with credentials
        super(Client, self).__init__(token=self._credentials)

    @property
    def api_root(self):
        """Return the api base url."""
        return self._api_root

    @property
    def credentials(self):
        """Return the credentials object."""
        return self._credentials

    def _save_credentials(self, credentials):
        """Save the credentials object to a file."""
        with open(self._credentials_file, 'wb') as outfile:
            cache = {
                "api_root": self.api_root,
                "credentials": credentials
            }
            pickle.dump(cache, outfile)

    def _try_to_load_credentials(self):
        """Try to load the cached credentials file.

        Returns false if unsuccessful and returns credentials if success.
        """
        if not os.path.isfile(self._credentials_file):
            return False

        with open(self._credentials_file, 'rb') as infile:
            try:
                cache = pickle.load(infile)
                api_root = cache["api_root"]
                credentials = cache["credentials"]
            except (KeyError, ValueError):
                os.remove(self._credentials_file)
                return False

            now = int((mktime(datetime.now(tz=utc).timetuple()) + datetime.now(
                tz=utc).microsecond / 1000000.0))  # utc timestamp
            credentials_expired = now > credentials['expires_at']
            same_api = api_root == self._api_root

            if not same_api or credentials_expired:
                os.remove(self._credentials_file)
                return False
            return credentials

    def _get_credentials_from_web(self):
        """Get user credentials from a web sign-in.

        Returns false if unsuccessful and returns credentials if success.
        """
        # Acquire and store credentials from web sign-in.
        oauth2_session = OAuth2Session(self._client_id)
        authorization_url, state = oauth2_session.authorization_url(
            self._authorization_base_url)
        print('Please go here and authorize:')
        print(authorization_url)

        redirect_response = input('\nPaste the full redirect URL here:\n')
        return oauth2_session.fetch_token(
            self._token_url, authorization_response=redirect_response)
