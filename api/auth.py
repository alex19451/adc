
from requests.api import post
import gitlab
from gitlab.exceptions import GitlabAuthenticationError
from tools import get_custom_logger


class Gitlab:
    def __init__(self, token, url):
        self.token = token
        self.gitlab_url = f"https://{url}/"
        self.__logger = get_custom_logger('[ADC]', f'url',"INFO")


    def gitlab_connect(self):
        """Authenticate the GL wrapper with Gitlab.

        Args:
            token (str): The Gitlab token to authenticate with.
                Defaults to: None.
        """
        try:
            gitlab_client = gitlab.Gitlab(self.gitlab_url, self.token)
            gitlab_client.auth()
            self.__logger.log(20, f'Client {gitlab_client}')
            return gitlab_client
        except GitlabAuthenticationError as e:
            self.__logger.log(40, f'Client {e}')
            return False
