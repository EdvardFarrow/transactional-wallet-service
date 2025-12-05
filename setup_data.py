import os
import sys
from decouple import config
import django
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', config('DJANGO_SETTINGS_MODULE', default='config.settings'))

django.setup()

from django.contrib.auth.models import User
from core.models import Wallet

def create_data():
    print("Init data")

    # Admin
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@test.com', 'password')
        Wallet.objects.create(user=admin)
        print("Admin created: admin / password")
    else:
        print("ℹAdmin already exists")

    # Alice (Sender) 
    alice, created = User.objects.get_or_create(username='alice', email='alice@test.com')
    if created:
        alice.set_password('password123')
        alice.save()
        Wallet.objects.create(user=alice, balance=Decimal('1000.00'))
        print("Alice created (Balance: 1000.00): alice / password123")
    else:
        alice.wallet.balance = Decimal('1000.00')
        alice.wallet.save()
        print("Alice balance reset to 1000.00")

    # Bob (Receiver) 
    bob, created = User.objects.get_or_create(username='bob', email='bob@test.com')
    if created:
        bob.set_password('password123')
        bob.save()
        Wallet.objects.create(user=bob, balance=Decimal('0.00'))
        print("Bob created (Balance: 0.00): bob / password123")
    else:
        bob.wallet.balance = Decimal('0.00')
        bob.wallet.save()
        print("Bob balance reset to 0.00")

    print("\nData setup complete! You can now run tests.")

if __name__ == '__main__':
    try:
        create_data()
    except Exception as e:
        print(f"Error: {e}")