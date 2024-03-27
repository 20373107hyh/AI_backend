from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from teacher.models import Images, Container, Course, Score, Experiment
from users.models import UserInfo
from time import sleep
from docker.errors import APIError

import json
import docker


def list_container(input_client):
    container_list = input_client.containers.list(all=True)
    return container_list


def list_image(input_client):
    image_list = input_client.images.list()
    return image_list


def run_container(input_client, image_name):
    container = input_client.containers.run(image_name, detach=True, ports={'8888/tcp': None})
    return container


def create_service(input_client, image_name, network_name, service_name, task_num):
    networks = [network_name]
    environment = {
        "JUPYTER_TOKEN": "123456789",
    }
    service = input_client.services.create(
        image_name,
        name=service_name,
        networks=networks,
        mode=docker.types.services.ServiceMode('replicated', replicas=task_num),
        endpoint_spec=docker.types.EndpointSpec(ports=[{'TargetPort': 8888}]),
        env=environment,
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


def get_service_url_by_id(input_client, service_name):
    service = input_client.services.get(service_name)
    port = 0
    for port_item in service.attrs['Endpoint']['Ports']:
        if port_item['TargetPort'] == 8888:
            port = port_item['PublishedPort']
            print(port)
            break
        else:
            return 'error, cannot find port'
    nodes = input_client.nodes.list()
    node_details = nodes[0].attrs
    ip = node_details['Status']['Addr']
    return 'http://' + ip + ':' + str(port) + '/lab?token=123456789'
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


@csrf_exempt
def show_container(request):
    container_list = Container.objects.all()
    container_list = list(container_list)
    container_list = [{
        'id': container.container_id,
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


@csrf_exempt
def add_new_container(request):
    image_name = request.POST.get('image_name')
    container_name = request.POST.get('container_name')
    network_name = 'test'
    # author = info['author']
    # author = UserInfo.objects.filter(realname=author).first()
    # if author is not None:
    #     author_id = author.id
    # else:
    #     return JsonResponse({'errno': 100002, 'msg': '作者不存在'})
    client = docker.from_env()
    print(container_name)
    container = create_service(client, image_name, network_name, container_name, 2)
    url = get_service_url_by_id(client, container_name)
    new_container = Container()
    new_container.container_id = container.short_id
    new_container.container_name = container.name
    new_container.container_url = url
    new_container.save()
    print(url)
    return JsonResponse({'errno': 100000, 'msg': '容器创建成功', 'data': url})
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
    )
    new_course.save()
    return JsonResponse({'errno': 100000, 'msg': '课程创建成功'})


@csrf_exempt
def list_course(request):
    courses = Course.objects.all()
    course_list = list(courses)
    course_list_json = [{
        "course_id": course.course_id,
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
    course = Course.objects.get(course_id=course_id)
    if course:
        image = course.use_image_name
        url = ''
        time = course.course_limit_time * 3600
        new_experiment = Experiment(
            course=course,
            experiment_countdown=time,
            experiment_url=url,
        )
        new_experiment.save()
        container_name = 'experiment_' + str(new_experiment.experiment_id)
        print(container_name)
        client = docker.from_env()
        create_service(client, image, 'test', container_name, 2)
        url = get_service_url_by_id(client, container_name)
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