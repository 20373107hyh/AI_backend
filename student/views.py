import json

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from student.models import Student_Courses
from teacher.models import Course, Experiment, Container
from users.models import UserInfo


@csrf_exempt
def get_user_info(request):
    user_id = request.POST.get('user_id')
    current_user = UserInfo.objects.get(user_id=user_id)
    data = {
        'user_id': current_user.user_id,
        'username': current_user.username,
        'password': current_user.password,
        'realname': current_user.realname,
        'email': current_user.email,
        'phone': current_user.phone,
        'status': current_user.status
    }
    return JsonResponse({'errno': 100000, 'msg': '请求用户信息成功', 'data': data})

@csrf_exempt
def get_course_list(request):

    courses_list = Course.objects.all().order_by('course_chapter__chapter_number')
    courses_info = []

    for student_course in courses_list:
        course_info = {
            'course_id': student_course.course_id,
            'course_name': student_course.course_name,
            'course_intro': student_course.course_intro,
            'course_aim': student_course.course_aim,
            'course_difficulty': student_course.course_difficulty,
            'course_chapter': student_course.course_chapter.chapter_number,
            'course_limit_time': student_course.course_limit_time,
        }
        courses_info.append(course_info)

    if courses_info:
        return JsonResponse({'errno': 100000, 'msg': '请求课程成功', 'data': courses_info})
    else:
        return JsonResponse({'errno': 100001, 'msg': '未能找到该学生的课程'})


@csrf_exempt
def list_course_by_chapter(request):
    courses = Course.objects.all().order_by('course_chapter__chapter_number')
    course_dict = {}
    for course in courses:
        course_detail = {
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
            "chapter_intro": course.course_chapter.chapter_intro,
        }
        if course.course_chapter.chapter_number in course_dict:
            course_dict[course.course_chapter.chapter_number].append(course_detail)
        else:
            course_dict[course.course_chapter.chapter_number] = [course_detail]
    course_list_json = list(course_dict.values())
    print(course_list_json)
    return JsonResponse({'errno': 100000, 'msg': '课程查询成功', 'data': course_list_json})


@csrf_exempt
def get_course(request):
    course_id = request.POST.get('course_id')
    user_id = request.POST.get('user_id')
    student = UserInfo.objects.get(user_id=user_id)
    course = Course.objects.get(course_id=course_id)
    print(course_id)
    if not course:
        return JsonResponse({'errno': 100001, 'msg': '未能找到对应的课程'})
    experiment = Experiment.objects.filter(user_id=user_id, course_id=course_id).first()
    score = Student_Courses.objects.filter(student_id=student, course_id=course).first()
    if not score:
        course_score = '教师未评分'
    else:
        course_score = score.course_score
    status = ''
    countdown = -1
    if not experiment:
        status = 'uncreated'
        # ssh_port = -1
        # ssh_password = ''
    else:
        status = 'running'
        countdown = experiment.get_remaining_time()
        # container_name = 'experiment_' + str(experiment.experiment_id)
        # print(container_name)
        # container = Container.objects.filter(container_name=container_name).first()
        # ssh_port = container.ssh_port
        # ssh_password = container.ssh_password
        print(countdown)
    data = {
        'course_id': course.course_id,
        'course_name': course.course_name,
        'course_intro': course.course_intro,
        'course_aim': course.course_aim,
        'course_difficulty': course.course_difficulty,
        'course_chapter': course.course_chapter.chapter_number,
        'course_limit_time': course.course_limit_time,
        'experiment_status': status,
        'experiment_countdown': countdown,
        'score': course_score,
        # 'ssh_port': ssh_port,
        # 'ssh_password': ssh_password,
    }
    return JsonResponse({'errno': 100000, 'msg': '查找课程成功', 'data': data})


