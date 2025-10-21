from django.contrib import admin

# Register your models here.
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ('username', 'role', 'qr_code', 'is_active')
	search_fields = ('username', 'role', 'qr_code')

# Register your models here.
