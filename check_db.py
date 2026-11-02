import os
import sys
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from students.models import Student

User = get_user_model()

print("USERS IN DATABASE:")
for u in User.objects.all():
    print(f"ID: {u.id}, Username: {u.username}, Email: {u.email}, UserType: {u.user_type}, IsSuperuser: {u.is_superuser}")
    try:
        student = Student.objects.get(user=u)
        print(f"  -> Has Student Profile: {student.student_id}, ID: {student.id}")
    except Student.DoesNotExist:
        print("  -> No Student Profile")
