from django.shortcuts import render, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from users.models import UserInfo
from django.http import JsonResponse
import json


@csrf_exempt
def login(request):
    print(request.body)
    info = json.loads(request.body.decode('utf-8'))
    username = info['username']
    password = info['password']
    current_user = (
            UserInfo.objects.filter(username = username).first() or
            UserInfo.objects.filter(email = username).first() or
            UserInfo.objects.filter(phone = username).first()
    )
    if current_user is None:
        print(2)
        return JsonResponse({'errno': 100002, 'msg': '用户不存在'})
    if password != current_user.password:
        print(3)
        return JsonResponse({'errno': 100003, 'msg': '密码错误'})
    if not request.session.session_key:
        request.session.save()  # 保存之后生成session_key，之后前端以此为标头请求后端
    session_id = request.session.session_key
    print(f"Session ID: {request.session.session_key}")
    print(f"Session UID: {request.session.get('uid')}")
    data = {
        'user_id': current_user.user_id,
        'username': current_user.username,
        'password': current_user.password,
        'session_id': session_id,
        'realname': current_user.realname,
        'email': current_user.email,
        'phone': current_user.phone,
        'status': current_user.status
    }
    return JsonResponse({'errno': 100000, 'msg': '登陆成功', 'data': data})


@csrf_exempt
def register(request):
    return HttpResponse("注册界面")


@csrf_exempt
def logout(request):
    return JsonResponse({'errno': 100000, 'msg': '登出成功'})