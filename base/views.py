import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from geopy.geocoders import Nominatim
from .models import *
from .forms import InternRegistrationForm, OrganizationForm, CustomAuthenticationForm, ProfileCompletionForm
from datetime import datetime, timedelta
from django.contrib.auth import logout, authenticate, login
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied



# Utility Functions
def get_address_from_coords(lat, lng):
    """Reverse geocode coordinates to get address"""
    geolocator = Nominatim(user_agent="intern_tracker")
    location = geolocator.reverse(f"{lat}, {lng}")
    return location.address if location else "Unknown location"

def check_geofence(point, organization):
    """Check if point is within organization's geofence"""
    return organization.location.distance(point) * 100000 <= organization.geofence_radius

# Authentication Views
def register(request):
    if request.method == 'POST':
        form = InternRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_intern = True
            user.save()
            messages.success(request, "Account created! Please complete your profile.")
            login(request, user)  # Auto-login after registration
            return redirect('send_otp')
    else:
        form = InternRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'login.html', {'form': form})





@login_required
def dashboard(request):
    try:
        intern = request.user.intern
        org = intern.organization
        
        today = datetime.now().date()
        locations = LocationLog.objects.filter(
            intern=intern,
            timestamp__date=today
        ).order_by('-timestamp')[:10]
        
        violations_today = LocationLog.objects.filter(
            intern=intern,
            is_inside_geofence=False,
            timestamp__date=today
        ).count()
        
        context = {
            'intern': intern,
            'organization': org,
            'locations': locations,
            'violations_today': violations_today,
            'mapbox_access_token': 'your_mapbox_access_token',
        }
        return render(request, 'dashboard.html', context)
        
    except Exception as e:
        print(f"Redirecting to profile complete - {str(e)}")
        return redirect('profile_complete')

@login_required
def profile_complete(request):
    # Check if profile exists
    if hasattr(request.user, 'intern'):
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = ProfileCompletionForm(request.POST)
        if form.is_valid():
            try:
                profile = form.save(commit=False)
                profile.user = request.user
                
                # Set required fields
                profile.first_name = request.user.first_name
                profile.last_name = request.user.last_name
                
                # Set defaults for required fields if not provided
                if not profile.department:
                    profile.department = "Not specified"
                
                profile.save()
                messages.success(request, "Profile completed successfully!")
                return redirect('dashboard')
                
            except IntegrityError:
                messages.error(request, "Profile already exists for this account")
                return redirect('dashboard')
                
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect('profile_complete')
    else:
        form = ProfileCompletionForm()
    
    return render(request, 'profile_complete.html', {'form': form})





# Dashboard Views
# @login_required
# def dashboard(request):
#     if not hasattr(request.user, 'internprofile'):
#         return redirect('profile_complete')
    
#     intern = request.user.internprofile
#     org = intern.organization
#     today = datetime.now().date()
    
    
#     locations = LocationLog.objects.filter(
#         intern=intern,
#         timestamp__date=today
#     ).order_by('-timestamp')[:10]
    
    
#     violations_today = LocationLog.objects.filter(
#         intern=intern,
#         is_inside_geofence=False,
#         timestamp__date=today
#     ).count()
    
#     context = {
#         'intern': intern,
#         'organization': org,
#         'locations': locations,
#         'violations_today': violations_today,
#         'mapbox_access_token': 'your_mapbox_access_token',
#     }
#     return render(request, 'dashboard.html', context)


# @login_required
# def profile_complete(request):
#     has_profile = hasattr(request.user, 'internprofile')
    
#     if has_profile and request.method == 'GET':
#         messages.info(request, "Your profile is already complete")
#         return redirect('dashboard')
        
#     if request.method == 'POST':
#         form = ProfileCompletionForm(request.POST)
#         if form.is_valid():
#             try:
#                 # Double-check in case of race condition
#                 if hasattr(request.user, 'internprofile'):
#                     messages.warning(request, "Profile already exists")
#                     return redirect('dashboard')
                    
