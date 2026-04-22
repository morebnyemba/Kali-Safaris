'use client';

import { useEffect, useState } from 'react';

interface BookingModalProps {
  isOpen: boolean;
  onClose: () => void;
  cruiseType: string;
  amountUsd: number;
}

type PaymentMode = 'whatsapp' | 'card';

interface CardPaymentState {
  cardNumber: string;
  expiry: string;
  cvv: string;
}

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_API_BASE ?? '';
const PENDING_3DS_REF_KEY = 'kalai_pending_3ds_reference';

export default function BookingModal({
  isOpen,
  onClose,
  cruiseType,
  amountUsd,
}: BookingModalProps) {
  const [selectedDate, setSelectedDate] = useState('');
  const [numberOfPeople, setNumberOfPeople] = useState('1');
  const [paymentMode, setPaymentMode] = useState<PaymentMode>('whatsapp');
  const [card, setCard] = useState<CardPaymentState>({ cardNumber: '', expiry: '', cvv: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [paymentMessage, setPaymentMessage] = useState('');
  const [lastMerchantReference, setLastMerchantReference] = useState('');

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const pendingRef = window.sessionStorage.getItem(PENDING_3DS_REF_KEY) ?? '';
    if (pendingRef) {
      setLastMerchantReference(pendingRef);
      setPaymentMode('card');
      setPaymentMessage('3DS authentication may still be pending. Use Complete 3DS Payment to confirm final status.');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const sanitizePan = (raw: string) => raw.replace(/\D/g, '');

  const toExpiryMMyy = (raw: string) => {
    const digits = raw.replace(/\D/g, '');
    if (digits.length >= 4) {
      return `${digits.slice(0, 2)}/${digits.slice(2, 4)}`;
    }
    return digits;
  };

  const toIveriExpiry = (raw: string) => raw.replace(/\D/g, '').slice(0, 4);

  const submit3DSChallenge = (challenge: Record<string, string>, merchantReference: string) => {
    const acsUrl = challenge.ACSURL || challenge.ACSUrl || challenge.AcsUrl || challenge.RedirectURL || challenge.RedirectUrl || challenge.AuthenticationURL || challenge.AuthenticationUrl;
    if (!acsUrl) {
      setPaymentMessage('3DS required but no challenge URL was returned. Please contact support.');
      return;
    }

    const paReq = challenge.PaReq || challenge.PAREQ || '';
    const md = challenge.MD || merchantReference;
    const termUrl = challenge.TermUrl || challenge.TermURL || `${window.location.origin}/booking/payment-status`;

    window.sessionStorage.setItem(PENDING_3DS_REF_KEY, merchantReference);
    setLastMerchantReference(merchantReference);

    const form = document.createElement('form');
    form.method = 'POST';
    form.action = acsUrl;
    form.style.display = 'none';

    const fields: Record<string, string> = {
      PaReq: paReq,
      MD: md,
      TermUrl: termUrl,
    };

    Object.entries(fields).forEach(([key, value]) => {
      if (!value) {
        return;
      }
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = key;
      input.value = value;
      form.appendChild(input);
    });

    document.body.appendChild(form);
    form.submit();
  };

  const complete3DSPayment = async () => {
    const merchantReference = lastMerchantReference || window.sessionStorage.getItem(PENDING_3DS_REF_KEY) || '';
    if (!merchantReference) {
      setPaymentMessage('No pending 3DS payment reference found.');
      return;
    }

    try {
      setIsSubmitting(true);
      setPaymentMessage('Checking final payment status...');

      const response = await fetch(`${API_BASE}/crm-api/payments/cbz/card/3ds/complete/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ merchant_reference: merchantReference }),
      });

      const result = await response.json();
      if (result.success && !result.pending) {
        setPaymentMessage(`Payment approved. Ref: ${result.merchant_reference}`);
        window.sessionStorage.removeItem(PENDING_3DS_REF_KEY);
        return;
      }

      if (result.pending) {
        setPaymentMessage('Payment is still pending final confirmation from the gateway.');
        return;
      }

      setPaymentMessage(result.message || 'Payment was not approved.');
    } catch {
      setPaymentMessage('Unable to complete 3DS payment at the moment. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitCardPayment = async () => {
    const pan = sanitizePan(card.cardNumber);
    const expiryDate = toIveriExpiry(card.expiry);
    const cvv = card.cvv.replace(/\D/g, '');

    if (pan.length < 13 || pan.length > 19) {
      setPaymentMessage('Enter a valid card number.');
      return;
    }
    if (expiryDate.length !== 4) {
      setPaymentMessage('Enter expiry date in MM/YY format.');
      return;
    }
    if (cvv.length < 3 || cvv.length > 4) {
      setPaymentMessage('Enter a valid CVV.');
      return;
    }

    try {
      setIsSubmitting(true);
      setPaymentMessage('Submitting card payment...');

      const response = await fetch(`${API_BASE}/crm-api/payments/cbz/card/debit/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pan,
          expiry_date: expiryDate,
          cvv,
          amount: Number(numberOfPeople) * amountUsd,
          currency: 'USD',
        }),
      });

      const result = await response.json();
      if (result.success && result.requires_3ds) {
        setPaymentMessage('3DS verification required. Redirecting to your bank authentication page...');
        submit3DSChallenge(result.challenge || {}, result.merchant_reference);
        return;
      }

      if (result.success && !result.pending) {
        setPaymentMessage(`Payment approved. Ref: ${result.merchant_reference}`);
        return;
      }

      if (result.pending) {
        setLastMerchantReference(result.merchant_reference || '');
        if (result.merchant_reference) {
          window.sessionStorage.setItem(PENDING_3DS_REF_KEY, result.merchant_reference);
        }
        setPaymentMessage('Payment is pending. If this was a 3DS flow, click Complete 3DS Payment after authentication.');
        return;
      }

      setPaymentMessage(result.message || 'Payment failed.');
    } catch {
      setPaymentMessage('Payment request failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (paymentMode === 'card') {
      void submitCardPayment();
      return;
    }
    
    const message = `*[Message from Kalai Safaris Website]*\n\nHi, I would like to book a ${cruiseType} for ${numberOfPeople} ${numberOfPeople === '1' ? 'person' : 'people'} on ${new Date(selectedDate).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}.`;
    
    const whatsappUrl = `https://wa.me/263712629336?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
    
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition"
          aria-label="Close modal"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Modal content */}
        <div className="p-6 md:p-8">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-r from-[#ffba5a] to-[#ff9800] mb-4">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
              Book Your Cruise
            </h2>
            <p className="text-gray-600">
              {cruiseType}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="date" className="block text-sm font-semibold text-gray-700 mb-2">
                Preferred Date
              </label>
              <input
                type="date"
                id="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#ff9800] focus:border-transparent transition"
              />
            </div>

            <div>
              <label htmlFor="people" className="block text-sm font-semibold text-gray-700 mb-2">
                Number of People
              </label>
              <input
                type="number"
                id="people"
                value={numberOfPeople}
                onChange={(e) => setNumberOfPeople(e.target.value)}
                min="1"
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#ff9800] focus:border-transparent transition"
              />
            </div>

            <div className="bg-gradient-to-r from-[#fff7ec] to-[#ffe8cc] border border-[#ffba5a]/30 rounded-lg p-4">
              <p className="text-sm text-gray-700">
                <strong className="text-gray-900">Estimated total:</strong> USD {(Number(numberOfPeople || '1') * amountUsd).toFixed(2)}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2 p-1 rounded-lg bg-gray-100">
              <button
                type="button"
                onClick={() => setPaymentMode('whatsapp')}
                className={`rounded-md py-2 text-sm font-semibold transition ${
                  paymentMode === 'whatsapp' ? 'bg-white shadow text-gray-900' : 'text-gray-600'
                }`}
              >
                WhatsApp Booking
              </button>
              <button
                type="button"
                onClick={() => setPaymentMode('card')}
                className={`rounded-md py-2 text-sm font-semibold transition ${
                  paymentMode === 'card' ? 'bg-white shadow text-gray-900' : 'text-gray-600'
                }`}
              >
                Pay by Card
              </button>
            </div>

            {paymentMode === 'card' && (
              <div className="space-y-3 rounded-lg border border-gray-200 p-4">
                <div>
                  <label htmlFor="cardNumber" className="block text-sm font-semibold text-gray-700 mb-2">
                    Card Number
                  </label>
                  <input
                    type="text"
                    id="cardNumber"
                    value={card.cardNumber}
                    onChange={(e) => setCard((prev) => ({ ...prev, cardNumber: e.target.value.replace(/\D/g, '').slice(0, 19) }))}
                    inputMode="numeric"
                    autoComplete="cc-number"
                    placeholder="5413330089020020"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#ff9800] focus:border-transparent transition"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="expiry" className="block text-sm font-semibold text-gray-700 mb-2">
                      Expiry (MM/YY)
                    </label>
                    <input
                      type="text"
                      id="expiry"
                      value={card.expiry}
                      onChange={(e) => setCard((prev) => ({ ...prev, expiry: toExpiryMMyy(e.target.value) }))}
                      inputMode="numeric"
                      autoComplete="cc-exp"
                      placeholder="02/28"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#ff9800] focus:border-transparent transition"
                    />
                  </div>
                  <div>
                    <label htmlFor="cvv" className="block text-sm font-semibold text-gray-700 mb-2">
                      CVV
                    </label>
                    <input
                      type="password"
                      id="cvv"
                      value={card.cvv}
                      onChange={(e) => setCard((prev) => ({ ...prev, cvv: e.target.value.replace(/\D/g, '').slice(0, 4) }))}
                      inputMode="numeric"
                      autoComplete="cc-csc"
                      placeholder="123"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#ff9800] focus:border-transparent transition"
                    />
                  </div>
                </div>
                <button
                  type="button"
                  onClick={complete3DSPayment}
                  disabled={isSubmitting}
                  className="w-full rounded-full border border-[#ff9800] text-[#ff9800] font-semibold py-2.5 hover:bg-[#fff2e0] transition disabled:opacity-50"
                >
                  Complete 3DS Payment
                </button>
              </div>
            )}

            {paymentMessage && (
              <div className="rounded-lg border border-[#ffba5a]/40 bg-[#fff9ef] p-3 text-sm text-gray-700">
                {paymentMessage}
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 font-semibold rounded-full hover:bg-gray-50 transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black font-bold rounded-full shadow-lg hover:shadow-xl transition-all duration-300"
              >
                {isSubmitting ? 'Processing...' : paymentMode === 'card' ? 'Pay Securely' : 'Continue to WhatsApp'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
