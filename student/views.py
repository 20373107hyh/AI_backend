import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from student.models import Student_Courses
from teacher.models import Course


@csrf_exempt
def get_course_list(request):

    courses_list = Course.objects.all().order_by('course_chapter')
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
def get_course(request):
    course_id = request.POST.get('course_id')
    print(course_id)
    course = Course.objects.filter(course_id=course_id).first()
    if not course:
        return JsonResponse({'errno': 100001, 'msg': '未能找到对应的课程'})
    data = {
        'course_id': course.course_id,
        'course_name': course.course_name,
        'course_intro': course.course_intro,
        'course_aim': course.course_aim,
        'course_difficulty': course.course_difficulty,
        'course_chapter': course.course_chapter.chapter_number,
        'course_limit_time': course.course_limit_time,
    }
    return JsonResponse({'errno': 100000, 'msg': '查找课程成功', 'data': data})


