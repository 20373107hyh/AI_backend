import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from student.models import Student_Courses
from teacher.models import Course

# Create your views here.
@csrf_exempt
def get_course_list(request):
    request_data = json.loads(request.body.decode('utf-8'))
    student_id = request_data['student_id']
    student_courses = Student_Courses.objects.filter(student_id = student_id)
    courses_info = []

    for student_course in student_courses:
        course_info = {
            'course_id': student_course.course_id.course_id,
            'course_name': student_course.course_id.course_name,
            'course_intro': student_course.course_id.course_intro,
            'course_chapter': student_course.course_id.course_chapter,
            'create_time': student_course.course_id.create_time,
            'update_time': student_course.course_id.update_time,
        }
        courses_info.append(course_info)

    if courses_info:
        return JsonResponse({'errno': 100000, 'msg': '请求课程成功', 'data': courses_info})
    else:
        return JsonResponse({'errno': 100001, 'msg': '未能找到该学生的课程'})

@csrf_exempt
def get_course(request):
    request_data = json.loads(request.body.decode('utf-8'))
    course_id = request_data['course_id']
    course = Course.objects.filter(course_id = course_id).first()
    if not course:
        return JsonResponse({'errno': 100001, 'msg': '未能找到对应的课程'})
    data = {
        'course_id': course.course_id,
        'course_name': course.course_name,
        'course_intro': course.course_intro,
        'course_chapter': course.course_chapter,
        'create_time': course.create_time,
        'update_time': course.update_time
    }
    return JsonResponse({'errno': 100000, 'msg': '查找课程成功', 'data': data})

