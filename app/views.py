from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .models import User
from .forms import LoginForm, RegisterForm,BillSearchForm,BillForm,AvatarForm
from django.contrib import messages  
from rest_framework import viewsets
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from .models import ElectricityBill
import json
from django.shortcuts import render
from .models import ElectricityBill
from django.db.models import Avg
from sklearn.linear_model import LinearRegression
import numpy as np
import datetime
from .forms import UserChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.db.models.functions import TruncMonth, TruncQuarter, ExtractYear
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import datetime
from .models import ElectricityBill
from .forms import PeriodSelectForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import ElectricityBill, UserBillPermissions
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False) 
            user.set_password(form.cleaned_data['password'])  
            user.save() 
            messages.success(request, 'Bạn đã đăng ký thành công. Vui lòng đăng nhập.')
            return redirect('/')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  
            else:
                messages.error(request, 'Tài khoản hoặc mật khẩu không chính xác')
        else:
            messages.error(request, 'Thông tin nhập vào form không hợp lệ')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})
@login_required(login_url='login')
def home_view(request):
    return render(request,'home.html')
from django.contrib.auth import update_session_auth_hash
from .forms import UserChangeForm, AvatarForm, PasswordChangeForm

@login_required(login_url='login')
def account_view(request):
    user = request.user
    user_form = UserChangeForm(request.POST or None, instance=user)
    avatar_form = AvatarForm(request.POST, request.FILES, instance=user)
    password_form = PasswordChangeForm(user=request.user, data=request.POST or None)

    if request.method == 'POST':
        if 'change_info' in request.POST:
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Thông tin tài khoản của bạn đã được cập nhật thành công.')
                return redirect('account')

        if 'change_avatar' in request.POST:
            if avatar_form.is_valid():
                avatar = request.FILES.get('avatar')
                if avatar:
                    if not avatar.closed:
                        data = avatar.read()
                        avatar_file = ContentFile(data)
                    else:
                        avatar_file = ContentFile(avatar.file.getvalue())
                    if user.avatar:
                        user.avatar.delete(save=False)

                    user.avatar.save(avatar.name, avatar_file, save=True)
                    messages.success(request, 'Ảnh đại diện của bạn đã được cập nhật thành công.')
                    return redirect('account')
                else:
                    messages.error(request, 'Không tải được file. Vui lòng thử lại.')

        if 'change_password' in request.POST:
            print("Received POST request for changing password")
            print("Old Password Input:", request.POST.get('old_password'))
            print("New Password1 Input:", request.POST.get('new_password1'))
            print("New Password2 Input:", request.POST.get('new_password2'))
            if password_form.is_valid():
                print("Password form is valid")
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Mật khẩu của bạn đã được thay đổi thành công.')
                return redirect('account')
            else:
                print("Password form errors:", password_form.errors)
                messages.error(request, 'Vui lòng kiểm tra lại thông tin.')    

    return render(request, 'account.html', {
        'user_form': user_form,
        'avatar_form': avatar_form,
        'password_form': password_form,
        'user': user
    })

@login_required(login_url='login')
def search_bills(request):
    # Kiểm tra quyền xem hóa đơn
    if not request.user.is_superuser and not hasattr(request.user, 'bill_permissions') or not request.user.bill_permissions.can_view:
        raise PermissionDenied("Bạn không có quyền xem hóa đơn.")

    form = BillSearchForm(request.GET or None)
    bills = ElectricityBill.objects.filter(user=request.user).order_by('-payment_date')

    if form.is_valid():
        month = form.cleaned_data.get('month')
        year = form.cleaned_data.get('year')
        consumption = form.cleaned_data.get('consumption')
        water_consumption = form.cleaned_data.get('water_consumption')

        if month and year:
            start_date = datetime.date(int(year), int(month), 1)
            end_date = datetime.date(int(year), int(month), 28)
            bills = bills.filter(payment_date__range=[start_date, end_date])

        if consumption:
            if consumption == '<10':
                bills = bills.filter(consumption__lt=10)
            elif consumption == '10-30':
                bills = bills.filter(consumption__gte=10, consumption__lt=30)
            elif consumption == '30-100':
                bills = bills.filter(consumption__gte=30, consumption__lt=100)
            elif consumption == '100-200':
                bills = bills.filter(consumption__gte=100, consumption__lt=200)
            elif consumption == '>=200':
                bills = bills.filter(consumption__gte=200)

        if water_consumption:
            if water_consumption == '<10':
                bills = bills.filter(water_consumption__lt=10)
            elif water_consumption == '10-30':
                bills = bills.filter(water_consumption__gte=10, water_consumption__lt=30)
            elif water_consumption == '30-50':
                bills = bills.filter(water_consumption__gte=30, water_consumption__lt=50)
            elif water_consumption == '>=50':
                bills = bills.filter(water_consumption__gte=50)

    return render(request, 'timkiem.html', {'form': form, 'bills': bills})


