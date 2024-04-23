import io
import random
import secrets
import shutil
import socket
import string
import tarfile
from io import BytesIO
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from docker.types import Resources
from teacher.models import Images, Container, Course, Score, Experiment, Chapter
from users.models import UserInfo
from time import sleep
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from docker.errors import APIError
import os
import json
import docker
import re

def list_container(input_client):
    container_list = input_client.containers.list(all=True)
    return container_list


def list_image(input_client):
    image_list = input_client.images.list()
    return image_list


def run_container(input_client, image_name):
    container = input_client.containers.run(image_name, detach=True, ports={'8888/tcp': None})
    return container


# def create_service(input_client, image_name, network_name, service_name, task_num, ssh_port, http_port, token, num_cpu, mem_size, from_volume_path, to_volume_path):
#     networks = [network_name]
#     password = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(10))
#     volumes = {
#         from_volume_path: {'bind': to_volume_path, 'mode': 'rw'},
#     }
#     resources = Resources(mem_limit=mem_size, cpu_limit=num_cpu)
#     service = input_client.services.create(
#         image_name,
#         name=service_name,
#         networks=networks,
#         mode=docker.types.services.ServiceMode('replicated', replicas=task_num),
#         endpoint_spec=docker.types.EndpointSpec(ports={8888: http_port}),
#         resources=resources,
#     )
#     print(service.name)
#     print(service.short_id)
#     return service



def create_service(input_client: docker.DockerClient,
                   image_name: str,
                   service_name: str,
                   ssh_port: int,
                   http_port: int,
                   token: str,
                   num_cpu: str,
                   mem_size: str,
                   from_volume_path: str,
                   to_volume_path: str,
                   network_name: str,
                   task_num: int):
    password = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(10))
    cpu_limit = int(float(num_cpu) * 100000000)
    mem_limit = int(mem_size) * 1024 * 1024 * 1024
    mounts = [
        docker.types.Mount(target=to_volume_path, source=from_volume_path, type="bind"),
    ]
    network = input_client.networks.create(network_name, driver="overlay")
    resources = docker.types.Resources(cpu_limit=cpu_limit, mem_limit=mem_limit)

    port_config = docker.types.EndpointSpec(ports={8888: http_port, 22: ssh_port})

    envs = ["JUPYTER_TOKEN=" + token, "ROOT_PASSWORD=" + password]

    service = input_client.services.create(
        image=image_name,
        name=service_name,
        command=['/usr/bin/supervisord'],
        mounts=mounts,
        resources=resources,
        networks=[network_name],
        env=envs,
        endpoint_spec=port_config,
        mode=docker.types.ServiceMode("replicated", replicas=task_num)
    )

    return service, password


def update_service_by_id(input_client: docker.DockerClient, service_id):
    # Generate a Docker API client.
    api_client = input_client.api
    print(service_id)
    # Get the service's current configuration.
    current_service = api_client.inspect_service(service_id)

    # Set the endpoint mode to dnsrr in the service configuration.
    current_service["Spec"]["EndpointSpec"]["Mode"] = "dnsrr"

    # Update the service with the new configuration.
    api_client.update_service(service_id, current_service["Spec"])


def create_container(input_client, image_name, container_name, ssh_port, http_port, token, num_cpu, mem_size, from_volume_path, to_volume_path):
    password = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(10))
    volumes = {
        from_volume_path: {'bind': to_volume_path, 'mode': 'rw'},
    }
    container = input_client.containers.run(
        image=image_name,
        ports={f'8888/tcp': http_port, f'22/tcp': ssh_port},
        detach=True,
        name=container_name,
        command=['/usr/bin/supervisord'],
        cpu_period=100000,
        cpu_quota=int(float(num_cpu) * 100000),
        mem_limit=mem_size,
        volumes=volumes,
        environment={"JUPYTER_TOKEN": token, "ROOT_PASSWORD": password},
    )
    return container, password


