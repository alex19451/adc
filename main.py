import json
import os

from tools import (yaml_writer, get_vars_values, to_hash_256,
                   get_custom_logger, upload_file, file_params)
from bottle import route, run, post, request, get, response, redirect, jinja2_view, static_file, BaseRequest, default_app, install
from config import *
from tools.gitlab_api import GitApi

logger = get_custom_logger('[ADC]', f'users', "INFO")


@route('/static/styles/<filepath:path>')
def load_static(filepath):
    return static_file(filepath, root='./static/styles')


@route('/static/js/<filepath:path>')
def load_static(filepath):
    return static_file(filepath, root='./static/js')


@route('/static/jquery/<filepath:path>')
def load_static(filepath):
    return static_file(filepath, root='./static/jquery')


@route('/static/images/<filepath:path>')
def load_static(filepath):
    return static_file(filepath, root='./static/images')


@route('/', method=['GET'])
@jinja2_view('static/html/index.html')
def index_page():
    """
    Home page
    """
    return {}


@route('/credentials', method=['GET', 'POST'])
@jinja2_view('static/html/adc/credentials.html')
def credentials():
    """
    Get credentials Gitlab
    """
    if request.method == 'POST':
        gitlab_token = request.forms.get('token')
        api_url = request.forms.get('api_url')
        response.set_cookie("api_url", api_url,
                            secret=secret, max_age=14400, path='/')
        response.set_cookie("nm_token", gitlab_token,
                            secret=secret, max_age=14400, path='/')
        gl = GitApi(gitlab_token, api_url)

        if gl.data == False:
            return {'credentials_status': False}
        else:
            return {'credentials_status': True}
    return {}


@route('/uploads/<file>', name='static')
def download_attachment(file):
    return static_file(file, root=f"{UPLOADS_DIR}/", download=file)


###### ADC Logging ################
@route('/log', method=['GET'])
@jinja2_view('static/html/log.html')
def log():
    log_file = f"log/[ADC]-users.log"
    if not os.path.isfile(log_file):
        open(log_file, 'a').close()
    with open(log_file, 'r') as f:
        data = f.readlines()
    return {'data': data}


@route('/adc_control', method=['GET', 'POST'])
@jinja2_view('static/html/adc/adc_control')
def adc_control():
    """
    Page user lists
    """
    env_value = request.get_cookie('env_value', secret=secret)
    deploy_status = ""
    if env_value:
        file_name = env_value[0]
    else:
        file_name = 'l2m-users.dev'
    environments = get_vars_values(VARS_DIR, 'environments.yaml')
    with open(os.path.join(FILES_DIR, file_name), "r") as file:
        parsed_json = json.load(file)
    yaml_writer(parsed_json, FILES_DIR, "user_list.yaml")
    users = get_vars_values(FILES_DIR, 'user_list.yaml')
    if request.method == 'POST':
        if request.forms.get('change_enviroment'):
            env_value = request.POST.getall('env_name')
            logger.log(20, f'Change env {env_value}')
            response.set_cookie("env_value", env_value,
                                secret=secret, max_age=14400, path='/')
            redirect("/adc_control")
        if request.forms.get('report_cities'):
            redirect("/cities")
        if request.forms.get('report_methods'):
            redirect("/methods")
        if request.forms.get('report_endpoints'):
            redirect("/endpoints")
        if request.forms.get('synchronization'):
            deploy_status = GitApi.git_api_request().commit_files_branch(file_name)
        if request.forms.get('view_user'):
            name = request.forms.get('user_name')
            return redirect('/user_view/{0}'.format(name))
        if request.forms.get('edit_user'):
            name = request.forms.get('user_name')
            logger.log(20, f'User edited {name}')
            return redirect('/user_edit/{0}'.format(name))
        if request.forms.get('add_user'):
            redirect('/user_add')
        if request.forms.get('apply_data'):
            name = request.forms.get('user_status')
            return static_file(file_name, root=FILES_DIR)
        if request.forms.get('delete_user'):
            name = request.forms.get('user_name')
            with open(os.path.join(FILES_DIR, file_name), mode='r+') as file:
                data = json.load(file)
                file.truncate(0)
                file.seek(0)
                for i, value in enumerate(data.get('users')):
                    if value.get('user') == name:
                        logger.log(
                            20, f'User deleted {name} with configs {value}')
                        del data.get('users')[i]
                json.dump(data, file, indent=4)
                file.close()
            redirect('/adc_control')

        if request.json and request.json.get('checkbox') == 'True':
            name = request.json.get('name')
            logger.log(20, f'User active {name}')
            with open(os.path.join(FILES_DIR, file_name), mode='r+') as file:
                data = json.load(file)
                file.truncate(0)
                file.seek(0)
                for i, value in enumerate(data.get('users')):
                    if value.get('user') == name:
                        data.get('users')[i]['enabled'] = 'true'
                json.dump(data, file, indent=4)
                file.close()
        if request.json and request.json.get('checkbox') == 'False':
            name = request.json.get('name')
            logger.log(20, f'User inactive {name}')
            with open(os.path.join(FILES_DIR, file_name), mode='r+') as file:
                data = json.load(file)
                file.truncate(0)
                file.seek(0)
                for i, value in enumerate(data.get('users')):
                    if value.get('user') == name:
                        data.get('users')[i]['enabled'] = 'false'
                json.dump(data, file, indent=4)
                file.close()

    return {'users': users.get('users'), "environments": environments, "file_name": file_name, "deploy_status":deploy_status}


