import secrets
import socket

from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from docker.types import Resources

from teacher.models import Images, Container, Course, Score, Experiment
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


def create_service(input_client, token, image_name, network_name, service_name, task_num, num_cpu, mem_size, http_port, ssh_port):
    networks = [network_name]
    environment = {
        "JUPYTER_TOKEN": token,
        'JUPYTER_NOTEBOOK_CONFIG': 'c.NotebookApp.tornado_settings={"headers":{"Content-Security-Policy":"frame-ancestors *"}}',
    }
    resources = Resources(mem_limit=mem_size, cpu_limit=num_cpu)
    service = input_client.services.create(
        image_name,
        name=service_name,
        networks=networks,
        mode=docker.types.services.ServiceMode('replicated', replicas=task_num),
        endpoint_spec=docker.types.EndpointSpec(ports={8888: http_port}),
        env=environment,
        resources=resources,
    )
    print(service.name)
    print(service.short_id)
    return service


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


def commit_container_by_id(input_client, container_id, image_name):
    container = input_client.containers.get(container_id)
    image = container.commit(repository=image_name)
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


@csrf_exempt
def upload_file(request):
    files = request.FILES.getlist('file[]')
    user_id = request.POST.get('user_id')
    container_id = request.POST.get('container_id')
    print("upload")
    print(user_id, container_id,files)
    for file in files:
        save_path = 'users_{}/container_{}/{}'.format(user_id, container_id, file.name)
        print(save_path)
        default_storage.save(save_path, ContentFile(file.read()))
    return JsonResponse({'errno': 100000, 'msg': '文件保存成功'})


@csrf_exempt
def load_files(request):
    user_id = request.POST.get('user_id')
    container_id = request.POST.get('container_id')
    print("load")
    print(user_id, container_id)
    dir_path = "users_" + str(user_id) + "/container_" + str(container_id)
    os.makedirs(dir_path, exist_ok=True)
    files = get_filenames_in_folder(dir_path)
    return JsonResponse({'errno': 100000, 'msg': '文件查找成功', 'data': files})


@csrf_exempt
def delete_file(request):
    user_id = request.POST.get('user_id')
    container_id = request.POST.get('container_id')
    file_name = request.POST.get('file_name')
    dir_path = "users_" + str(user_id) + "/container_" + str(container_id)
    file_path = dir_path + "/" + file_name
    try:
        os.remove(file_path)
        return JsonResponse({'errno': 100000, 'msg': '文件删除成功'})
    except OSError as e:
        return JsonResponse({'errno': 100001, 'msg': e.strerror})


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
    print(config)
    match = re.search(r'(\d+)核CPU (\d+)G内存', config)
    num_cpu, mem_size = match.groups()
    num_cpu_m = int(float(num_cpu) * 10 ** 9)
    mem_size_m = int(mem_size) * 1024 * 1024 * 1024
    author = UserInfo.objects.get(user_id=author_id)
    network_name = 'test'
    token = secrets.token_hex(16)
    ports = set()
    while len(ports) < 2:
        port = get_free_port()
        ports.add(port)

    ssh_port, http_port = ports
    # author = info['author']
    # author = UserInfo.objects.filter(realname=author).first()
    # if author is not None:
    #     author_id = author.id
    # else:
    #     return JsonResponse({'errno': 100002, 'msg': '作者不存在'})
    client = docker.from_env()
    print(container_name)
    container = create_service(
        client,
        token,
        image_name,
        network_name,
        container_name,
        1,
        num_cpu_m,
        mem_size_m,
        http_port,
        ssh_port
    )
    url = get_service_url_by_id(client, container_name, token, http_port)
    new_container = Container()
    new_container.container_id = container.short_id
    new_container.author_id = author
    new_container.container_name = container.name
    new_container.container_url = url
    new_container.cpu_num = num_cpu
    new_container.mem_size = mem_size
    new_container.ssh_port = ssh_port
    new_container.http_port = http_port
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