def get_url(container):
    sleep(15)
    client = docker.from_env()
    container = client.containers.get(container.id)
    port = container.attrs['NetworkSettings']['Ports']['8888/tcp'][0]['HostPort']
    logs = container.logs()
    logs_decoded = logs.decode("utf-8")
    lines = logs_decoded.split('\n')
    url_line = [line for line in lines if 'http' in line]
    if url_line:
        url = url_line[-1]
        return 'http://127.0.0.1:' + port + '/lab?token=' + url.split('token=')[1]
    else:
        return 'log error, not found URL'


def get_service_url_by_id(input_client, service_name, token, http_port):
    service = input_client.services.get(service_name)
    nodes = input_client.nodes.list()
    node_details = nodes[0].attrs
    ip = node_details['Status']['Addr']
    return 'http://' + ip + ':' + str(http_port) + '/lab?token=' + token
# def get_url_by_id(input_client, container_id):
#     # 获取并解析容器日志
#     container = input_client.containers.get(container_id)
#     logs = container.logs()
#     logs_decoded = logs.decode("utf-8")
#     lines = logs_decoded.split('\n')
#     url_line = [line for line in lines if 'http' in line]
#
#     if url_line:
#         url = url_line[1]
#         return 'http' + url.split('http')[1]
#     else:
#         return 'log error, not found URL'


def get_container_url_by_id(input_client, token, http_port):
    return 'http://127.0.0.1:' + str(http_port) + '/lab?token=' + token


def stop_container(container):
    container.stop()


def stop_container_by_id(input_client, container_id):
    container = input_client.containers.get(container_id)
    container.stop()


def start_container_by_id(input_client, container_id):
    container = input_client.containers.get(container_id)
    container.start()


def remove_container(container):
    container.stop()
    container.remove()


def remove_image(input_client, image_id):
    input_client.images.remove(image_id)


def remove_container_by_id(input_client, container_id):
    container = input_client.containers.get(container_id)
    container.stop()
    container.remove()


def commit_container(container, image_name):
    image = container.commit(repository=image_name)
    return image


def find_free_port():
    while True:
        port = random.randint(10000, 65536)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', port))
            if result != 0:  # 如果端口可用，connect_ex返回错误代码
                return port


def copy_dir(from_path, to_path):
    if os.path.exists(to_path):
        print(1)
        shutil.rmtree(to_path)
    print('1:', from_path, to_path)
    shutil.copytree(from_path, to_path)


def commit_container_by_id(input_client, container_name, image_name, from_path, to_path):
    # put_archive_to_container(from_path, to_path, container_id)
    container = input_client.containers.get(container_name)
    image = container.commit(repository=image_name)
    dir_name = 'image_' + image_name
    image_dir = './images/' + dir_name
    os.makedirs(image_dir, exist_ok=True)
    origin_dir = './images/container_' + container_name
    print(from_path, image_dir)
    copy_dir(from_path, image_dir)
    # os.rename(origin_dir, image_dir)
    return image


def commit_container_in_service(input_client, service_id, image_name):
    service = input_client.services.get(service_id)
    tasks = service.tasks()
    container_id = tasks[0]['Status']['ContainerStatus']['ContainerID']
    commit_container_by_id(input_client, container_id, image_name)


def remove_service_by_id(input_client, service_name):
    service = input_client.services.get(service_name)
    service.remove()


def get_filenames_in_folder(folder_path):
    filenames = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    return filenames


def get_runtime_workdir(image_name):
    client = docker.from_env()
    command = 'pwd'
    response = client.containers.run(image_name, command, remove=True)
    return response.decode('utf-8').strip()


def create_tar_stream(from_path):
    # Create a tarfile object in memory
    fileobj = BytesIO()
    tar = tarfile.TarFile(fileobj=fileobj, mode='w')

    for root, dirs, files in os.walk(from_path):
        # Ignore directories starting with .
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, from_path)
            new_path = os.path.join('work', relative_path)
            tar.add(full_path, arcname=new_path)
    tar.close()

    # Set the file pointer to the start of the file
    fileobj.seek(0)
    return fileobj


def put_archive_to_container(from_path, to_path, container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)  # Your container name

    stream = create_tar_stream(from_path)
    container.put_archive(to_path, stream)


