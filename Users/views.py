from django.shortcuts import render,redirect,get_object_or_404 # type: ignore
from django.contrib.auth import authenticate,login,logout # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from django.views.decorators.cache import never_cache # type: ignore
from .forms import UserSignupForm,UserLoginForm # type: ignore
from .models import User,Address # type: ignore
import random
from django.core.mail import send_mail # type: ignore
from django.conf import settings # type: ignore
from django.utils import timezone # type: ignore
from django.core.cache import cache # type: ignore
from django.http import JsonResponse # type: ignore
from django.contrib import messages # type: ignore
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger # type: ignore
from django.urls import reverse,reverse_lazy # type: ignore
from datetime import timedelta
from django.db.models import Q # type: ignore
from Admin.views import admin_required
from django.views.decorators.http import require_POST
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.views import PasswordResetConfirmView
# Create your views here.

def Login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    error_message = None

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')


            user = authenticate(request, email = email , password = password)

            if user is not None:
                print(f"Authentication successfull for user : {user}")
                login(request, user)
                return redirect('home')
            
            else:
                error_message = "Invalid email or password"

        else :
            error_message = "Please correct the error below"
        
    else:
        form = UserLoginForm()
 
    return render(request,'Users/user-login.html', {'form' : form , 'error_message' : error_message})

def generate_otp():
    return random.randint(100000,999999)

def send_signup_email(email, otp):
    subject = 'Your OTP for Baka Store Registration'
    message = f"Your OTP for completing your registration at Baka Store is \n OTP : {otp}"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email, 'psreeraj711@gmail.com']
    try:
        send_mail(subject, message, from_email, recipient_list)
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")


def Signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            otp = generate_otp()
            email = form_data['email']
            request.session['email'] = email
            request.session['otp'] = otp
            request.session['form_data'] = form_data
            request.session['otp_created_at'] = timezone.now().isoformat()
            print(f"Generated OTP: {otp}") 
            send_signup_email(email, otp)
            messages.success(request, "Signup successful! An OTP has been sent to your email.")
            return redirect('verify-otp')
    else:
        form = UserSignupForm()
    return render(request, 'Users/user_signup.html', {'form': form})

def home(request):
    return render(request,'Users/home.html')

