from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User
import random
import uuid
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging
from django.core.validators import MinLengthValidator




class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_supervisor = models.BooleanField(default=False)
    is_intern = models.BooleanField(default=False)
    
    
    
    def __str__(self):
        return f"Profile for {self.user.username}"



class SupervisorProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='supervisor_profile')
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True)
    phone = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.user_profile.user.get_full_name()} (Supervisor)"







# Create your models here.
class University(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    partnership_since = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'University'
        verbose_name_plural = 'Universities'

    def __str__(self):
        return self.name







class Department(models.Model):
    # Basic Information
    name = models.CharField(max_length=100, unique=True, null=True)
    code = models.CharField(max_length=10, unique=True, help_text="Short department code (e.g., HR-001)", null=True)
    parent_department = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_departments'
    )
    
    # Operational Details
    location = models.CharField(max_length=100, blank=True)
    floor = models.CharField(max_length=20, blank=True)
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual department budget"
    )
    
    # HR Specific Fields
    headcount = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    established_date = models.DateField(null=True, blank=True)
    
    # Contact Information
    phone_extension = models.CharField(max_length=10, blank=True)
    internal_email = models.EmailField(blank=True)
    
    # Additional Metadata
    description = models.TextField(blank=True)
    mission_statement = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        permissions = [
            ('can_manage_department', 'Can manage department settings'),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def save(self, *args, **kwargs):
        if not self.code:
            # Auto-generate department code if not provided
            prefix = self.department_type.upper()
            last_dept = Department.objects.filter(
                department_type=self.department_type
            ).order_by('-code').first()
            if last_dept:
                last_num = int(last_dept.code.split('-')[-1])
                self.code = f"{prefix}-{last_num + 1:03d}"
            else:
                self.code = f"{prefix}-001"
        super().save(*args, **kwargs)
    
    @property
    def current_headcount(self):
        """Returns actual count of active employees in department"""
        return self.employee_set.filter(is_active=True).count()
    
    @property
    def budget_utilization(self):
        """Calculates percentage of budget used"""
        if self.budget and self.budget > 0:
            total_salaries = sum(
                emp.salary for emp in self.employees.filter(is_active=True)
            )
            return (total_salaries / self.budget) * 100
        return 0






class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=20, null=True)
    employee_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    position = models.CharField(max_length=100)  # e.g., "HR Manager", "Developer"
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.employee_id








class Intern(models.Model):
    # User relationship
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='intern',
        null=True
    )
    
    # Personal Information
    first_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('U', 'Prefer not to say'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    image = models.ImageField(upload_to='interns/images/', null=True, blank=True)
    
    # Contact Information
    personal_email = models.EmailField(unique=True, null=True)
    phone_number = models.CharField(max_length=20, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Organization Information (moved from InternProfile)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True)
    department = models.ForeignKey('Department', on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True)
    
    # Academic Information
    university = models.ForeignKey(
        'University',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    degree_program = models.CharField(max_length=100, blank=True, null=True)
    current_year = models.PositiveSmallIntegerField(null=True, blank=True)
    expected_graduation = models.DateField(null=True, blank=True)
    transcript = models.FileField(upload_to='interns/transcripts/', null=True, blank=True)
    
    # Internship Details
    internship_start_date = models.DateField(null=True)
    internship_end_date = models.DateField(null=True)
    mentor = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mentored_interns'
    )
    INTERNSHIP_STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('terminated', 'Terminated'),
        ('extended', 'Extended'),
    ]
    status = models.CharField(
        max_length=20,
        choices=INTERNSHIP_STATUS_CHOICES,
        default='active'
    )
    
    # HR Administration
    stipend_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    resume = models.FileField(upload_to='interns/resumes/', null=True, blank=True)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['first_name']
        verbose_name = 'Intern'
        verbose_name_plural = 'Interns'
        permissions = [
            ('manage_interns', 'Can manage all intern records'),
        ]

    def __str__(self):
        return f"{self.first_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def internship_duration(self):
        return (self.internship_end_date - self.internship_start_date).days
    
    @property
    def days_remaining(self):
        if self.status == 'active':
            return (self.internship_end_date - timezone.now().date()).days
        return 0
    
    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

        