#                 profile = form.save(commit=False)
#                 profile.user = request.user
                
#                 try:
#                     if not profile.department:
#                         profile.department = "Not specified"

#                     # profile.full_clean()
#                     profile.save()
#                     messages.success(request, "Profile completed successfully!")
#                     return redirect('dashboard')
                    
#                 except ValidationError as e:
#                     for field, errors in e.message_dict.items():
#                         for error in errors:
#                             messages.error(request, f"{field}: {error}")
                            
#                 except IntegrityError as e:
#                     if 'base_internprofile_user_id_key' in str(e):
#                         messages.error(request, "Profile already exists for this account")
#                     else:
#                         messages.error(request, "An error occurred while saving your profile")
#                     return redirect('profile_complete')
                    
#             except Exception as e:
#                 messages.error(request, "An unexpected error occurred")
#                 return redirect('profile_complete')
                
#         else:
#             for field, errors in form.errors.items():
#                 for error in errors:
#                     messages.error(request, f"{field}: {error}")
#     else:
#         form = ProfileCompletionForm()
    
#     return render(request, 'profile_complete.html', {
#         'form': form,
#         'has_profile': hasattr(request.user, 'internprofile')
#     })

# Location Tracking API
@csrf_exempt
@login_required
def update_location(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        # Ensure proper JSON content
        if not request.body:
            return JsonResponse({'status': 'error', 'message': 'Empty request body'}, status=400)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

        # Validate required fields
        if 'latitude' not in data or 'longitude' not in data:
            return JsonResponse({'status': 'error', 'message': 'Missing latitude/longitude'}, status=400)

        try:
            lat = float(data['latitude'])
            lng = float(data['longitude'])
            point = Point(lng, lat, srid=4326)
        except (ValueError, TypeError):
            return JsonResponse({'status': 'error', 'message': 'Invalid coordinates'}, status=400)

        # Check user profile
        if not hasattr(request.user, 'internprofile'):
            return JsonResponse({'status': 'error', 'message': 'User has no intern profile'}, status=400)

        intern = request.user.internprofile
        
        # Check if organization exists
        if not intern.organization:
            return JsonResponse({'status': 'error', 'message': 'No organization assigned'}, status=400)

        # Get address and check geofence
        address = get_address_from_coords(lat, lng) or "Unknown"
        is_inside = check_geofence(point, intern.organization)

        # Save location
        LocationLog.objects.create(
            intern=intern,
            point=point,
            accuracy=data.get('accuracy'),
            address=address,
            is_inside_geofence=is_inside
        )

        return JsonResponse({
            'status': 'success',
            'is_inside': is_inside,
            'address': address
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# Intern Management
@login_required
def intern_list(request):
    if not request.user.is_supervisor:
        messages.error(request, "You don't have permission to view this page")
        return redirect('dashboard')
    
    organization = request.user.supervisorprofile.organization
    interns = InternProfile.objects.filter(organization=organization)
    
    return render(request, 'list.html', {
        'interns': interns,
        'organization': organization
    })

@login_required
def intern_detail(request, pk):
    intern = get_object_or_404(Intern, pk=pk)
    # Verify permissions using the new profile structure
    if hasattr(request.user, 'profile') and request.user.profile.is_supervisor:
        try:
            supervisor_org = request.user.profile.supervisor_profile.organization
            if supervisor_org != intern.organization:
                messages.error(request, "You don't have permission to view this intern")
                return redirect('intern_list')
        except AttributeError:
            messages.error(request, "Supervisor profile not complete")
            return redirect('intern_list')
    
    # Get time filter from query params
    time_filter = request.GET.get('time', 'today')
    
    if time_filter == 'week':
        date_filter = datetime.now() - timedelta(days=7)
    elif time_filter == 'month':
        date_filter = datetime.now() - timedelta(days=30)
    else:  # today
        date_filter = datetime.now() - timedelta(days=1)
    
    locations = LocationLog.objects.filter(
        intern=intern,
        timestamp__gte=date_filter
    ).order_by('-timestamp')
    
    violations = locations.filter(is_inside_geofence=False)
    
    return render(request, 'detail.html', {
        'intern': intern,
        'locations': locations[:50],  # Limit to 50 most recent
        'violations': violations.count(),
        'time_filter': time_filter
    })

# Organization Management
@login_required
def organization_dashboard(request):
    if not request.user.is_supervisor:
        messages.error(request, "Access denied")
        return redirect('dashboard')
    
    org = request.user.supervisorprofile.organization
    interns = InternProfile.objects.filter(organization=org)
    
    # Stats for dashboard
    active_interns = interns.filter(is_active=True).count()
    violations_today = LocationLog.objects.filter(
        intern__organization=org,
        is_inside_geofence=False,
        timestamp__date=datetime.now().date()
    ).count()
    
    return render(request, 'dashboard.html', {
        'organization': org,
        'active_interns': active_interns,
        'violations_today': violations_today,
        'mapbox_access_token': 'your_mapbox_access_token'
    })

@login_required
def edit_organization(request):
    if not request.user.is_supervisor:
        messages.error(request, "Access denied")
        return redirect('dashboard')
    
    org = request.user.supervisorprofile.organization
    
    if request.method == 'POST':
        form = OrganizationForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            messages.success(request, "Organization updated successfully")
            return redirect('organization_dashboard')
    else:
        form = OrganizationForm(instance=org)
    
    return render(request, 'edit.html', {'form': form})

# Reporting Views
# @login_required
# def location_history(request):
#     intern = request.user.internprofile
#     time_filter = request.GET.get('time', 'today')
    
#     if time_filter == 'week':
#         date_filter = datetime.now() - timedelta(days=7)
#     elif time_filter == 'month':
#         date_filter = datetime.now() - timedelta(days=30)
#     else:  # today
#         date_filter = datetime.now() - timedelta(days=1)
    
#     locations = LocationLog.objects.filter(
#         intern=intern,
#         timestamp__gte=date_filter
#     ).order_by('-timestamp')
    
#     return render(request, 'location_history.html', {
#         'locations': locations,
#         'time_filter': time_filter
#     })


@login_required
def location_history(request, pk=None):
    # If intern_id is provided, check permissions
    if pk:
        if not request.user.is_superuser and not request.user.is_staff:
            raise PermissionDenied
        intern = get_object_or_404(InternProfile, id=pk)
    else:
        # For regular users, show their own history
        intern = request.user.internprofile
    
    time_filter = request.GET.get('time', 'today')
    
    if time_filter == 'week':
        date_filter = datetime.now() - timedelta(days=7)
    elif time_filter == 'month':
        date_filter = datetime.now() - timedelta(days=30)
    else:  # today
        date_filter = datetime.now() - timedelta(days=1)
    
    locations = LocationLog.objects.filter(
        intern=intern,
        timestamp__gte=date_filter
    ).order_by('-timestamp')
    
    return render(request, 'location_history.html', {
        'locations': locations,
        'time_filter': time_filter,
        'intern': intern
    })


# @login_required
# def geofence_violations(request):
#     if request.user.is_intern:
#         intern = request.user.internprofile
#         violations = LocationLog.objects.filter(
#             intern=intern,
#             is_inside_geofence=False
#         ).order_by('-timestamp')
#     else:  # supervisor
#         org = request.user.supervisorprofile.organization
#         violations = LocationLog.objects.filter(
#             intern__organization=org,
#             is_inside_geofence=False
#         ).order_by('-timestamp')
    
#     return render(request, 'geofence_violations.html', {
#         'violations': violations
#     })



@login_required
def geofence_violations(request, intern_id=None):
    # If intern_id is provided (for supervisor viewing specific intern)
    if intern_id:
        if not (request.user.is_supervisor or request.user.is_staff):
            raise PermissionDenied
        intern = get_object_or_404(InternProfile, id=intern_id)
        violations = LocationLog.objects.filter(
            intern=intern,
            is_inside_geofence=False
        ).order_by('-timestamp')
    # For regular intern viewing their own violations
    elif request.user.is_intern:
        intern = request.user.internprofile
        violations = LocationLog.objects.filter(
            intern=intern,
            is_inside_geofence=False
        ).order_by('-timestamp')
    # For supervisor viewing all violations in their organization
    else:
        org = request.user.supervisorprofile.organization
        violations = LocationLog.objects.filter(
            intern__organization=org,
            is_inside_geofence=False
        ).order_by('-timestamp')
    
    return render(request, 'geofence_violations.html', {
        'violations': violations,
        'specific_intern': intern if intern_id else None
    })




def user_logout(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')  



from .forms import EmailForm, OTPForm
import uuid

def send_otp(request):
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                otp = OTP.generate_otp(user)
                
                # Send email
                send_mail(
                    'Your Secure OTP Code',
                    f'Your verification code is: {otp.otp}\n\nThis code will expire in 15 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                
                request.session['otp_user_id'] = user.id
                request.session['otp_token'] = str(otp.token)
                return redirect('verify_otp')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address.')
    else:
        form = EmailForm()
    
    return render(request, 'accounts/send_otp.html', {'form': form})

def verify_otp(request):
    if 'otp_user_id' not in request.session:
        return redirect('send_otp')
    
    user_id = request.session['otp_user_id']
    otp_token = request.session.get('otp_token')
    
    try:
        user = User.objects.get(id=user_id)
        otp = OTP.objects.get(user=user, token=otp_token)
        
        if request.method == 'POST':
            form = OTPForm(request.POST)
            if form.is_valid():
                entered_otp = form.cleaned_data['otp']
                
                if otp.is_expired():
                    messages.error(request, 'OTP has expired. Please request a new one.')
                    return redirect('send_otp')
                
                if otp.otp == entered_otp:
                    otp.is_verified = True
                    otp.save()
                    login(request, user)
                    del request.session['otp_user_id']
                    del request.session['otp_token']
                    return redirect('otp_success')
                else:
                    messages.error(request, 'Invalid OTP. Please try again.')
        else:
            form = OTPForm()
        
        return render(request, 'accounts/verify_otp.html', {
            'form': form,
            'email': user.email
        })
    
    except (User.DoesNotExist, OTP.DoesNotExist):
        messages.error(request, 'Invalid session. Please try again.')
        return redirect('send_otp')

def otp_success(request):
    return render(request, 'accounts/otp_success.html')

# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import WebAuthnCredential
import json

@csrf_exempt
def check_user(request):
    if request.method == 'GET':
        email = request.GET.get('email')
        exists = User.objects.filter(email=email).exists()
        return JsonResponse({'exists': exists})

@csrf_exempt
def register_credential(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = User.objects.get(email=data['email'])
            
            WebAuthnCredential.objects.create(
                user=user,
                credential_id=data['credential_id'],
                public_key=data['public_key'],
                counter=data['counter'],
                device_type=data['device_type'],
                backed_up=data['backed_up'],
                transports=data['transports']
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def get_credentials(request):
    if request.method == 'GET':
        email = request.GET.get('email')
        try:
            user = User.objects.get(email=email)
            credentials = WebAuthnCredential.objects.filter(user=user)
            creds_list = [{
                'id': cred.credential_id,
                'transports': cred.transports
            } for cred in credentials]
            return JsonResponse({'credentials': creds_list})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)


@csrf_exempt
def update_counter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = User.objects.get(email=data['email'])
            credential = WebAuthnCredential.objects.get(
                user=user,
                credential_id=data['credential_id']
            )
            credential.counter = data['new_counter']
            credential.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)