@csrf_exempt
def add_new_image(request):
    container_name = request.POST.get('container_name')
    new_image_name = request.POST.get('new_image_name')
    client = docker.from_env()
    commit_container_in_service(client, container_name, new_image_name)
    return JsonResponse({'errno': 100000, 'msg': '新镜像创建成功'})



@csrf_exempt
def delete_container(request):
    container_name = request.POST.get('container_name')
    client = docker.from_env()
    container = Container.objects.filter(container_name=container_name).first()
    remove_service_by_id(client, container_name)
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
    client = docker.from_env()
    try:
        client.images.remove(image_name)
        return JsonResponse({'errno': 100000, 'msg': '镜像删除成功'})
    except APIError as e:
        if 'image is being used by stopped container' in str(e):
            return JsonResponse({'errno': 100000, 'msg': '镜像删除失败，有容器正在使用该镜像'})
        else:
            return JsonResponse({'errno': 100000, 'msg': '镜像删除失败，发生未知错误'})



@csrf_exempt
def stop_container(request):
    container_name = request.POST.get('container_name')
    client = docker.from_env()
    stop_container_by_id(client, container_name)
    container_in_DB = Container.objects.filter(container_name=container_name).first()
    container = client.containers.get(container_name)
    container_in_DB.container_status = container.status
    container_in_DB.save()
    return JsonResponse({'errno': 100000, 'msg': '容器停止运行成功'})
    # container = Container.objects.filter(container_name=container_name).first()
    # if container:
    #     client = docker.from_env()
    #     stop_container_by_id(client, container.container_id)
    #     return JsonResponse({'errno': 100000, 'msg': '容器停止运行成功'})
    # else:
    #     return JsonResponse({'errno': 100002, 'msg': '容器不存在'})


@csrf_exempt
def search_container(request):
    container_id = request.POST.get('container_id')
    container = Container.objects.filter(container_id=container_id).first()
    container_info = {
        'container_id': container.container_id,
        'container_name': container.container_name,
        'container_url': container.container_url,
        'author': container.author_id.realname,
        'cpu_num': container.cpu_num,
        'mem_size': container.mem_size,
        'http_port': container.http_port,
        'ssh_port': container.ssh_port,
    }
    return JsonResponse({'errno': 100000, 'msg': '容器查询成功', 'data': container_info})


@csrf_exempt
def start_container(request):
    container_name = request.POST.get('container_name')
    print(container_name)
    client = docker.from_env()
    start_container_by_id(client, container_name)
    container = client.containers.get(container_name)
    url = get_url(container)
    container_in_DB = Container.objects.filter(container_name=container_name).first()
    container = client.containers.get(container_name)
    container_in_DB.container_status = container.status
    container_in_DB.container_url = url
    container_in_DB.save()
    return JsonResponse({'errno': 100000, 'msg': '容器开始运行成功'})
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
    new_course = Course(
        course_name=course_name,
        course_intro=course_intro,
        course_aim=course_aim,
        use_image_name=use_image_name,
        course_limit_time=course_limit_time,
        course_difficulty=course_difficulty,
        course_chapter=course_chapter,
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
        "course_chapter": course.course_chapter,
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
            "course_chapter": course.course_chapter,
        }
        return JsonResponse({'errno': 100000, 'msg': '课程查询成功', 'data': course_json})
    else:
        return JsonResponse({'errno': 100001, 'msg': '未找到课程'})


@csrf_exempt
def create_experiment(request):
    course_id = request.POST.get('course_id')
    user_id = request.POST.get('user_id')
    user = UserInfo.objects.get(user_id=user_id)
    course = Course.objects.get(course_id=course_id)
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
            print(container_name)
            client = docker.from_env()
            # create_service(client, image, 'test', container_name, 2) 这里需要修改！！！！
            # url = get_service_url_by_id(client, container_name) 这里也是！！！
            print(url)
            new_experiment.experiment_url = url
            new_experiment.save()
            data = {
                'experiment_id': new_experiment.experiment_id,
                'experiment_course': new_experiment.course.course_id,
                'experiment_url': new_experiment.experiment_url,
                'experiment_countdown': new_experiment.experiment_countdown,
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