@login_required(login_url='login')
def add_bill(request):
    # Kiểm tra quyền thêm hóa đơn
    if not request.user.is_superuser and not request.user.bill_permissions.can_add:
        raise PermissionDenied("Bạn không có quyền thêm hóa đơn mới.")
    
    if request.method == 'POST':
        form = BillForm(request.POST)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.user = request.user  # Liên kết hóa đơn với người dùng hiện tại
            bill.save()
            messages.success(request, "Hóa đơn mới đã được thêm thành công.")
            return redirect('search')
        else:
            messages.error(request, "Đã xảy ra lỗi. Vui lòng kiểm tra lại thông tin.")
    else:
        form = BillForm()

    return render(request, 'add_bill.html', {'form': form})


def get_quarter_label(date):
    # Hàm này sẽ trả về nhãn cho quý dựa trên ngày
    quarter = (date.month - 1) // 3 + 1
    return f'{date.year}-Q{quarter}'

from django.shortcuts import render
from django.db.models import Max
from .forms import PeriodSelectForm
from .models import ElectricityBill
from django.db.models import Sum, F
from django.db.models.functions import TruncMonth, TruncQuarter, ExtractYear
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
@login_required(login_url='login')
def statistics_view(request):
    form = PeriodSelectForm(request.POST or None)
    chart_data = {}
    comparison_info = {}
    if request.method == 'POST' and form.is_valid():
        period = form.cleaned_data['period']
        # Lấy ngày thanh toán mới nhất từ bảng ElectricityBill của người dùng hiện tại
        latest_payment_date = ElectricityBill.objects.filter(user=request.user).aggregate(latest_date=Max('payment_date'))['latest_date']
        if not latest_payment_date:
            return render(request, 'thongke.html', {'form': form, 'error': 'No data available for current user.'})
        current_date = latest_payment_date
        if period == 'monthly':
            start_date = current_date.replace(day=1) - relativedelta(months=5)
            current_period_start = current_date.replace(day=1)
            previous_period_start = current_period_start - relativedelta(months=1)
        elif period == 'quarterly':
            current_quarter = (current_date.month - 1) // 3 + 1
            start_month = 3 * (current_quarter - 1) + 1
            start_date = datetime.date(current_date.year, start_month, 1) - relativedelta(months=15)
            current_period_start = datetime.date(current_date.year, start_month, 1)
            previous_period_start = current_period_start - relativedelta(months=3)
        elif period == 'yearly':
            start_date = datetime.date(current_date.year, 1, 1) - relativedelta(years=5)
            current_period_start = datetime.date(current_date.year, 1, 1)
            previous_period_start = current_period_start - relativedelta(years=1)
        # Truy vấn và nhóm dữ liệu chỉ cho người dùng hiện tại
        bills = ElectricityBill.objects.filter(user=request.user, payment_date__range=[start_date, current_date])
        period_annotation = TruncMonth('payment_date') if period == 'monthly' else TruncQuarter('payment_date') if period == 'quarterly' else ExtractYear('payment_date')
        bills = bills.annotate(period=period_annotation).values('period').annotate(total_spent=Sum(F('unit_price') * F('consumption') + F('water_price') * F('water_consumption'))).order_by('period')
        # Chuẩn bị dữ liệu cho biểu đồ
        chart_data['labels'] = [entry['period'].strftime('%Y-%m') if period == 'monthly' else get_quarter_label(entry['period']) if period == 'quarterly' else str(entry['period']) for entry in bills]
        chart_data['values'] = [entry['total_spent'] for entry in bills]
        # Truy vấn cho kỳ hiện tại và kỳ trước
        current_spent = ElectricityBill.objects.filter(user=request.user, payment_date__range=[current_period_start, current_date]).aggregate(total_spent=Sum(F('unit_price') * F('consumption') + F('water_price') * F('water_consumption')))['total_spent'] or 0
        previous_spent = ElectricityBill.objects.filter(user=request.user, payment_date__range=[previous_period_start, current_period_start - relativedelta(days=1)]).aggregate(total_spent=Sum(F('unit_price') * F('consumption') + F('water_price') * F('water_consumption')))['total_spent'] or 0
        # Tính toán thông tin so sánh
        comparison_info = {
            'current_spent': current_spent,
            'previous_spent': previous_spent,
            'difference': current_spent - previous_spent
        }

    return render(request, 'thongke.html', {'form': form, 'chart_data': chart_data, 'comparison_info': comparison_info})

@login_required(login_url='login')