@route('/cities', method=['GET', 'POST'])
@jinja2_view('static/html/adc/cities')
def adc_cities():
    """
    Page cities
    """
    if request.method == 'POST':
        if request.forms.get('add_city'):
            new_city = request.forms.get('city_name')
            logger.log(20, f'Add new city {new_city}')
            data = get_vars_values(VARS_DIR, 'cities.yaml')
            if not (new_city in (data.get('changeable') + data.get('visible'))) and new_city:
                data['changeable'].append(new_city)
                yaml_writer(data, VARS_DIR, 'cities.yaml')
        if request.forms.get('delete_city'):
            del_city = request.forms.get('city_name')
            logger.log(20, f'City  deleted {del_city}')
            data = get_vars_values(VARS_DIR, 'cities.yaml')
            if (del_city in (data.get('changeable') + data.get('visible'))):
                data['changeable'].remove(del_city)
                yaml_writer(data, VARS_DIR, 'cities.yaml')
    cities = get_vars_values(VARS_DIR, 'cities.yaml')
    return {'cities': cities}


@route('/methods', method=['GET', 'POST'])
@jinja2_view('static/html/adc/methods')
def adc_methods():
    """
    Page methods
    """
    if request.method == 'POST':
        if request.forms.get('add_method'):
            new_method = request.forms.get('method_name')
            logger.log(20, f'Add new method {new_method}')
            data = get_vars_values(VARS_DIR, 'methods.yaml')
            if not (new_method in (data.get('changeable') + data.get('visible'))) and new_method:
                data['changeable'].append(new_method)
                yaml_writer(data, VARS_DIR, 'methods.yaml')
        if request.forms.get('delete_method'):
            del_method = request.forms.get('method_name')
            logger.log(20, f'Delete method {del_method}')
            data = get_vars_values(VARS_DIR, 'methods.yaml')
            if (del_method in (data.get('changeable') + data.get('visible'))):
                data['changeable'].remove(del_method)
                yaml_writer(data, VARS_DIR, 'methods.yaml')
    methods = get_vars_values(VARS_DIR, 'methods.yaml')
    return {'methods': methods}


@route('/endpoints', method=['GET', 'POST'])
@jinja2_view('static/html/adc/endpoints')
def adc_endpoints():
    """
    Page endpoints
    """
    if request.method == 'POST':
        if request.forms.get('add_endpoint'):
            new_endpoint = request.forms.get('endpoint_name')
            logger.log(20, f'Add new endpoint {new_endpoint}')
            data = get_vars_values(VARS_DIR, 'endpoints.yaml')
            if not (new_endpoint in (data.get('changeable') + data.get('visible'))) and new_endpoint:
                data['changeable'].append(new_endpoint)
                yaml_writer(data, VARS_DIR, 'endpoints.yaml')
        if request.forms.get('delete_endpoint'):
            del_endpoint = request.forms.get('endpoint_name')
            logger.log(20, f'Delete endpoint {del_endpoint}')
            data = get_vars_values(VARS_DIR, 'endpoints.yaml')
            if (del_endpoint in (data.get('changeable') + data.get('visible'))):
                data['changeable'].remove(del_endpoint)
                yaml_writer(data, VARS_DIR, 'endpoints.yaml')
    endpoints = get_vars_values(VARS_DIR, 'endpoints.yaml')
    return {'endpoints': endpoints}