# @csrf_exempt
# def upload_file(request):
#     files = request.FILES.getlist('file[]')
#     user_id = request.POST.get('user_id')
#     container_name = request.POST.get('container_name')
#     path = request.POST.get('path')
#     print("upload")
#     print(user_id, container_name, files, path)
#     for file in files:
#         if path is None:
#             save_path = 'users_{}/container_{}/{}'.format(user_id, container_name, file.name)
#         else:
#             save_path = 'users_{}/container_{}/{}/{}'.format(user_id, container_name, path, file.name)
#         print(save_path)
#         default_storage.save(save_path, ContentFile(file.read()))
#     return JsonResponse({'errno': 100000, 'msg': '文件保存成功'})


# @csrf_exempt
# def upload_file(request):
#     files = request.FILES.getlist('file[]')
#     paths = request.POST.getlist('path[]')  # 文件的相对路径列表
#     user_id = request.POST.get('user_id')
#     container_name = request.POST.get('container_name')
#     path = request.POST.get('path')
#     print("upload")
#     print(user_id, container_name, files, path)
#     for file, relative_path in zip(files, paths):
#         if path is None:
#             save_path = 'users_{}/container_{}/{}'.format(user_id, container_name, relative_path)
#         else:
#             save_path = 'users_{}/container_{}/{}/{}'.format(user_id, container_name, path, relative_path)
#         print(save_path)
#         default_storage.save(save_path, ContentFile(file.read()))
#     return JsonResponse({'errno': 100000, 'msg': '文件保存成功'})


# @csrf_exempt
# def upload_file(request):
#     tar_file = request.FILES.get('tarFile')  # get tar file
#     user_id = request.POST.get('user_id')
#     container_name = request.POST.get('container_name')
#     path = request.POST.get('path')
#     print(user_id, container_name, path)
#     # Convert the uploaded file to BytesIO
#     tar_file_IO_content = io.BytesIO(tar_file.read())
#
#     # Below line handle corrupted tar file and throws Exception
#     tar = tarfile.open(fileobj=tar_file_IO_content)
#
#     # Process tar members
#     for member in tar:
#         if member.isfile():
#             file_content = tar.extractfile(member).read()
#             save_directory = f'users_{user_id}/container_{container_name}/{path}/{os.path.dirname(member.name)}'
#             if not os.path.exists(save_directory):
#                 os.makedirs(save_directory)
#             save_path = f'{save_directory}/{os.path.basename(member.name)}'
#             default_storage.save(save_path, ContentFile(file_content))
#
#     return JsonResponse({'errno': 100000, 'msg': '文件保存成功'})


@csrf_exempt
def upload_file(request):
    tar_file = request.FILES.get('tarFile')  # get tar file
    user_id = request.POST.get('user_id')
    container_name = request.POST.get('container_name')
    path = request.POST.get('path')

    if tar_file is not None:  # tar file exists, process as before
        # Convert the uploaded file to BytesIO
        tar_file_IO_content = io.BytesIO(tar_file.read())

        # Below line handle corrupted tar file and throws Exception
        tar = tarfile.open(fileobj=tar_file_IO_content)

        # Process tar members
        for member in tar:
            if member.isfile():
                file_content = tar.extractfile(member).read()
                save_directory = f'users_{user_id}/container_{container_name}/{path}/{os.path.dirname(member.name)}'
                if not os.path.exists(save_directory):
                    os.makedirs(save_directory)
                save_path = f'{save_directory}/{os.path.basename(member.name)}'
                default_storage.save(save_path, ContentFile(file_content))
    else:  # No tar file, process single file or multiple files
        files = request.FILES.getlist('files[]')  # get files
        for file in files:
            # Convert the uploaded file to BytesIO
            file_IO_content = io.BytesIO(file.read())

            save_directory = f'users_{user_id}/container_{container_name}/{path}'
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)
            save_path = f'{save_directory}/{file.name}'
            default_storage.save(save_path, ContentFile(file_IO_content.getvalue()))

    return JsonResponse({'errno': 100000, 'msg': '文件保存成功'})


