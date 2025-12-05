from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Wallet, Transaction

class WalletInline(admin.StackedInline):
    model = Wallet
    can_delete = False
    verbose_name_plural = 'Wallet'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (WalletInline, )
    list_display = ('username', 'email', 'get_balance', 'is_staff')

    def get_balance(self, instance):
        if hasattr(instance, 'wallet'):
            return instance.wallet.balance
        return None
    get_balance.short_description = 'Balance'

class SentTransactionsInline(admin.TabularInline):
    model = Transaction
    fk_name = 'sender'
    extra = 0
    readonly_fields = ('receiver', 'amount', 'fee', 'status', 'created_at')
    can_delete = False
    verbose_name = "Sent Transaction"

class ReceivedTransactionsInline(admin.TabularInline):
    model = Transaction
    fk_name = 'receiver'
    extra = 0
    readonly_fields = ('sender', 'amount', 'fee', 'status', 'created_at')
    can_delete = False
    verbose_name = "Received Transaction"

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__username',)
    inlines = [SentTransactionsInline, ReceivedTransactionsInline]

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'amount', 'fee', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('sender__user__username', 'receiver__user__username')
    readonly_fields = ('created_at',)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)