@never_cache
def verifyOTP(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        session_otp = request.session.get('otp')
        otp_created_at = request.session.get('otp_created_at')

        try:
            otp = int(otp)
        except (ValueError,TypeError):
            otp =None
        
        if otp_created_at:
            otp_created_at = timezone.datetime.fromisoformat(otp_created_at)
            if timezone.now() > otp_created_at + timezone.timedelta(minutes=2):
                return render(request, "Users/otp-verify.html", {'error' : 'OTP expired . Please request for new one.'})
            
        if otp == session_otp:
            print("reached here")
            form_data = request.session.get('form_data')
            if form_data:
                user = User.objects.create_user(
                    username=form_data['email'],
                    email= form_data['email'],
                    first_name = form_data['first_name'],
                    last_name = form_data['last_name'],
                    password= form_data['password1'],
                )
                user.is_active = True
                user.save()
                return redirect('user-login')
            
        else:
            if otp_created_at:
                countdown = max(0,int((otp_created_at + timezone.timedelta(minutes=2)- timezone.now()).total_seconds()))
                
            else:
                countdown = 120
            return  render(request, 'Users/otp-verify.html', {'error' : 'Invalid OTP' , 'countdown' : countdown})
    
    otp_created_at = request.session.get('otp_created_at')
    if otp_created_at:
        otp_created_at = timezone.datetime.fromisoformat(otp_created_at)
        countdown = max(0,int((otp_created_at + timezone.timedelta(minutes=2) - timezone.now()).total_seconds()))
        if countdown <= 0:
            countdown = 0
    else:
        countdown = 60

    return render(request, 'Users/otp-verify.html', {'countdown': countdown})
        


@never_cache
def resend_otp(request):
    email = request.session.get('email')
    if email:
        otp = generate_otp()
        print(f"OTP:{otp}")
        request.session['otp'] = otp
        request.session['otp_created_at'] = timezone.now().isoformat()
        send_signup_email(email, otp)
        return JsonResponse({'success': True, 'message': 'OTP resent successfully'})
    return JsonResponse({'success': False, 'message': 'Unable to resend OTP'})

def Logout(request):
    logout(request)
    return redirect('user-login')

def admin_users_list(request):
    query = request.GET.get('q')
    if query:
        users = User.objects.filter(
            Q(first_name__icontains = query) |
            Q(last_name__icontains = query) |
            Q(email__icontains = query) |
            Q(phone_number__icontains = query)
        )
    else :
        users = User.objects.all().order_by('-created_at')

    paginator = Paginator(users,10)
    page_number = request.GET.get('page')
    customers = paginator.get_page(page_number)
    return render(request, 'Admin/admin_customer_list.html',{'customers' : customers, 'query' : query})

@admin_required
def toggle_customer_status(request,user_id):
    user = get_object_or_404(User,id = user_id)
    user.is_active = not user.is_active
    user.save()
    action = "unblocked" if user.is_active else "blocked"
    messages.success(request, f"User {user.get_full_name()} has been {action}.")
    return redirect('customers')

def account_details(request):
    addresses = Address.objects.filter(user = request.user)
    return render(request, 'Users/profile.html', {'user' : request.user, 'addresses' : addresses})

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.phone_number = request.POST.get('phone_number')

        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        if current_password and new_password:
            if user.check_password(current_password):
                user.set_password(new_password)
            else:
                return JsonResponse({'success': False, 'error': 'Current password is incorrect'})
        
        try:
            user.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def get_address(request):
    address_id = request.GET.get('id')
    address = get_object_or_404(Address, id = address_id, user = request.user)
    return JsonResponse({
        'id' : address.id,
        'address_line1' : address.address_line1,
        'address_line2' : address.address_line2,
        'city' : address.city,
        'state' : address.state,
        'postal_code' : address.postal_code,
        'country' : address.country,
    })

def save_address(request):
    if request.method == 'POST':
        # Retrieve form data
        address_id = request.POST.get('address_id')
        address_line1 = request.POST.get('address_line1', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', '').strip()

        # Check if required fields are filled
        if not all([address_line1, city, state, postal_code, country]):
            return JsonResponse({'success': False, 'error': 'All required fields must be filled.'})

        if address_id:
            address = get_object_or_404(Address, id = address_id, user = request.user)
        else:
            address = Address(user = request.user)

        # Update the address fields
        address.address_line1 = address_line1
        address.address_line2 = request.POST.get('address_line2', '').strip()  # Optional field
        address.city = city
        address.state = state
        address.postal_code = postal_code
        address.country = country
        address.save()

        return JsonResponse({'success' : True})
    return JsonResponse({'success' : False, 'error' : 'Invalid request method'})

def delete_address(request, address_id):

    address = get_object_or_404(Address, id = address_id, user = request.user)
    print(f'this is the address{address}')
    try:
        address.delete()
        return JsonResponse({'success' : True})
    except Exception as e:
        return JsonResponse({'success' : False, 'error' : str(e) })


def upload_profile_photo(request):
    if request.method == 'POST' and 'profile_photo' in request.FILES:
        photo = request.FILES['profile_photo']
        request.user.profile_photo = photo
        request.user.save()
        return JsonResponse({
            'success' : True,
            'photo_url' : request.user.profile_photo.url,
        })
    return JsonResponse({'success' : False, 'error' : 'No file uploaded'}, status = 400)

def forget_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email = email)
        except User.DoesNotExist:
            return JsonResponse({'success' : False, 'message' : 'No user found with this email address.'})
        
        #Generate password reset link
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        #Create password reset link
        reset_url = request.build_absolute_uri(
            reverse('password_reset_confirm', kwargs={'uidb64' : uid, 'token' : token})
        )

        subject = 'Password Reset for Baka Store'
        message = f'Click the following link to reset your password :{reset_url}'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email,settings.EMAIL_HOST_USER]

        try:
            send_mail(subject, message, from_email, recipient_list)
            return JsonResponse({'success' : True, 'message' : 'Password reset link to your email.'})
        except Exception as e:
            return JsonResponse({'success' : False, 'message' : 'Failed to send email. Please try again later.'})
    return render(request, 'Users/forget_password.html')

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'Users/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

def password_reset_complete(request):
    return render(request, 'Users/password_reset_complete.html')