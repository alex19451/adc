from bottle import request
from config import *
from api.auth import Gitlab
from tools import get_custom_logger
from tools import retry_with_active

class GitApi:
    def __init__(self, token, url):
        self.git_auth_instance = Gitlab(token, url)
        self.__logger = get_custom_logger('[ADC]', f'users',"INFO")
        self.data = self.git_auth_instance.gitlab_connect()

    def commit_files_branch(self, file_name):
        """
        Add files gitlab server
        """
        project = self.data.projects.get(BRANCH_ID)
        if file_name == "l2m-users.dev":
            commit_message = "Update testing"
        elif file_name =="l2m-users.prod":
            commit_message = "Update prod"

        value = {
        'branch': BRANCH,
        'commit_message': commit_message,
        'actions': [
            {
                'action': 'update',
                'file_path': f'{file_name}',
                'content': open(f'{FILES_DIR}/{file_name}').read(),
            }
        ]
        }
        self.__logger.log(20, f'Payload {value}')
        commit = project.commits.create(value)
        self.__logger.log(20, f'Commit {commit}')
        if commit.stats.get('total') == 0:
            return "SKIPPED"
        else:
            result = self.get_pipelines()
            return result

    @retry_with_active(retries=8, sleep=3)
    def get_pipelines(self):
        project = self.data.projects.get(BRANCH_ID)
        pipeline = project.pipelines.get('latest')
        return pipeline

    @staticmethod
    def git_api_request():
        """
        Get cookies value
        """
        api_url = request.get_cookie('api_url', secret=secret)
        nm_token = request.get_cookie('nm_token', secret=secret)
        git_api_request = GitApi(nm_token, api_url)
        return git_api_request