@csrf_exempt
def upload_tar_file(request):
    tar_file = request.FILES['file']
    user_id = request.POST.get('user_id')
    container_name = request.POST.get('container_name')
    path = request.POST.get('path')
    tar_content = ContentFile(tar_file.read())

    with tarfile.open(fileobj=tar_content) as tar:
        for member in tar.getmembers():
            if member.is_file():
                file = tar.extractfile(member)
                save_path = 'users_{}/container_{}/{}/{}'.format(user_id, container_name, path, member.name)
                default_storage.save(save_path, ContentFile(file.read()))

    return JsonResponse({'errno': 100000, 'msg': '文件保存成功'})


def list_files(startpath):
    file_list = []
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            relative_path = os.path.join(root, f)
            file_dict = {'filename': f, 'path': relative_path.replace(startpath, '').replace('\\', '/').lstrip('/')}
            file_list.append(file_dict)
    return file_list


@csrf_exempt
def load_files(request):
    user_id = request.POST.get('user_id')
    container_name = request.POST.get('container_name')
    print("load")
    print(user_id, container_name)
    dir_path = "users_" + str(user_id) + "/container_" + str(container_name)
    os.makedirs(dir_path, exist_ok=True)
    files = list_files(dir_path)
    return JsonResponse({'errno': 100000, 'msg': '文件查找成功', 'data': files})


# @csrf_exempt
# def delete_file(request):
#     user_id = request.POST.get('user_id')
#     container_name = request.POST.get('container_name')
#     file_path = request.POST.get('file_path')
#     dir_path = "users_" + str(user_id) + "/container_" + str(container_name)
#     file_path = dir_path + "/" + file_path
#     print(file_path)
#     try:
#         os.remove(file_path)
#         return JsonResponse({'errno': 100000, 'msg': '文件删除成功'})
#     except OSError as e:
#         return JsonResponse({'errno': 100001, 'msg': e.strerror})


@csrf_exempt
def delete_file(request):
    user_id = request.POST.get('user_id')
    container_name = request.POST.get('container_name')
    file_paths = json.loads(request.POST['file_paths'])   # getlist 用来获取一个列表
    dir_path = "users_" + str(user_id) + "/container_" + str(container_name)
    for file_path in file_paths:    # 循环删除每个文件
        file_path = dir_path + "/" + file_path
        try:
            os.remove(file_path)
        except OSError as e:
            return JsonResponse({'errno': 100001, 'msg': e.strerror})
    return JsonResponse({'errno': 100000, 'msg': '文件删除成功'})


@csrf_exempt
def show_container(request):
    container_list = Container.objects.all()
    container_list = [{
        'id': container.container_id,
        'author_name': container.author_id.realname,
        'name': container.container_name,
        'url': container.container_url,
    } for container in container_list]
    return HttpResponse(json.dumps({'errno': 100000, 'msg': '容器查询成功', 'data': container_list}, ensure_ascii=False), content_type="application/json;charset=UTF-8")


@csrf_exempt
def show_images(request):
    client = docker.from_env()
    image_list = list_image(client)
    image_names = []
    for image in image_list:
        for tag in image.tags:
            image_names.append(tag)
    return HttpResponse(json.dumps({'errno': 100000, 'msg': '镜像查询成功', 'data': image_names}, ensure_ascii=False), content_type="application/json;charset=UTF-8")


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