def delete_bill(request, bill_id):
    bill = get_object_or_404(ElectricityBill, pk=bill_id)
    
    if request.method == 'POST':
        # Kiểm tra quyền xóa hóa đơn
        if request.user.is_superuser or request.user.bill_permissions.can_delete:
            bill.delete()
            return HttpResponse(status=200)  # Trả về mã 200 để biểu thị xóa thành công
        else:
            return HttpResponseForbidden("Bạn không có quyền xóa hóa đơn này.")  # Trả về mã 403 nếu không có quyền
    else:
        return HttpResponseNotAllowed(['POST'])  # Trả về mã 405 nếu không phải là phương thức POST
@login_required(login_url='login')   
def edit_bill_view(request, bill_id):
    bill = get_object_or_404(ElectricityBill, id=bill_id)
    
    # Kiểm tra quyền chỉnh sửa hóa đơn
    if not request.user.is_superuser and not request.user.bill_permissions.can_change:
        raise PermissionDenied("Bạn không có quyền chỉnh sửa hóa đơn này.")
    
    if request.method == 'POST':
        form = BillForm(request.POST, instance=bill)
        if form.is_valid():
            form.save()
            return redirect('search')
    else:
        form = BillForm(instance=bill)
    
    return render(request, 'edit_bill.html', {'form': form, 'bill': bill})



from rest_framework import viewsets
from .models import User
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

@login_required(login_url='login') 
def predict_expenses(request):
    # Lấy hóa đơn mới nhất
    latest_bill = ElectricityBill.objects.filter(user=request.user).order_by('-payment_date').last()
    if not latest_bill:
        return render(request, 'predict.html', {'error': 'No billing data available.'})

    # Tính trung bình tiêu thụ điện và nước
    avg_electricity = ElectricityBill.objects.filter(user=request.user).aggregate(
        Avg('unit_price'), 
        Avg('consumption')
    )
    avg_water = ElectricityBill.objects.filter(user=request.user).aggregate(
        Avg('water_price'), 
        Avg('water_consumption')
    )

    # Tạo mô hình hồi quy tuyến tính
    bills = ElectricityBill.objects.filter(user=request.user)
    X = np.array([bill.payment_date.timetuple().tm_yday for bill in bills])
    y_electric = np.array([bill.consumption * bill.unit_price for bill in bills])
    y_water = np.array([bill.water_consumption * bill.water_price for bill in bills])

    model_electric = LinearRegression()
    model_water = LinearRegression()
    model_electric.fit(X.reshape(-1, 1), y_electric)
    model_water.fit(X.reshape(-1, 1), y_water)

    # Dự đoán cho 5 tháng tiếp theo
    predictions = {'electricity': [], 'water': []}
    months = []
    for i in range(1, 6):
        future_date = latest_bill.payment_date + datetime.timedelta(days=30 * i)
        day_of_year = future_date.timetuple().tm_yday
        pred_electric = max(0, model_electric.predict([[day_of_year]])[0])
        pred_water = max(0, model_water.predict([[day_of_year]])[0])
        predictions['electricity'].append(pred_electric)
        predictions['water'].append(pred_water)
        months.append(f"{future_date.year}-{future_date.month:02d}")

    return render(request, 'predict.html', {
        'months': json.dumps(months),
        'predictions': {
            'electricity': json.dumps(predictions['electricity']),
            'water': json.dumps(predictions['water'])
        }
    })
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags

@login_required(login_url='login')
def export_bill(request, bill_id):
    bill = ElectricityBill.objects.get(id=bill_id, user=request.user)
    user = bill.user
    bill_details = f"""
    Người dùng: {user.full_name}
    Username: {user.username}
    Email: {user.email}
    Số điện thoại: {user.phone_number}
    Địa chỉ: {user.address}

    Mã hóa đơn: {bill.id}
    Tên hóa đơn: {bill.bill_name}
    Ngày tạo: {bill.payment_date}
    Hạn thanh toán: {bill.han_thanhtoan}
    Số lượng tiêu thụ điện: {bill.consumption} kWh, Giá điện: {bill.unit_price} đơn vị
    Số lượng tiêu thụ nước: {bill.water_consumption} m³, Giá nước: {bill.water_price} đơn vị
    Tổng tiền: {bill.total_amount} VND
    """
    
    # Create the email
    email = EmailMessage(
        subject=f'Hóa đơn tiền điện: {bill.bill_name}',
        body=bill_details,
        from_email='quanlydiennuoc28@gmail.com',
        to=[user.email],
    )
    
    # Create a text file attachment
    email.attach(f'hoa_don_{bill.bill_name}.txt', bill_details, 'text/plain')
    
    # Send the email
    email.send()
    
    response = HttpResponse("Email đã được gửi thành công.", content_type='text/plain')
    return response
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import User
def forgot_password_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        try:
            user = User.objects.get(username=username)
            send_mail(
                'Your Password',
                f'Your password is: {user.raw_password}',
                '....@gmail.com',
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'Mật khẩu đã được gửi đến email của bạn.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'Tên đăng nhập không tồn tại.')
    return render(request, 'quenpass.html')

