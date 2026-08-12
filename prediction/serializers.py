from rest_framework import serializers

class PredictionInputSerializer(serializers.Serializer):
    """Serializer matching your dataset columns"""
    student_db_id = serializers.IntegerField(required=False, allow_null=True)
    
    # Personal Info
    Age = serializers.FloatField(required=True, min_value=15, max_value=100)
    Gender = serializers.ChoiceField(choices=['Male', 'Female'], required=True)
    Department = serializers.ChoiceField(
        choices=['CS', 'Engineering', 'Business', 'Arts', 'Science'], 
        required=True
    )
    Semester = serializers.ChoiceField(
        choices=['Year 1', 'Year 2', 'Year 3', 'Year 4'],
        required=True
    )
    
    # Academic Performance
    GPA = serializers.FloatField(required=True, min_value=0, max_value=4)
    Semester_GPA = serializers.FloatField(required=False, min_value=0, max_value=4)
    CGPA = serializers.FloatField(required=True, min_value=0, max_value=4)
    Study_Hours_per_Day = serializers.FloatField(required=True, min_value=0, max_value=24)
    Attendance_Rate = serializers.FloatField(required=True, min_value=0, max_value=100)
    Assignment_Delay_Days = serializers.FloatField(required=False, min_value=0)
    
    # Financial & Support
    Family_Income = serializers.FloatField(required=False, min_value=0)
    Scholarship = serializers.ChoiceField(choices=['Yes', 'No'], required=False)
    Part_Time_Job = serializers.ChoiceField(choices=['Yes', 'No'], required=False)
    Parental_Education = serializers.ChoiceField(
        choices=['No Formal Education', 'High School', 'Bachelor', 'Master', 'PhD'],
        required=False
    )
    
    # Other Factors
    Internet_Access = serializers.ChoiceField(choices=['Yes', 'No'], required=False)
    Travel_Time_Minutes = serializers.FloatField(required=False, min_value=0)
    Stress_Index = serializers.FloatField(required=False, min_value=0, max_value=10)

class BatchPredictionSerializer(serializers.Serializer):
    """Serializer for batch prediction"""
    students = serializers.ListField(
        child=PredictionInputSerializer(),
        min_length=1,
        max_length=50
    )