@csrf_exempt
def add_new_container(request):
    image_name = request.POST.get('image_name')
    container_name = request.POST.get('container_name')
    author_id = request.POST.get('author_id')
    config = request.POST.get('config')
    match = re.search(r'(\d+)核CPU (\d+)G内存', config)
    num_cpu, mem_size = match.groups()
    mem_size_g = mem_size + 'g'
    workdir = get_runtime_workdir(image_name)
    # volume_dir = workdir + '/work'
    current_dir = os.getcwd()
    user_file_dir = 'users_' + author_id
    local_file_dir = 'users_' + author_id + '/container_' + container_name
    user_dir = os.path.join(current_dir, user_file_dir)
    local_dir = os.path.join(current_dir, local_file_dir)
    image_dir = 'images/image_' + image_name.split(':')[0]
    image_dir = os.path.join(current_dir, image_dir)
    copy_dir(image_dir, local_dir)
    print(image_dir, local_dir)
    copied_dir = os.path.join(user_dir, 'image_' + image_name.split(':')[0])
    # os.rename(copied_dir, local_dir)
    # os.makedirs(local_dir, exist_ok=True)
    author = UserInfo.objects.get(user_id=author_id)
    token = secrets.token_hex(16)
    ports = set()
    while len(ports) < 2:
        port = get_free_port()
        ports.add(port)

    ssh_port, http_port = ports
    client = docker.from_env()
    print(container_name)
    container, password = create_container(
        input_client=client,
        image_name=image_name,
        container_name=container_name,
        ssh_port=ssh_port,
        http_port=http_port,
        num_cpu=num_cpu,
        mem_size=mem_size_g,
        token=token,
        from_volume_path=local_dir,
        to_volume_path=workdir
    )
    url = get_container_url_by_id(client, token, http_port)
    new_container = Container()
    new_container.container_id = container.short_id
    new_container.author_id = author
    new_container.container_name = container.name
    new_container.container_url = url
    new_container.cpu_num = num_cpu
    new_container.mem_size = mem_size
    new_container.ssh_port = ssh_port
    new_container.http_port = http_port
    new_container.ssh_password = password
    new_container.base_image = image_name
    new_container.save()
    print(url)
    return JsonResponse({'errno': 100000, 'msg': '容器创建成功'})
    # if container:
    #     url = get_url(container)
    #     new_container = Container()
    #     new_container.container_id = container.id
    #     new_container.container_name = container.name
    #     new_container.container_url = url
    #     new_container.author_id = author_id
    #     new_container.save()
    #     return JsonResponse({'errno': 100000, 'msg': '容器创建成功'})
    # else:
    #     return JsonResponse({'errno': 100003, 'msg': '容器创建失败'})



def delete_file_in_container(container_name, file_path):
    client = docker.from_env()

    # Get the container
    container = client.containers.get(container_name)

    # Execute rm command
    exit_code, output = container.exec_run(f'rm -rf {file_path}')

    if exit_code == 0:
        print(f'Successfully deleted {file_path} in {container_name}')
    else:
        print(f'Failed to delete {file_path} in {container_name}. Output: {output}')


@csrf_exempt
def add_new_image(request):  # 修改
    container_name = request.POST.get('container_name')
    new_image_name = request.POST.get('new_image_name')
    client = docker.from_env()
    container = Container.objects.filter(container_name=container_name).first()
    local_container = client.containers.get(container_name)
    workdir = local_container.attrs['Config']['WorkingDir']
    author_id = container.author_id.user_id
    current_dir = os.getcwd()
    local_file_dir = 'users_' + str(author_id) + '/container_' + container_name
    from_path = os.path.join(current_dir, local_file_dir)
    to_path = workdir
    image = commit_container_by_id(client, container_name, new_image_name, from_path, to_path)
    new_image = Images(
        image_id=image.id,
        image_name=image.tags[0],
        author_id=container.author_id,
        cpu_num=container.cpu_num,
        mem_size=container.mem_size,
    )
    new_image.save()
    return JsonResponse({'errno': 100000, 'msg': '新镜像创建成功'})


@csrf_exempt
def delete_container(request):
    container_name = request.POST.get('container_name')
    author_id = request.POST.get('author_id')
    client = docker.from_env()
    container = Container.objects.filter(container_name=container_name).first()
    remove_container_by_id(client, container_name)
    container_path = './users_' + author_id + '/container_' + container_name
    shutil.rmtree(container_path)
    container.delete()
    return JsonResponse({'errno': 100000, 'msg': '容器删除成功'})
    # container = Container.objects.filter(container_name=container_name).first()
    # if container:
    #     client = docker.from_env()
    #     remove_container_by_id(client, container.container_id)
    #     container.delete()
    #     return JsonResponse({'errno': 100000, 'msg': '容器删除成功'})
    # else:
    #     return JsonResponse({'errno': 100002, 'msg': '容器不存在'})