@route('/user_view/<name>', method=['GET', 'POST'])
@jinja2_view('static/html/adc/user_view')
def adc_user_view(name):
    """
    Page user view
    """
    from_url = str(request.url).split('/')[4]
    users = get_vars_values(FILES_DIR, 'user_list.yaml')
    user = ""
    for item in users.get('users'):
        if item.get("user") == from_url:
            user = item

    return {"user": user}


@route('/user_edit/<name>', method=['GET', 'POST'])
@jinja2_view('static/html/adc/user_edit')
def adc_user_edit(name):
    """
    Page user edit
    """
    users = get_vars_values(FILES_DIR, 'user_list.yaml')
    env_value = request.get_cookie('env_value', secret=secret)
    if env_value:
        file_name = env_value[0]
    else:
        file_name = 'l2m-users.dev'
    if request.method == 'POST':
        if request.forms.get('cancel_edit'):
            redirect('/adc_control')
        if request.forms.get('edit_user'):
            username = request.forms.get('user_name')
            status = [user.get('enabled') for user in users.get(
                'users') if user.get('user') == username]
            user_pass = to_hash_256(request.forms.get('user_pass'))
            source_address = request.POST.getall('source_address')
            city_permit = request.POST.getall('city_permit')
            endpoint_permit = request.POST.getall('endpoint_permit')
            method_ro_permit = request.POST.getall('method_ro_permit')
            method_rw_permit = request.POST.getall('method_rw_permit')
            city_deny = request.POST.getall('city_deny')
            endpoint_deny = request.POST.getall('endpoint_deny')
            method_ro_deny = request.POST.getall('method_ro_deny')
            method_rw_deny = request.POST.getall('method_rw_deny')
            user_result = {"user": username, "pass": user_pass, "enabled": status[0], "cities": {"permit": city_permit, "deny": city_deny}, "src_addr": source_address,
                           "endpoints": {"permit": endpoint_permit, "deny": endpoint_deny,
                                         "v2": {"ro_methods": {"permit": method_ro_permit, "deny": method_ro_deny},
                                                "rw_methods": {"permit": method_rw_permit, "deny": method_rw_deny}
                                                }
                                         }
                           }
            with open(os.path.join(FILES_DIR, file_name), mode='r+') as file:
                data = json.load(file)
                file.truncate(0)
                file.seek(0)
                for i, value in enumerate(data.get('users')):
                    if value.get('user') == username:
                        del data.get('users')[i]
                logger.log(20, f'User  edit {name} with configs {data}')
                data["users"].append(user_result)
                json.dump(data, file, indent=4)
                file.close()
            redirect('/adc_control')

    cities = get_vars_values(VARS_DIR, 'cities.yaml')
    endpoints = get_vars_values(VARS_DIR, 'endpoints.yaml')
    methods = get_vars_values(VARS_DIR, 'methods.yaml')
    from_url = str(request.url).split('/')[4]
    users = get_vars_values(FILES_DIR, 'user_list.yaml')
    user = ""
    for item in users.get('users'):
        if item.get("user") == from_url:
            user = item

    return {"user": user, "cities": cities, "endpoints": endpoints, "methods": methods}


