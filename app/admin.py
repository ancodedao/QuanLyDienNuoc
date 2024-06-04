from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User, ElectricityBill, UserBillPermissions

class UserCreationForm(forms.ModelForm):
    """Form for creating new users. Includes all the required fields,
    plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'full_name', 'email', 'phone_number', 'address', 'avatar')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    """Form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    disabled password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('username', 'password', 'full_name', 'email', 'phone_number', 'address', 'avatar', 'is_active', 'is_staff', 'is_superuser')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        return self.initial["password"]

class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    list_display = ('username', 'full_name', 'email', 'phone_number', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('full_name', 'email', 'phone_number', 'address', 'avatar')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser')}),
    )
    # Add fieldsets for adding user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'full_name', 'email', 'phone_number', 'address', 'avatar', 'password1', 'password2'),
        }),
    )
    search_fields = ('username', 'full_name', 'email')
    ordering = ('username',)
    filter_horizontal = ()

# Register the new UserAdmin
admin.site.register(User, UserAdmin)

class ElectricityBillAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return request.user.is_superuser or (hasattr(request.user, 'bill_permissions') and request.user.bill_permissions.can_add)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or (hasattr(request.user, 'bill_permissions') and request.user.bill_permissions.can_change)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or (hasattr(request.user, 'bill_permissions') and request.user.bill_permissions.can_delete)

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or (hasattr(request.user, 'bill_permissions') and request.user.bill_permissions.can_view)

admin.site.register(ElectricityBill, ElectricityBillAdmin)

class UserBillPermissionsAdmin(admin.ModelAdmin):
    list_display = ['user', 'can_view', 'can_add', 'can_change', 'can_delete']
    search_fields = ['user__username']

admin.site.register(UserBillPermissions, UserBillPermissionsAdmin)
