from django.urls import path
from app import views

urlpatterns = [
    path('list/', views.PersonList.as_view()),
    path('list/<int:pk>', views.PersonDetail.as_view()),
]