@csrf_exempt
def delete_image(request):
    image_name = request.POST.get('image_name')
    image = Images.objects.get(image_name=image_name)
    image_path = "./images/image_" + image_name
    client = docker.from_env()
    try:
        image.delete()
        client.images.remove(image_name)
        shutil.rmtree(image_path)
        return JsonResponse({'errno': 100000, 'msg': '镜像删除成功'})
    except APIError as e:
        if 'image is being used by stopped container' in str(e):
            return JsonResponse({'errno': 100000, 'msg': '镜像删除失败，有容器正在使用该镜像'})
        else:
            return JsonResponse({'errno': 100000, 'msg': '镜像删除失败，发生未知错误'})


# @csrf_exempt
# def stop_container(request):
#     container_name = request.POST.get('container_name')
#     client = docker.from_env()
#     stop_container_by_id(client, container_name)
#     container_in_DB = Container.objects.filter(container_name=container_name).first()
#     container = client.containers.get(container_name)
#     container_in_DB.container_status = container.status
#     container_in_DB.save()
#     return JsonResponse({'errno': 100000, 'msg': '容器停止运行成功'})
#     # container = Container.objects.filter(container_name=container_name).first()
#     # if container:
#     #     client = docker.from_env()
#     #     stop_container_by_id(client, container.container_id)
#     #     return JsonResponse({'errno': 100000, 'msg': '容器停止运行成功'})
#     # else:
#     #     return JsonResponse({'errno': 100002, 'msg': '容器不存在'})


@csrf_exempt
def search_container(request):
    container_id = request.POST.get('container_id')
    container = Container.objects.filter(container_id=container_id).first()
    client = docker.from_env()
    local_container = client.containers.get(container_id)
    workdir = local_container.attrs['Config']['WorkingDir']
    container_info = {
        'container_id': container.container_id,
        'container_name': container.container_name,
        'container_url': container.container_url,
        'author': container.author_id.realname,
        'cpu_num': container.cpu_num,
        'mem_size': container.mem_size,
        'http_port': container.http_port,
        'ssh_port': container.ssh_port,
        'workdir': workdir,
        'ssh_password': container.ssh_password,
    }
    return JsonResponse({'errno': 100000, 'msg': '容器查询成功', 'data': container_info})


# @csrf_exempt
# def start_container(request):
#     container_name = request.POST.get('container_name')
#     print(container_name)
#     client = docker.from_env()
#     start_container_by_id(client, container_name)
#     container = client.containers.get(container_name)
#     url = get_url(container)
#     container_in_DB = Container.objects.filter(container_name=container_name).first()
#     container = client.containers.get(container_name)
#     container_in_DB.container_status = container.status
#     container_in_DB.container_url = url
#     container_in_DB.save()
#     return JsonResponse({'errno': 100000, 'msg': '容器开始运行成功'})
    # container = Container.objects.filter(container_name=container_name).first()
    # if container:
    #     client = docker.from_env()
    #     start_container_by_id(client, container.container_id)
    #     return JsonResponse({'errno': 100000, 'msg': '容器重新运行成功'})
    # else:
    #     return JsonResponse({'errno': 100002, 'msg': '容器不存在'})


@csrf_exempt
def create_course(request):
    course_name = request.POST.get('course_name')
    course_intro = request.POST.get('course_intro')
    author_id = request.POST.get('author_id')
    author = UserInfo.objects.get(user_id=author_id)
    course_aim = request.POST.get('course_aim')
    use_image_name = request.POST.get('use_image_name')
    course_limit_time = request.POST.get('course_limit_time')
    course_difficulty = request.POST.get('course_difficulty')
    course_chapter = request.POST.get('course_chapter')
    chapter = Chapter.objects.get(chapter_number=course_chapter)
    new_course = Course(
        course_name=course_name,
        course_intro=course_intro,
        course_aim=course_aim,
        use_image_name=use_image_name,
        course_limit_time=course_limit_time,
        course_difficulty=course_difficulty,
        course_chapter=chapter,
        author_id=author,
    )
    new_course.save()
    return JsonResponse({'errno': 100000, 'msg': '课程创建成功'})


