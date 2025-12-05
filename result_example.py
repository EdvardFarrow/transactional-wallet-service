import os
import sys
import django
import requests
import threading
import time
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Wallet

API_URL = "http://127.0.0.1:8000/api/transfer"
AUTH = ('alice', 'password123')


def get_wallet(username):
    return Wallet.objects.get(user__username=username)

def print_header(text):
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")

def show_balances(title="CURRENT BALANCES (DB STATE)"):
    print(f"\n {title}")
    
    # Refresh data from DB
    try:
        alice = get_wallet('alice')
        bob = get_wallet('bob')
        admin_user, _ = User.objects.get_or_create(username='admin')
        admin, _ = Wallet.objects.get_or_create(user_id=admin_user.id)

        print(f"{'User':<10} | {'Balance':<15}")
        print("-" * 27)
        print(f"{'Alice':<10} | {alice.balance:<15}")
        print(f"{'Bob':<10} | {bob.balance:<15}")
        print(f"{'Admin':<10} | {admin.balance:<15} (Fees)")
        print("-" * 27)
    except Exception as e:
        print(f"Error showing balances: {e}")

def reset_balances(alice_amount, bob_amount=0):
    print(f"\n Resetting balances: Alice={alice_amount}, Bob={bob_amount}, Admin=0...")
    
    admin_user, _ = User.objects.get_or_create(username='admin')
    admin_wallet, _ = Wallet.objects.get_or_create(user_id=admin_user.id)
    
    alice_user, _ = User.objects.get_or_create(username='alice')
    alice_wallet, _ = Wallet.objects.get_or_create(user_id=alice_user.id)
    
    bob_user, _ = User.objects.get_or_create(username='bob')
    bob_wallet, _ = Wallet.objects.get_or_create(user_id=bob_user.id)

    alice_wallet.balance = Decimal(str(alice_amount))
    bob_wallet.balance = Decimal(str(bob_amount))
    admin_wallet.balance = Decimal('0.00')

    alice_wallet.save()
    bob_wallet.save()
    admin_wallet.save()
    print(" Balances updated.")

# SINGLE TRANSFER

def run_single_transfer():
    print_header("MODE 1: SINGLE TRANSFER (WITH FEE)")
    
    reset_balances(5000, 0) 
    show_balances("Balances BEFORE test")

    try:
        amount_str = input("\n How much to transfer to Bob? (Enter = 2000): ") or "2000"
        amount = Decimal(amount_str)
    except ValueError:
        print(" Error: number required")
        return

    fee = Decimal('0.00')
    if amount > 1000:
        fee = amount * Decimal('0.1')
    total = amount + fee

    print(f"\n Operation Plan:")
    print(f"   Transfer Amount: {amount}")
    print(f"   Fee (10%):       {fee}")
    print(f"   Total Deduction: {total}")
    
    if input("\n Execute? [Y/n]: ").lower() == 'n': return

    try:
        response = requests.post(
            API_URL, 
            json={"to_user": "bob", "amount": str(amount)},
            auth=AUTH
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n SUCCESS! (HTTP 200). TX ID: {data.get('tx_id')}")
        else:
            print(f"\n ERROR (HTTP {response.status_code}): {response.text}")

    except Exception as e:
        print(f" Connection Error: {e}")

    show_balances("Balances AFTER test")


# RACE CONDITION

def run_race_attack():
    print_header("MODE 2: RACE CONDITION ATTACK")
    
    reset_balances(1000, 0) 
    show_balances("Balances BEFORE attack")

    print("\n STARTING ATTACK:")
    print("   Target: Alice (1000.00)")
    print("   Threads: 30")
    print("   Amount per thread: 100.00")
    print("   Expectation: 10 successes, 20 failures")
    
    if input("\n Start attack? [Y/n]: ").lower() == 'n': return

    threads = []
    
    def attack_worker(idx):
        try:
            res = requests.post(
                API_URL, 
                json={"to_user": "bob", "amount": "100.00"},
                auth=AUTH
            )
            if res.status_code == 200:
                print(f"    Thread {idx:02d}: Success!")
            elif res.status_code == 400:
                print(f"    Thread {idx:02d}: Blocked (Insufficient funds)")
            else:
                print(f"    Thread {idx:02d}: {res.status_code}")
        except:
            print(f"    Thread {idx:02d}: Network Error")

    print("\nSTARTING")
    start_time = time.time()
    
    for i in range(30):
        t = threading.Thread(target=attack_worker, args=(i+1,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
        
    print(f"FINISHED (Took: {time.time() - start_time:.2f} sec)\n")

    show_balances("Balances AFTER attack (Alice should be 0.00)")


# MAIN MENU

if __name__ == "__main__":
    if not User.objects.filter(username='alice').exists():
        print(" Error: Run 'make init' first!")
        sys.exit(1)

    while True:
        print_header("TRANSACTION SYSTEM CONTROL")
        print("1. Single Transfer (Fee Test)")
        print("2. Race Condition Attack (Stress Test)")
        print("0. Exit")
        
        choice = input("\n Select mode: ")
        
        if choice == '1':
            run_single_transfer()
        elif choice == '2':
            run_race_attack()
        elif choice == '0':
            print("Bye!")
            break
        else:
            print("Invalid choice")
        
        input("\n Press Enter to continue...")