class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True)
    date = models.DateField()
    check_in = models.TimeField()
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ])

    def __str__(self):
        return 'self.employee'

class LeaveRequest(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')



class PerformanceReview(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    rating = models.IntegerField(choices=[(1, 'Poor'), (5, 'Excellent')])
    comments = models.TextField()

class Skill(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Python", "Project Management"
    employees = models.ManyToManyField(Employee, through='EmployeeSkill')

class EmployeeSkill(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert'),
    ])

class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.DateField()  # Stores year-month (e.g., 2023-10-01)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)

class Benefit(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Health Insurance"
    description = models.TextField()
    employees = models.ManyToManyField(Employee, through='EmployeeBenefit')

class EmployeeBenefit(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    benefit = models.ForeignKey(Benefit, on_delete=models.CASCADE)
    enrollment_date = models.DateField()


class JobOpening(models.Model):
    title = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    description = models.TextField()
    requirements = models.TextField()
    posted_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

class Application(models.Model):
    job = models.ForeignKey(JobOpening, on_delete=models.CASCADE)
    applicant_name = models.CharField(max_length=100)
    applicant_email = models.EmailField()
    resume = models.FileField(upload_to='resumes/')
    status = models.CharField(max_length=20, choices=[
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
    ], default='submitted')
    created_at = models.DateTimeField(auto_now_add=True)  # Add this field if missing

    def __str__(self):
        return f"{self.applicant_name} - {self.job.title}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class CompanyProfile(models.Model):
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='company/')
    address = models.TextField()
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)






class Organization(models.Model):
    name = models.CharField(max_length=255)
    location = gis_models.PointField(null=True, blank=True)
    geofence_radius = models.PositiveIntegerField(
        default=100,  # Default 100m radius
        help_text="Radius in meters"
    )
    address = models.TextField(blank=True)
    
    LOCATION_SOURCE_CHOICES = [
        ('manual', 'Manual Entry'),
        ('geocode', 'Geocode from Address'),
        ('first_checkin', 'Derive from First Intern Check-in'),
        ('pending', 'Pending Automatic Detection')
    ]
    location_source = models.CharField(
        max_length=20,
        choices=LOCATION_SOURCE_CHOICES,
        default='pending'
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.location_source == 'geocode' and self.address and not self.location:
            self.geocode_from_address()
        super().save(*args, **kwargs)
    
    def geocode_from_address(self):
        try:
            geolocator = Nominatim(user_agent="base")
            location = geolocator.geocode(self.address)
            if location:
                self.location = Point(location.longitude, location.latitude)
                self.location_source = 'geocode'
                return True
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding failed for {self.name}: {str(e)}")
        return False

    def get_intern_count(self):
        """Returns count of active interns in this organization"""
        return self.intern_set.filter(is_active=True).count()

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"




    

class LocationLog(models.Model):
    intern = models.ForeignKey(Intern, on_delete=models.CASCADE)
    point = gis_models.PointField()
    timestamp = models.DateTimeField(auto_now_add=True)
    accuracy = models.FloatField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    is_inside_geofence = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        status = "Inside" if self.is_inside_geofence else "Outside"
        return f"{self.intern} at {self.point} ({status})"






class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    @classmethod
    def generate_otp(cls, user):
        # Delete expired OTPs
        cls.objects.filter(user=user, expires_at__lt=timezone.now()).delete()
        
        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timezone.timedelta(minutes=15)
        return cls.objects.create(user=user, otp=otp, expires_at=expires_at)
    
    def is_expired(self):
        return timezone.now() > self.expires_at


# models.py
from django.db import models
from django.contrib.auth.models import User

class WebAuthnCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    credential_id = models.TextField()  # Stores the Base64 encoded credential ID
    public_key = models.TextField()  # Stores the Base64 encoded public key
    counter = models.IntegerField()
    device_type = models.CharField(max_length=100)
    backed_up = models.BooleanField()
    transports = models.JSONField(default=list)
    
    class Meta:
        unique_together = ('user', 'credential_id')