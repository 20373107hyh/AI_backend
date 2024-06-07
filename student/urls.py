from django.urls import path
from . import views

urlpatterns = [
    path("get_course_list/", views.get_course_list, name="get_course_list"),
    path("get_course/", views.get_course, name="get_course"),
    path('list_course_by_chapter/', views.list_course_by_chapter, name='list_course_by_chapter'),
    path('get_user_info/', views.get_user_info, name='get_user_info'),
]
