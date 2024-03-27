from django.urls import path
from . import views

urlpatterns = [
    path('show_container/', views.show_container, name='show_container'),
    path('show_images/', views.show_images, name='show_images'),
    path('add_new_container/', views.add_new_container, name='add_new_container'),
    path('add_new_image/', views.add_new_image, name='add_new_image'),
    path('stop_container/', views.stop_container, name='stop_container'),
    path('delete_container/', views.delete_container, name='delete_container'),
    path('delete_image/', views.delete_image, name='delete_image'),
    path('start_container/', views.start_container, name='start_container'),
    path('create_course/', views.create_course, name='create_course'),
    path('list_course/', views.list_course, name='list_course'),
    path('delete_course/', views.delete_course, name='delete_course'),
    path('get_course_info/', views.get_course_info, name='get_course_info'),
    path('create_experiment/', views.create_experiment, name='create_experiment'),
    path('delete_experiment/', views.delete_experiment, name='delete_experiment'),
]