@route('/user_add', method=['GET', 'POST'])
@jinja2_view('static/html/adc/user_add')
def adc_user_add():
    """
    Page user add
    """
    cities = get_vars_values(VARS_DIR, 'cities.yaml')
    endpoints = get_vars_values(VARS_DIR, 'endpoints.yaml')
    methods = get_vars_values(VARS_DIR, 'methods.yaml')
    env_value = request.get_cookie('env_value', secret=secret)
    if env_value:
        file_name = env_value[0]
    else:
        file_name = 'l2m-users.dev'
    if request.method == 'POST':
        if request.forms.get('add_user'):
            username = request.forms.get('user_name')
            description = request.forms.get('user_description')
            user_pass = to_hash_256(request.forms.get('user_pass'))
            source_address = request.POST.getall('source_address')
            city_permit = request.POST.getall('city_permit')
            endpoint_permit = request.POST.getall('endpoint_permit')
            method_ro_permit = request.POST.getall('method_ro_permit')
            method_rw_permit = request.POST.getall('method_rw_permit')
            city_deny = request.POST.getall('city_deny')
            endpoint_deny = request.POST.getall('endpoint_deny')
            method_ro_deny = request.POST.getall('method_ro_deny')
            method_rw_deny = request.POST.getall('method_rw_deny')
            user_result = {"user": username, "pass": user_pass, "description": description, "cities": {"permit": city_permit, "deny": city_deny}, "src_addr": source_address,
                           "endpoints": {"permit": endpoint_permit, "deny": endpoint_deny,
                                         "v2": {"ro_methods": {"permit": method_ro_permit, "deny": method_ro_deny},
                                                "rw_methods": {"permit": method_rw_permit, "deny": method_rw_deny}
                                                }
                                         }
                           }
            logger.log(
                20, f'Add new user {username} with config {user_result}')
            with open(os.path.join(FILES_DIR, file_name), mode='r+') as file:
                data = json.load(file)
                file.truncate(0)
                file.seek(0)
                data["users"].append(user_result)
                json.dump(data, file, indent=4)
                file.close()
            redirect('/adc_control')

    return {"cities": cities, "endpoints": endpoints, "methods": methods}


@route('/converting', method=['GET', 'POST'])
@jinja2_view('static/html/adc/converting')
def adc_converting():
    """
    Converting users.json
    """
    users_files = file_params(UPLOADS_DIR)
    if request.method == 'POST':
        if request.files.get('users_upload'):
            upload = request.files.get('users_upload')
            upload_file(upload, UPLOADS_DIR)
        elif request.forms.get('convert_from_file'):
            file_name = request.forms.get('convert_from_file')
            env_name = request.forms.get('upload_env_name')
            append_users = []
            with open(os.path.join(FILES_DIR, env_name), "r") as file2:
                current_users_file = json.load(file2)
            current_users_name = [item.get('user')
                                  for item in current_users_file.get('users')]
            with open(os.path.join(UPLOADS_DIR, file_name), "r") as file:
                load_json = json.load(file)
                for item in load_json.get("users"):
                    username = item.get("user")
                    user_pass = item.get("pass")
                    description = "Load from converted"
                    source_address = item.get('src_addr')
                    city_permit = item.get('endpoints').get('city')
                    city_deny = []
                    endpoint_permit = item.get('endpoints').get('endpoint')
                    endpoint_deny = []
                    if item.get("access_types").get('type') == "rw":
                        if item.get("access_types").get('value'):
                            method_rw_permit = item.get(
                                "access_types").get('value')
                            method_ro_permit = item.get(
                                "access_types").get('value')
                            method_ro_deny = []
                            method_rw_deny = []
                        else:
                            method_rw_permit = ['all']
                            method_ro_permit = ['all']
                            method_ro_deny = []
                            method_rw_deny = []
                    elif item.get("access_types").get('type') == "ro":
                        if item.get("access_types").get('value'):
                            method_rw_permit = []
                            method_ro_deny = []
                            method_rw_deny = []
                            method_ro_permit = item.get(
                                "access_types").get('value')
                        else:
                            method_rw_permit = []
                            method_ro_permit = ['all']
                            method_ro_deny = []
                            method_rw_deny = []

                    user_result = {"user": username, "pass": user_pass, "description": description, "enabled": "true", "cities": {"permit": city_permit, "deny": city_deny}, "src_addr": source_address,
                                   "endpoints": {"permit": endpoint_permit, "deny": endpoint_deny,
                                                 "v2": {"ro_methods": {"permit": method_ro_permit, "deny": method_ro_deny},
                                                        "rw_methods": {"permit": method_rw_permit, "deny": method_rw_deny}
                                                        }
                                                 }
                                   }
                    if not (username in current_users_name):
                        append_users.append(user_result)
            with open(os.path.join(FILES_DIR, env_name), mode='r+') as file:
                data = json.load(file)
                file.truncate(0)
                file.seek(0)
                data["users"] = data['users'] + append_users
                json.dump(data, file, indent=4)
                file.close()
            redirect('/adc_control')

        elif request.forms.get('delete_user_file'):
            filename = request.forms.get('delete_user_file')
            file = os.path.join(UPLOADS_DIR, filename)
            os.remove(file)
            redirect("/converting")
    return {'users_files': users_files, }


if __name__ == '__main__':
    run(host='0.0.0.0', port=8080, debug=True, reloader=True)
else:
    app = application = default_app()
