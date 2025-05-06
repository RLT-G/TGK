from django.contrib import admin
from .models import Proxy, PhoneNumber, TelegramAccount, Channel, Comment, Order, Category


class TelegramAccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'phone_number', 'is_banned', 'created_at')
    
    def get_fields(self, request, obj=None):
        fields = [
            'username', 
            'telegram_firstname', 
            'telegram_secondname', 
            'avatar', 
            'phone_number', 
            'proxy', 
            'gender', 
            'api_id', 
            'api_hash'
        ]
        if obj:
            fields = [
                'username', 
                'telegram_firstname', 
                'telegram_secondname', 
                'avatar', 
                'phone_number', 
                'proxy', 
                'gender', 
                'current_order', 
                'api_id', 
                'api_hash', 
                'auth_code', 
                'is_connected', 
                'is_banned',
                'need_update'
            ]
        return fields
    

class ProxyAdmin(admin.ModelAdmin):
    fields = ('id', 'version', 'ip', 'host', 'port', 'user', 'password', 'date', 'date_end', 'country')


class OrderAdmin(admin.ModelAdmin):
    fields = (
        'channel_address', 
        'channel_description', 
        'channel_category', 
        'ordered_comment_posts', 
        'ordered_ad_days', 
        'completed_comment_posts', 
        'completed_ad_days', 
        'accounts_count', 
        'ordered_status'
    )
    

class PhoneNumberAdmin(admin.ModelAdmin):
    fields = ('number', 'country')


admin.site.register(Category)

admin.site.register(Channel)

admin.site.register(Comment)

admin.site.register(Proxy, ProxyAdmin)

admin.site.register(Order, OrderAdmin)

admin.site.register(PhoneNumber, PhoneNumberAdmin)

admin.site.register(TelegramAccount, TelegramAccountAdmin)