@csrf_exempt
def list_course(request):
    courses = Course.objects.all()
    course_list = list(courses)
    course_list_json = [{
        "course_id": course.course_id,
        "author_name": course.author_id.realname,
        "course_name": course.course_name,
        "course_intro": course.course_intro,
        "course_aim": course.course_aim,
        "use_image_name": course.use_image_name,
        "course_limit_time": course.course_limit_time,
        "course_difficulty": course.course_difficulty,
        "course_chapter": course.course_chapter.chapter_number,
        "chapter_name": course.course_chapter.chapter_name,
    } for course in course_list]
    return JsonResponse({'errno': 100000, 'msg': '课程查询成功', 'data': course_list_json})


@csrf_exempt
def delete_course(request):
    course_id = request.POST.get('course_id')
    course = Course.objects.get(course_id=course_id)
    if course:
        course.delete()
        return JsonResponse({'errno': 100000, 'msg': '课程删除成功'})
    else:
        return JsonResponse({'errno': 100001, 'msg': '未找到课程'})


@csrf_exempt
def get_course_info(request):
    course_id = request.POST.get('course_id')
    course = Course.objects.get(course_id=course_id)
    image_name = course.use_image_name
    print(image_name)
    image = Images.objects.get(image_name=image_name)
    if course:
        course_json = {
            "course_id": course.course_id,
            "author_name": course.author_id.realname,
            "course_name": course.course_name,
            "course_intro": course.course_intro,
            "course_aim": course.course_aim,
            "use_image_name": course.use_image_name,
            "course_limit_time": course.course_limit_time,
            "course_difficulty": course.course_difficulty,
            "course_chapter": course.course_chapter.chapter_number,
            "chapter_name": course.course_chapter.chapter_name,
            "cpu_num": image.cpu_num,
            "mem_size": image.mem_size
        }
        return JsonResponse({'errno': 100000, 'msg': '课程查询成功', 'data': course_json})
    else:
        return JsonResponse({'errno': 100001, 'msg': '未找到课程'})


@csrf_exempt
def list_chapter(request):
    chapters = Chapter.objects.all().order_by('chapter_number')
    chapter_list = list(chapters)
    chapter_json = [{
        'chapter_num': chapter.chapter_number,
        'chapter_name': chapter.chapter_name,
    }for chapter in chapter_list]
    return JsonResponse({'errno': 100000, 'msg': '章节查询成功', 'data': chapter_json})


@csrf_exempt
def add_chapter(request):
    chapter_num = request.POST.get('chapter_num')
    chapter_name = request.POST.get('chapter_name')
    new_chapter = Chapter(
        chapter_number=chapter_num,
        chapter_name=chapter_name,
    )
    try:
        new_chapter.save()
        return JsonResponse({'errno': 100000, 'msg': '章节添加成功'})
    except IntegrityError:
        return JsonResponse({'errno': 100001, 'msg': '章节添加失败，章节号重复'}, status=400)


@csrf_exempt
def delete_chapter(request):
    chapter_num = request.POST.get('chapter_num')
    try:
        chapter = Chapter.objects.get(chapter_number=chapter_num)
        chapter.delete()
        return JsonResponse({'errno': 100000, 'msg': '章节删除成功'})
    except Chapter.DoesNotExist:
        return JsonResponse({'errno': 100001, 'msg': '章节不存在'}, status=404)
    except ProtectedError:
        return JsonResponse({'errno': 100002, 'msg': '章节删除失败，有关联课程'},
                            status=400)



