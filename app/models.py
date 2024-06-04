from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.conf import settings
#nguoi dung
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The username must be set')
        user = self.model(username=username, **extra_fields)
        if password:
            user.raw_password = password  # Lưu mật khẩu gốc
            user.set_password(password)  # Mã hóa mật khẩu
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if password is None:
            raise ValueError('Superusers must have a password.')

        return self.create_user(username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(primary_key=True, max_length=100, unique=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/avatar.jpg')
    address = models.CharField(max_length=150)
    raw_password = models.CharField(max_length=128, blank=True, null=True)  # Thêm trường này
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # Thêm trường này

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['full_name', 'email']

    def __str__(self):
        return self.username

#hoa don

class ElectricityBill(models.Model):
    bill_name = models.CharField(max_length=100)  # Tên hóa đơn
    payment_date = models.DateField()  # Ngày tạo hóa đơn
    han_thanhtoan = models.DateField(null=True, blank=True)  # Hạn thanh toán
    consumption = models.DecimalField(max_digits=10, decimal_places=2)  # Lượng điện tiêu thụ
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # Giá điện mỗi đơn vị
    water_consumption = models.DecimalField(max_digits=10, decimal_places=2)  # Lượng nước tiêu thụ
    water_price = models.DecimalField(max_digits=10, decimal_places=2)  # Giá nước mỗi đơn vị
    info_dien = models.CharField(max_length=255, blank=True, null=True)  # Thông tin thêm về điện
    info_nuoc = models.CharField(max_length=255, blank=True, null=True)  # Thông tin thêm về nước
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Người dùng liên kết

    @property
    def total_amount(self):
        electricity_cost = self.unit_price * self.consumption
        water_cost = self.water_price * self.water_consumption
        return electricity_cost + water_cost

    @property
    def user_phone_number(self):
        return self.user.phone_number if self.user else None

    def __str__(self):
        return f"{self.bill_name} - Date: {self.payment_date}"

class UserBillPermissions(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bill_permissions')
    can_view = models.BooleanField(default=True)
    can_add = models.BooleanField(default=True)
    can_change = models.BooleanField(default=True)
    can_delete = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s bill permissions"