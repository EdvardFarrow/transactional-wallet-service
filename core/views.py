from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Wallet, Transaction
from .tasks import send_transfer_notification
import logging 

logger = logging.getLogger(__name__)



class TransferView(APIView):
    def post(self, request):
        sender_user = request.user
        receiver_username = request.data.get('to_user')

        # Validation of incoming data
        try:
            amount = Decimal(request.data.get('amount'))
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (TypeError, ValueError):
            return Response({'error': 'Invalid amount'}, status=400)
        
        
        # Def from sent to self
        if sender_user.username == receiver_username:
            return Response({'error': 'Cannot transfer to self'}, status=400)


        try:
            with transaction.atomic():
                # ID wallets
                try:
                    sender_wallet_id = sender_user.wallet.id
                except Wallet.DoesNotExist:
                    return Response({'error': 'Sender has no wallet'}, status=400)
                
                
                try:
                    receiver_user = User.objects.get(username=receiver_username)
                    receiver_wallet_id = receiver_user.wallet.id
                except User.DoesNotExist:
                    return Response({'error': 'Receiver user not found'}, status=404)
                except Wallet.DoesNotExist:
                    return Response({'error': 'Receiver wallet not found'}, status=404)
                
                admin_user, _ = User.objects.get_or_create(username='admin')
                admin_wallet, _ = Wallet.objects.get_or_create(user=admin_user)
                admin_wallet_id = admin_wallet.id

                # Sorting for Deadlocks
                wallet_ids = sorted([sender_wallet_id, receiver_wallet_id, admin_wallet_id])
                
                # Block (FOR UPDATE)
                wallets_dict = {
                    w.id: w for w in Wallet.objects.select_for_update().filter(id__in=wallet_ids)
                }

                
                sender = wallets_dict[sender_wallet_id]
                receiver = wallets_dict[receiver_wallet_id]
                admin = wallets_dict[admin_wallet.id]

                # Balance check (Double Spending Check)
                if sender.balance < amount:
                    logger.warning(f"Insufficient funds: User {sender.user.username} has {sender.balance}, tried {amount}")
                    raise ValueError("Insufficient funds")

                # fee logic
                fee = Decimal('0.00')
                
                if amount > 1000:
                    fee = amount * Decimal('0.1') # 10%
                
                total_deduction = amount + fee  
                

                # Balance
                if sender.balance < total_deduction:
                    logger.warning(f"Insufficient funds: User {sender.user.username} has {sender.balance}, need {total_deduction}")
                    raise ValueError("Insufficient funds")
                
                sender.balance -= total_deduction 
                receiver.balance += amount
                
                if fee > 0:
                    admin.balance += fee

                sender.save()
                receiver.save()
                if fee > 0:
                    admin.save()

                # Create transaction
                tx = Transaction.objects.create(
                    sender=sender,
                    receiver=receiver,
                    amount=amount,
                    fee=fee
                )

                # Celery task 
                transaction.on_commit(lambda: send_transfer_notification.delay(tx.id, receiver.user.email))
                
                logger.info(f"Transfer successful: TX ID {tx.id}, Fee: {fee}")

            return Response({'status': 'success', 'tx_id': tx.id}, status=200)

        except Wallet.DoesNotExist:
            logger.error(f"Wallet not found during transfer from {sender_user}")
            return Response({'error': 'User or wallet not found'}, status=404)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            logger.exception("Critical transaction error")
            return Response({'error': 'Transaction processing failed'}, status=500)