@csrf_exempt
def create_experiment(request):
    course_id = request.POST.get('course_id')
    user_id = request.POST.get('user_id')
    user = UserInfo.objects.get(user_id=user_id)
    course = Course.objects.get(course_id=course_id)
    image = Images.objects.get(image_name=course.use_image_name)
    num_cpu = image.cpu_num
    mem_size = image.mem_size
    if course:
        if Experiment.objects.filter(user_id=user_id, course_id=course_id).exists():
            experiment = Experiment.objects.get(user_id=user_id, course_id=course_id)
            data = {
                'experiment_id': experiment.experiment_id,
                'experiment_course': experiment.course.course_id,
                'experiment_url': experiment.experiment_url,
                'experiment_countdown': experiment.experiment_countdown,
            }
            return JsonResponse({'errno': 100000, 'msg': '实验创建成功', 'data': data})
        else:
            image = course.use_image_name
            url = ''
            time = course.course_limit_time * 3600
            new_experiment = Experiment(
                course=course,
                user_id=user,
                experiment_countdown=time,
                experiment_url=url,
            )
            new_experiment.save()
            container_name = 'experiment_' + str(new_experiment.experiment_id)
            network_name = 'experiment_' + str(new_experiment.experiment_id)
            print('container_name', container_name)
            client = docker.from_env()
            print(num_cpu, 'config', mem_size)
            mem_size_g = mem_size + 'g'
            workdir = get_runtime_workdir(image)
            # volume_dir = workdir + '/work'
            current_dir = os.getcwd()
            user_file_dir = 'users_' + user_id
            local_file_dir = 'users_' + user_id + '/container_' + container_name
            user_dir = os.path.join(current_dir, user_file_dir)
            local_dir = os.path.join(current_dir, local_file_dir)
            image_dir = 'images/image_' + image.split(':')[0]
            image_dir = os.path.join(current_dir, image_dir)
            copy_dir(image_dir, local_dir)
            token = secrets.token_hex(16)
            ports = set()
            while len(ports) < 2:
                port = get_free_port()
                ports.add(port)

            ssh_port, http_port = ports
            client = docker.from_env()
            service, password = create_service(
                input_client=client,
                image_name=image,
                service_name=container_name,
                ssh_port=ssh_port,
                http_port=http_port,
                token=token,
                num_cpu=num_cpu,
                mem_size=mem_size,
                from_volume_path=local_dir,
                to_volume_path=workdir,
                network_name=network_name,
                task_num=1,
            )
            # update_service_by_id(client, service.id)  //need to update!!!
            # container, password = create_container(
            #     input_client=client,
            #     image_name=image,
            #     container_name=container_name,
            #     ssh_port=ssh_port,
            #     http_port=http_port,
            #     num_cpu=num_cpu,
            #     mem_size=mem_size_g,
            #     token=token,
            #     from_volume_path=local_dir,
            #     to_volume_path=workdir
            # )
            # url = get_service_url_by_id(client, container_name) 这里也是！！！
            url = get_container_url_by_id(client, token, http_port)
            print('url', url)
            new_experiment.experiment_url = url
            new_experiment.experiment_password = password
            new_experiment.save()
            data = {
                'experiment_id': new_experiment.experiment_id,
                'experiment_course': new_experiment.course.course_id,
                'experiment_url': new_experiment.experiment_url,
                'experiment_countdown': new_experiment.experiment_countdown,
                'experiment_password': new_experiment.experiment_password
            }
            return JsonResponse({'errno': 100000, 'msg': '实验创建成功', 'data': data})
    else:
        return JsonResponse({'errno': 100001, 'msg': '实验创建失败'})


@csrf_exempt
def delete_experiment(request):
    experiment_id = request.POST.get('experiment_id')
    client = docker.from_env()
    container_name = 'experiment_' + str(experiment_id)
    print(experiment_id)
    try:
        experiment = Experiment.objects.get(experiment_id=experiment_id)
    except ObjectDoesNotExist:
        return JsonResponse({'errno': 100001, 'msg': '实验不存在，删除失败'})

    remove_service_by_id(client, container_name)
    container_path = './users_' + str(experiment.user_id.user_id) + '/container_experiment_' + experiment_id
    shutil.rmtree(container_path)
    experiment.delete()

    return JsonResponse({'errno': 100000, 'msg': '实验删除成功'})


@csrf_exempt
def save_experiment(request):
    experiment_id = request.POST.get('experiment_id')
    countdown = request.POST.get('countdown')
    experiment = Experiment.objects.get(experiment_id=experiment_id)
    experiment.experiment_countdown = countdown
    experiment.save()
    return JsonResponse({'errno': 100000, 'msg': '实验保存成功'})
