from django.urls import path

from . import views

app_name = 'clinical_portal'

urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('schedule/', views.my_schedule, name='my_schedule'),
    path('patient/<int:customer_id>/', views.patient_detail, name='patient_detail'),
    path('order/<int:order_id>/save-plan/', views.save_session_plan, name='save_session_plan'),
    path('session/<int:session_id>/book/', views.book_session, name='book_session'),
    path('session/<int:session_id>/complete/', views.complete_session, name='complete_session'),
    path('session/<int:session_id>/cancel/', views.cancel_session, name='cancel_session'),
]
