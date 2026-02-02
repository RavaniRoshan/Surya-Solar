from typing import Optional, Dict, Any
import razorpay
from app.core.config import settings

class RazorpayService:
    def __init__(self):
        self.client: Optional[razorpay.Client] = None
        self._initialize_client()

    def _initialize_client(self):
        try:
            if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
                self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        except Exception as e:
            print(f"Failed to initialize Razorpay client: {e}")

    def create_order(self, amount: int, currency: str = "INR", receipt: str = None) -> Dict[str, Any]:
        if not self.client:
            raise Exception("Razorpay client not initialized. Check API keys.")
        
        data = {
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
            "payment_capture": 1
        }
        return self.client.order.create(data=data)

    def verify_payment(self, payment_id: str, order_id: str, signature: str) -> bool:
        if not self.client:
            raise Exception("Razorpay client not initialized")
            
        try:
            self.client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
            return True
        except razorpay.errors.SignatureVerificationError:
            return False

razorpay_service = RazorpayService()
