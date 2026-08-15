'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import {
  FaArrowRight, FaArrowLeft,
  FaCcAmex, FaCcDinersClub, FaCcDiscover, FaCcJcb, FaCcMastercard, FaCcVisa, FaCreditCard,
  FaLock, FaShieldAlt, FaCheckCircle,
  FaUser, FaEnvelope, FaPhone, FaGlobeAmericas, FaCalendarAlt, FaUsers, FaMobileAlt, FaWallet,
  FaIdCard, FaNotesMedical, FaFileUpload,
} from 'react-icons/fa';
import type { IconType } from 'react-icons';

interface BookingModalProps {
  isOpen: boolean;
  onClose: () => void;
  cruiseType: string;
  amountUsd: number;
  initialPaymentMode?: PaymentMode;
  initialBookingReference?: string;
  fixedAmountUsd?: number;
  launchedFromWhatsApp?: boolean;
  presentation?: 'modal' | 'page';
  onCheckoutStepChange?: (step: CheckoutStep) => void;
}

type PaymentMode = 'ecocash' | 'card' | 'omari';
type CardProvider = 'copyandpay' | 'cbz_direct';

type PaymentChannel = 'ecocash' | 'card' | 'omari';

interface CardPaymentState {
  cardNumber: string;
  expiry: string;
  cvv: string;
}

interface EcoCashPaymentState {
  msisdn: string;
}

interface OmariPaymentState {
  msisdn: string;
  otp: string;
}

type OmariStep = 'phone' | 'otp';

interface TravelerDetails {
  fullName: string;
  email: string;
  phone: string;
  country: string;
  specialRequests: string;
  agreeToTerms: boolean;
}

interface TravelerEntry {
  name: string;
  age: string;
  nationality: string;
  gender: string;
  idNumber: string;
  medicalDietaryRequirements: string;
  travelerType: 'adult' | 'child';
  idDocumentDataUrl: string;
  idDocumentName: string;
  idDocumentMimeType: string;
}

type CheckoutStep = 'details' | 'payment';
type CardBrand = 'visa' | 'mastercard' | 'amex' | 'discover' | 'diners' | 'jcb' | 'unknown';

const createEmptyTraveler = (): TravelerEntry => ({
  name: '',
  age: '',
  nationality: '',
  gender: '',
  idNumber: '',
  medicalDietaryRequirements: '',
  travelerType: 'adult',
  idDocumentDataUrl: '',
  idDocumentName: '',
  idDocumentMimeType: '',
});

const MAX_ID_DOCUMENT_SIZE_BYTES = 5 * 1024 * 1024;
const ALLOWED_ID_DOCUMENT_MIME_TYPES = ['image/jpeg', 'image/png', 'application/pdf'];

interface PaymentConfig {
  mode: string;
  ecocash: {
    accepted_formats: string[];
    test_msisdns: string[];
  };
  card: {
    supports_3ds: boolean;
    test_pans: string[];
    default_provider?: CardProvider;
    providers?: {
      copyandpay_enabled?: boolean;
      cbz_direct_enabled?: boolean;
    };
    copyandpay?: {
      enabled: boolean;
      base_url: string;
      brands: string;
    };
  };
}

interface OmariConfig {
  available: boolean;
  mode: string;
}

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_API_BASE ?? '';
const PENDING_3DS_REF_KEY = 'kalai_pending_3ds_reference';
const PENDING_PAYMENT_CHANNEL_KEY = 'kalai_pending_payment_channel';
const PENDING_BOOKING_REFERENCE_KEY = 'kalai_pending_booking_reference';
const RETURN_TO_WHATSAPP_KEY = 'kalai_return_to_whatsapp';
const WHATSAPP_NUMBER = '263712629336';

const getSessionItem = (key: string) => {
  if (typeof window === 'undefined') {
    return '';
  }

  try {
    return window.sessionStorage.getItem(key) ?? '';
  } catch {
    return '';
  }
};

const setSessionItem = (key: string, value: string) => {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    window.sessionStorage.setItem(key, value);
  } catch {
    // Ignore storage failures (e.g. strict privacy mode).
  }
};

const removeSessionItem = (key: string) => {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    window.sessionStorage.removeItem(key);
  } catch {
    // Ignore storage failures (e.g. strict privacy mode).
  }
};

export default function BookingModal({
  isOpen,
  onClose,
  cruiseType,
  amountUsd,
  initialPaymentMode,
  initialBookingReference,
  fixedAmountUsd,
  launchedFromWhatsApp = false,
  presentation = 'modal',
  onCheckoutStepChange,
}: BookingModalProps) {
  const [selectedDate, setSelectedDate] = useState('');
  const [numberOfPeople, setNumberOfPeople] = useState('1');
  const [paymentMode, setPaymentMode] = useState<PaymentMode>('ecocash');
  const [ecocash, setEcocash] = useState<EcoCashPaymentState>({ msisdn: '' });
  const [card, setCard] = useState<CardPaymentState>({ cardNumber: '', expiry: '', cvv: '' });
  const [cardProvider, setCardProvider] = useState<CardProvider>('copyandpay');
  const [omari, setOmari] = useState<OmariPaymentState>({ msisdn: '', otp: '' });
  const [omariStep, setOmariStep] = useState<OmariStep>('phone');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [paymentMessage, setPaymentMessage] = useState('');
  const [lastMerchantReference, setLastMerchantReference] = useState('');
  const [lastPaymentChannel, setLastPaymentChannel] = useState<PaymentChannel>('card');
  const [paymentConfig, setPaymentConfig] = useState<PaymentConfig | null>(null);
  const [omariConfig, setOmariConfig] = useState<OmariConfig | null>(null);
  const [activeBookingReference, setActiveBookingReference] = useState(initialBookingReference ?? '');
  const [canReturnToWhatsApp, setCanReturnToWhatsApp] = useState(false);
  const [checkoutStep, setCheckoutStep] = useState<CheckoutStep>('details');
  const [detailsMessage, setDetailsMessage] = useState('');
  const [auto3DSCheckedReference, setAuto3DSCheckedReference] = useState('');
  const [traveler, setTraveler] = useState<TravelerDetails>({
    fullName: '',
    email: '',
    phone: '',
    country: '',
    specialRequests: '',
    agreeToTerms: false,
  });
  const [travelers, setTravelers] = useState<TravelerEntry[]>([createEmptyTraveler()]);
  const detailsFormAnchorRef = useRef<HTMLDivElement | null>(null);
  const detailsDateInputRef = useRef<HTMLInputElement | null>(null);
  const isPagePresentation = presentation === 'page';
  const isTestMode = useMemo(() => paymentConfig?.mode === 'Test', [paymentConfig]);
  const isCopyAndPayAvailable = useMemo(() => {
    if (!paymentConfig) {
      return true;
    }
    if (typeof paymentConfig.card?.providers?.copyandpay_enabled === 'boolean') {
      return paymentConfig.card.providers.copyandpay_enabled;
    }
    return Boolean(paymentConfig.card?.copyandpay?.enabled);
  }, [paymentConfig]);
  const isCbzDirectAvailable = useMemo(() => {
    if (!paymentConfig) {
      return true;
    }
    if (typeof paymentConfig.card?.providers?.cbz_direct_enabled === 'boolean') {
      return paymentConfig.card.providers.cbz_direct_enabled;
    }
    return true;
  }, [paymentConfig]);
  const paymentModePill = useMemo(() => {
    const mode = (paymentConfig?.mode || '').toUpperCase();
    if (mode === 'LIVE') {
      return {
        label: 'CBZ Mode: LIVE',
        className: 'border-emerald-200 bg-emerald-50 text-emerald-800',
      };
    }
    if (mode === 'TEST') {
      return {
        label: 'CBZ Mode: TEST',
        className: 'border-amber-200 bg-amber-50 text-amber-800',
      };
    }
    return {
      label: 'CBZ Mode: UNKNOWN',
      className: 'border-slate-200 bg-slate-50 text-slate-700',
    };
  }, [paymentConfig?.mode]);
  const isOmariAvailable = useMemo(() => (omariConfig ? omariConfig.available : true), [omariConfig]);
  const isOmariTestMode = useMemo(() => omariConfig?.mode === 'Test', [omariConfig]);
  const omariModePill = useMemo(() => {
    const mode = (omariConfig?.mode || '').toUpperCase();
    if (mode === 'LIVE') {
      return {
        label: 'Omari Mode: LIVE',
        className: 'border-emerald-200 bg-emerald-50 text-emerald-800',
      };
    }
    if (mode === 'TEST') {
      return {
        label: 'Omari Mode: TEST',
        className: 'border-amber-200 bg-amber-50 text-amber-800',
      };
    }
    return {
      label: 'Omari Mode: UNKNOWN',
      className: 'border-slate-200 bg-slate-50 text-slate-700',
    };
  }, [omariConfig?.mode]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    onCheckoutStepChange?.(checkoutStep);
  }, [checkoutStep, isOpen, onCheckoutStepChange]);

  useEffect(() => {
    if (!isOpen || checkoutStep !== 'details') {
      return;
    }

    const id = window.setTimeout(() => {
      detailsFormAnchorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      detailsDateInputRef.current?.focus();
    }, 0);

    return () => window.clearTimeout(id);
  }, [checkoutStep, cruiseType, isOpen]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    setPaymentMode(initialPaymentMode ?? 'ecocash');
    setActiveBookingReference(initialBookingReference ?? '');
    setCanReturnToWhatsApp(launchedFromWhatsApp && Boolean(initialBookingReference));
    setCheckoutStep(initialBookingReference ? 'payment' : 'details');
    setDetailsMessage('');
    setAuto3DSCheckedReference('');
    setOmari({ msisdn: '', otp: '' });
    setOmariStep('phone');
    if (!initialBookingReference) {
      const count = Math.max(Number(numberOfPeople || '1') || 1, 1);
      setTravelers(Array.from({ length: count }, () => createEmptyTraveler()));
    }

    if (launchedFromWhatsApp) {
      setSessionItem(RETURN_TO_WHATSAPP_KEY, '1');
      if (initialBookingReference) {
        setSessionItem(PENDING_BOOKING_REFERENCE_KEY, initialBookingReference);
      }
    } else {
      removeSessionItem(RETURN_TO_WHATSAPP_KEY);
    }

    let isCancelled = false;

    const loadPaymentConfig = async () => {
      try {
        const response = await fetch(`${API_BASE}/crm-api/payments/cbz/config/`, {
          cache: 'no-store',
        });
        const result = await response.json();

        if (!isCancelled && result.success && result.config) {
          setPaymentConfig(result.config);
          if (result.config.card?.default_provider === 'cbz_direct') {
            setCardProvider('cbz_direct');
          } else if (result.config.card?.providers?.copyandpay_enabled) {
            setCardProvider('copyandpay');
          } else {
            setCardProvider('cbz_direct');
          }
          if (result.config.mode === 'Test' && result.config.ecocash.test_msisdns.length > 0) {
            setEcocash((current) => (
              current.msisdn
                ? current
                : { msisdn: result.config.ecocash.test_msisdns[0] }
            ));
          }
        }
      } catch {
        if (!isCancelled) {
          setPaymentConfig(null);
        }
      }
    };

    void loadPaymentConfig();

    const loadOmariConfig = async () => {
      try {
        const response = await fetch(`${API_BASE}/crm-api/payments/omari/config/`, {
          cache: 'no-store',
        });
        const result = await response.json();

        if (!isCancelled && result.success && result.config) {
          setOmariConfig(result.config);
        }
      } catch {
        if (!isCancelled) {
          setOmariConfig(null);
        }
      }
    };

    void loadOmariConfig();

    // Only restore a pending 3DS state when the modal is opened with an existing
    // booking reference (i.e. the user returned from ACS/bank). A fresh "Book Now"
    // click must always start at step 1 — clear any stale keys so they don't
    // silently skip the details form.
    if (initialBookingReference) {
      const pendingRef = getSessionItem(PENDING_3DS_REF_KEY);
      if (pendingRef) {
        setLastMerchantReference(pendingRef);
        setPaymentMode('card');
        setLastPaymentChannel('card');
        setPaymentMessage('3DS authentication may still be pending. Use Complete 3DS Payment to confirm final status.');
        setCheckoutStep('payment');
      }
    } else {
      removeSessionItem(PENDING_3DS_REF_KEY);
      removeSessionItem(PENDING_PAYMENT_CHANNEL_KEY);
      setLastMerchantReference('');
      setPaymentMessage('');
    }

    return () => {
      isCancelled = true;
    };
  }, [initialBookingReference, initialPaymentMode, isOpen, launchedFromWhatsApp, numberOfPeople]);

  useEffect(() => {
    if (cardProvider === 'copyandpay' && !isCopyAndPayAvailable) {
      setCardProvider(isCbzDirectAvailable ? 'cbz_direct' : 'copyandpay');
      return;
    }
    if (cardProvider === 'cbz_direct' && !isCbzDirectAvailable) {
      setCardProvider(isCopyAndPayAvailable ? 'copyandpay' : 'cbz_direct');
    }
  }, [cardProvider, isCbzDirectAvailable, isCopyAndPayAvailable]);

  const sanitizePan = (raw: string) => raw.replace(/\D/g, '');

  // Display-only grouping (1234 5678 ...) — the underlying `card.cardNumber`
  // state stays digits-only and is what actually gets sanitized/submitted.
  const formatCardNumberDisplay = (digits: string) => digits.replace(/(.{4})/g, '$1 ').trim();

  const detectCardBrand = (pan: string): CardBrand => {
    if (!pan) {
      return 'unknown';
    }

    if (/^4/.test(pan)) {
      return 'visa';
    }
    if (/^(5[1-5]|2(?:2[2-9]|[3-6][0-9]|7[01]|720))/.test(pan)) {
      return 'mastercard';
    }
    if (/^3[47]/.test(pan)) {
      return 'amex';
    }
    if (/^6(?:011|5)/.test(pan)) {
      return 'discover';
    }
    if (/^3(?:0[0-5]|[68])/.test(pan)) {
      return 'diners';
    }
    if (/^35/.test(pan)) {
      return 'jcb';
    }
    return 'unknown';
  };

  const cardBrand = useMemo(() => detectCardBrand(sanitizePan(card.cardNumber)), [card.cardNumber]);
  const cardBrandMeta = useMemo((): { label: string; icon?: IconType } => {
    if (cardBrand === 'visa') {
      return { label: 'Visa', icon: FaCcVisa };
    }
    if (cardBrand === 'mastercard') {
      return { label: 'Mastercard', icon: FaCcMastercard };
    }
    if (cardBrand === 'amex') {
      return { label: 'Amex', icon: FaCcAmex };
    }
    if (cardBrand === 'discover') {
      return { label: 'Discover', icon: FaCcDiscover };
    }
    if (cardBrand === 'diners') {
      return { label: 'Diners Club', icon: FaCcDinersClub };
    }
    if (cardBrand === 'jcb') {
      return { label: 'JCB', icon: FaCcJcb };
    }
    return { label: 'Unknown' };
  }, [cardBrand]);
  const cardBrandColorClass = useMemo(() => {
    if (cardBrand === 'visa') {
      return 'text-[#1434CB]';
    }
    if (cardBrand === 'mastercard') {
      return 'text-[#EB001B]';
    }
    if (cardBrand === 'amex') {
      return 'text-[#006FCF]';
    }
    if (cardBrand === 'discover') {
      return 'text-[#FF6000]';
    }
    if (cardBrand === 'diners') {
      return 'text-[#0079BE]';
    }
    if (cardBrand === 'jcb') {
      return 'text-[#0F4C81]';
    }
    return 'text-gray-500';
  }, [cardBrand]);
  const cardBrandVisual = useMemo<ReactNode>(() => {
    if (cardBrand === 'mastercard') {
      return (
        <span className="inline-flex items-center" aria-label="Mastercard" title="Mastercard">
          <span className="h-5 w-5 rounded-full bg-[#EB001B] opacity-95" />
          <span className="-ml-2 h-5 w-5 rounded-full bg-[#F79E1B] opacity-95" />
        </span>
      );
    }

    if (cardBrandMeta.icon) {
      return <cardBrandMeta.icon className={cardBrandColorClass} />;
    }

    return <FaCreditCard className="text-gray-500" />;
  }, [cardBrand, cardBrandColorClass, cardBrandMeta]);

  const sanitizeMsisdn = (raw: string) => raw.replace(/\D/g, '').slice(0, 12);

  const normalizeEcoCashMsisdn = (raw: string) => {
    const digits = sanitizeMsisdn(raw);
    if (digits.startsWith('263') && digits.length === 12) {
      return digits;
    }
    if (digits.startsWith('0') && digits.length === 10) {
      return `263${digits.slice(1)}`;
    }
    if (digits.length === 9 && digits.startsWith('7')) {
      return `263${digits}`;
    }
    return digits;
  };

  const isValidEcoCashMsisdn = (raw: string) => /^(2637\d{8}|07\d{8}|7\d{8})$/.test(raw.replace(/\D/g, ''));

  const toExpiryMMyy = (raw: string) => {
    const digits = raw.replace(/\D/g, '');
    if (digits.length >= 4) {
      return `${digits.slice(0, 2)}/${digits.slice(2, 4)}`;
    }
    return digits;
  };

  const toIveriExpiry = (raw: string) => raw.replace(/\D/g, '').slice(0, 4);

  const isLuhnValid = (pan: string) => {
    let sum = 0;
    let shouldDouble = false;

    for (let i = pan.length - 1; i >= 0; i -= 1) {
      let digit = Number(pan[i]);
      if (Number.isNaN(digit)) {
        return false;
      }
      if (shouldDouble) {
        digit *= 2;
        if (digit > 9) {
          digit -= 9;
        }
      }
      sum += digit;
      shouldDouble = !shouldDouble;
    }

    return sum % 10 === 0;
  };

  const isCardExpiryValid = (expiryMMyy: string) => {
    if (!/^\d{4}$/.test(expiryMMyy)) {
      return false;
    }

    const month = Number(expiryMMyy.slice(0, 2));
    const year = Number(expiryMMyy.slice(2, 4));
    if (!Number.isFinite(month) || month < 1 || month > 12) {
      return false;
    }

    const now = new Date();
    const currentYear = now.getFullYear() % 100;
    const currentMonth = now.getMonth() + 1;

    if (year < currentYear) {
      return false;
    }
    if (year === currentYear && month < currentMonth) {
      return false;
    }
    return true;
  };

  const hasExistingBooking = Boolean(initialBookingReference);

  useEffect(() => {
    if (hasExistingBooking || !isOpen) {
      return;
    }

    const count = Math.max(Number(numberOfPeople || '1') || 1, 1);
    setTravelers((current) => {
      if (current.length === count) {
        return current;
      }
      const next = [...current];
      while (next.length < count) {
        next.push(createEmptyTraveler());
      }
      return next.slice(0, count);
    });
  }, [hasExistingBooking, isOpen, numberOfPeople]);

  const totalAmount = fixedAmountUsd ?? (Number(numberOfPeople || '1') * amountUsd);

  const isValidEmail = (email: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());

  const validateBookingDetails = () => {
    if (hasExistingBooking) {
      return '';
    }
    if (!selectedDate) {
      return 'Select your preferred date.';
    }

    const people = Number(numberOfPeople || '0');
    if (!Number.isFinite(people) || people < 1) {
      return 'Enter a valid number of travelers.';
    }
    if (!traveler.fullName.trim()) {
      return 'Enter traveler full name.';
    }
    if (!isValidEmail(traveler.email)) {
      return 'Enter a valid email address.';
    }
    if (!traveler.phone.trim()) {
      return 'Enter a contact phone number.';
    }
    if (!traveler.agreeToTerms) {
      return 'Please accept the booking and payment terms to continue.';
    }

    for (let i = 0; i < travelers.length; i += 1) {
      const item = travelers[i];
      const label = `Traveler ${i + 1}`;
      const ageNum = Number(item.age || '0');

      if (!item.name.trim()) {
        return `${label}: full name is required.`;
      }
      if (!Number.isFinite(ageNum) || ageNum <= 0) {
        return `${label}: valid age is required.`;
      }
      if (!item.nationality.trim()) {
        return `${label}: nationality is required.`;
      }
      if (!item.gender.trim()) {
        return `${label}: gender is required.`;
      }
      if (!item.idNumber.trim()) {
        return `${label}: ID/Passport number is required.`;
      }
    }

    return '';
  };

  const buildBookingDetailsPayload = () => {
    if (hasExistingBooking) {
      return undefined;
    }

    return {
      tour_name: cruiseType,
      selected_date: selectedDate,
      number_of_people: Number(numberOfPeople || '1'),
      customer: {
        full_name: traveler.fullName.trim(),
        email: traveler.email.trim(),
        phone: traveler.phone.trim(),
        country: traveler.country.trim(),
        special_requests: traveler.specialRequests.trim(),
      },
      consent: {
        terms_accepted: traveler.agreeToTerms,
        accepted_at: new Date().toISOString(),
      },
      travelers: travelers.map((item) => ({
        name: item.name.trim(),
        age: Number(item.age || '0'),
        nationality: item.nationality.trim(),
        gender: item.gender.trim(),
        id_number: item.idNumber.trim(),
        medical: item.medicalDietaryRequirements.trim(),
        type: item.travelerType,
        id_document_data_url: item.idDocumentDataUrl,
        id_document_name: item.idDocumentName,
        id_document_mime_type: item.idDocumentMimeType,
      })),
    };
  };

  const handleTravelerDocumentChange = (index: number, file: File | null) => {
    if (!file) {
      setTravelers((prev) => prev.map((row, i) => (i === index
        ? {
            ...row,
            idDocumentDataUrl: '',
            idDocumentName: '',
            idDocumentMimeType: '',
          }
        : row)));
      return;
    }

    if (!ALLOWED_ID_DOCUMENT_MIME_TYPES.includes(file.type)) {
      setDetailsMessage('ID document must be a JPG, PNG, or PDF file.');
      return;
    }

    if (file.size > MAX_ID_DOCUMENT_SIZE_BYTES) {
      setDetailsMessage('ID document must be 5MB or smaller.');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = typeof reader.result === 'string' ? reader.result : '';
      if (!dataUrl) {
        setDetailsMessage('Failed to read the selected ID document.');
        return;
      }

      setDetailsMessage('');
      setTravelers((prev) => prev.map((row, i) => (i === index
        ? {
            ...row,
            idDocumentDataUrl: dataUrl,
            idDocumentName: file.name,
            idDocumentMimeType: file.type,
          }
        : row)));
    };
    reader.onerror = () => {
      setDetailsMessage('Failed to process the selected ID document.');
    };
    reader.readAsDataURL(file);
  };

  const buildReturnToWhatsAppHref = (bookingReference: string, merchantReference: string) => {
    const parts = [
      'Hi Kalai Safaris, I have completed my website card payment.',
      bookingReference ? `Booking reference: ${bookingReference}.` : '',
      merchantReference ? `Merchant reference: ${merchantReference}.` : '',
      'Please continue with my WhatsApp booking.',
    ].filter(Boolean);

    return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(parts.join(' '))}`;
  };

  const buildApprovalMessage = useCallback((merchantReference: string, gatewayMode?: string) => {
    const mode = gatewayMode || paymentConfig?.mode || '';
    if (mode === 'Test') {
      return `Sandbox approval only. iVeri is running in Test mode, so no real customer charge was made. Ref: ${merchantReference}`;
    }
    return `Payment approved. Ref: ${merchantReference}`;
  }, [paymentConfig?.mode]);

  const submit3DSChallenge = (challenge: Record<string, string>, merchantReference: string) => {
    const acsUrl = challenge.ACSURL || challenge.ACSUrl || challenge.AcsUrl || challenge.RedirectURL || challenge.RedirectUrl || challenge.AuthenticationURL || challenge.AuthenticationUrl;
    if (!acsUrl) {
      setPaymentMessage('3DS required but no challenge URL was returned. Please contact support.');
      return;
    }

    const paReq = challenge.PaReq || challenge.PAREQ || '';
    // MD is set to merchantReference so our callback route can extract it after ACS redirect
    const md = merchantReference;
    // TermUrl points to our API route handler so it can receive the ACS POST body (PaRes + MD)
    // and then redirect to the payment-status page as a GET request.
    const termUrl = `${window.location.origin}/api/3ds/callback`;

    setSessionItem(PENDING_3DS_REF_KEY, merchantReference);
    setSessionItem(PENDING_PAYMENT_CHANNEL_KEY, 'card');
    if (activeBookingReference) {
      setSessionItem(PENDING_BOOKING_REFERENCE_KEY, activeBookingReference);
    }
    if (launchedFromWhatsApp) {
      setSessionItem(RETURN_TO_WHATSAPP_KEY, '1');
    }
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

  const complete3DSPayment = useCallback(async (options?: { silent?: boolean }) => {
    const silent = Boolean(options?.silent);
    const merchantReference = lastMerchantReference || getSessionItem(PENDING_3DS_REF_KEY);
    if (!merchantReference) {
      if (!silent) {
        setPaymentMessage('No pending 3DS payment reference found.');
      }
      return;
    }

    try {
      setIsSubmitting(true);
      setPaymentMessage(silent ? 'Verifying your 3DS payment status...' : 'Checking final payment status...');

      const response = await fetch(`${API_BASE}/crm-api/payments/cbz/card/3ds/complete/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ merchant_reference: merchantReference }),
      });

      const result = await response.json();
      if (result.success && !result.pending) {
        if (result.booking_reference) {
          setActiveBookingReference(result.booking_reference);
          setSessionItem(PENDING_BOOKING_REFERENCE_KEY, result.booking_reference);
        }
        setCanReturnToWhatsApp(launchedFromWhatsApp);
        setPaymentMessage(buildApprovalMessage(result.merchant_reference, result.gateway_mode));
        removeSessionItem(PENDING_3DS_REF_KEY);
        return;
      }

      if (result.pending) {
        setCanReturnToWhatsApp(launchedFromWhatsApp);
        setPaymentMessage('Payment is still pending final confirmation from the gateway.');
        return;
      }

      setPaymentMessage(result.message || 'Payment was not approved.');
    } catch {
      setPaymentMessage('Unable to complete 3DS payment at the moment. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }, [buildApprovalMessage, lastMerchantReference, launchedFromWhatsApp]);

  useEffect(() => {
    if (!isOpen || checkoutStep !== 'payment' || paymentMode !== 'card' || cardProvider !== 'cbz_direct') {
      return;
    }

    const pendingReference = lastMerchantReference || getSessionItem(PENDING_3DS_REF_KEY);
    if (!pendingReference || pendingReference === auto3DSCheckedReference || isSubmitting) {
      return;
    }

    setAuto3DSCheckedReference(pendingReference);
    void complete3DSPayment({ silent: true });
  }, [auto3DSCheckedReference, cardProvider, checkoutStep, complete3DSPayment, isOpen, isSubmitting, lastMerchantReference, paymentMode]);

  const checkEcoCashPaymentStatus = async () => {
    const merchantReference = lastMerchantReference;
    if (!merchantReference) {
      setPaymentMessage('No pending EcoCash payment reference found.');
      return;
    }

    try {
      setIsSubmitting(true);
      setPaymentMessage('Checking EcoCash payment status...');

      const response = await fetch(`${API_BASE}/crm-api/payments/cbz/query/${merchantReference}/`, {
        cache: 'no-store',
      });
      const result = await response.json();

      if (result.success && result.is_approved) {
        setPaymentMessage(`EcoCash payment approved. Ref: ${merchantReference}`);
        return;
      }

      if (result.success && result.is_pending) {
        setPaymentMessage(result.data?.result_description || 'EcoCash payment is still pending confirmation.');
        return;
      }

      setPaymentMessage(result.data?.result_description || result.message || 'EcoCash payment was not approved.');
    } catch {
      setPaymentMessage('Unable to check EcoCash payment status right now. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitEcocashPayment = async () => {
    const msisdn = normalizeEcoCashMsisdn(ecocash.msisdn);

    if (!isValidEcoCashMsisdn(ecocash.msisdn)) {
      setPaymentMessage('Enter a valid EcoCash number in 2637XXXXXXXX or 07XXXXXXXX format.');
      return;
    }

    try {
      setIsSubmitting(true);
      setPaymentMessage('Initiating EcoCash payment...');

      const response = await fetch(`${API_BASE}/crm-api/payments/cbz/ecocash/debit/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          msisdn,
          amount: totalAmount,
          currency: 'USD',
          booking_reference: initialBookingReference,
          booking_details: buildBookingDetailsPayload(),
        }),
      });

      const result = await response.json();

      if (result.success && result.pending) {
        setLastMerchantReference(result.merchant_reference || '');
        setLastPaymentChannel('ecocash');
        if (result.merchant_reference) {
          setSessionItem(PENDING_3DS_REF_KEY, result.merchant_reference);
          setSessionItem(PENDING_PAYMENT_CHANNEL_KEY, 'ecocash');
        }
        setPaymentMessage(result.message || 'EcoCash prompt sent. Complete the approval on your phone, then check status here.');
        return;
      }

      if (result.success) {
        setLastMerchantReference(result.merchant_reference || '');
        setLastPaymentChannel('ecocash');
        setPaymentMessage(buildApprovalMessage(result.merchant_reference, result.gateway_mode));
        return;
      }

      setPaymentMessage(result.message || 'EcoCash payment failed.');
    } catch {
      setPaymentMessage('EcoCash initiation failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const buildOmariApprovalMessage = useCallback((reference: string) => {
    if (isOmariTestMode) {
      return `Sandbox approval only. Omari is running in Test mode, so no real customer charge was made. Ref: ${reference}`;
    }
    return `Omari payment approved. Ref: ${reference}`;
  }, [isOmariTestMode]);

  const submitOmariAuth = async () => {
    const msisdn = normalizeEcoCashMsisdn(omari.msisdn);

    if (!isValidEcoCashMsisdn(omari.msisdn)) {
      setPaymentMessage('Enter a valid Omari-linked mobile number in 2637XXXXXXXX or 07XXXXXXXX format.');
      return;
    }

    try {
      setIsSubmitting(true);
      setPaymentMessage('Sending your Omari OTP...');

      const response = await fetch(`${API_BASE}/crm-api/payments/omari/auth/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          msisdn,
          amount: totalAmount,
          currency: 'USD',
          channel: 'WEB',
          booking_reference: initialBookingReference,
          booking_details: buildBookingDetailsPayload(),
        }),
      });

      const result = await response.json();

      if (result.booking_reference) {
        setActiveBookingReference(result.booking_reference);
        setSessionItem(PENDING_BOOKING_REFERENCE_KEY, result.booking_reference);
      }

      if (!result.error && result.reference) {
        setLastMerchantReference(result.reference);
        setLastPaymentChannel('omari');
        setOmariStep('otp');
        setPaymentMessage(result.message || 'OTP sent. Enter the code you received by SMS to confirm your payment.');
        return;
      }

      setPaymentMessage(result.message || 'Unable to start Omari payment. Please try another payment method.');
    } catch {
      setPaymentMessage('Omari payment initiation failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitOmariOtp = async () => {
    const otp = omari.otp.trim();
    if (!otp) {
      setPaymentMessage('Enter the OTP you received to confirm your Omari payment.');
      return;
    }

    const reference = lastMerchantReference;
    if (!reference) {
      setPaymentMessage('No pending Omari payment found. Please request a new OTP.');
      setOmariStep('phone');
      return;
    }

    try {
      setIsSubmitting(true);
      setPaymentMessage('Confirming your Omari payment...');

      const response = await fetch(`${API_BASE}/crm-api/payments/omari/request/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          msisdn: normalizeEcoCashMsisdn(omari.msisdn),
          reference,
          otp,
        }),
      });

      const result = await response.json();

      if (result.booking_reference) {
        setActiveBookingReference(result.booking_reference);
        setSessionItem(PENDING_BOOKING_REFERENCE_KEY, result.booking_reference);
      }

      if (!result.error && result.responseCode === '000') {
        setCanReturnToWhatsApp(launchedFromWhatsApp);
        setPaymentMessage(buildOmariApprovalMessage(result.paymentReference || reference));
        return;
      }

      setPaymentMessage(result.message || 'Omari payment was not approved.');
    } catch {
      setPaymentMessage('Unable to confirm Omari payment. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const checkOmariPaymentStatus = async () => {
    const reference = lastMerchantReference;
    if (!reference) {
      setPaymentMessage('No pending Omari payment reference found.');
      return;
    }

    try {
      setIsSubmitting(true);
      setPaymentMessage('Checking Omari payment status...');

      const response = await fetch(`${API_BASE}/crm-api/payments/omari/query/${reference}/`, {
        cache: 'no-store',
      });
      const result = await response.json();

      if (!result.error && (result.status || '').toLowerCase() === 'success') {
        setPaymentMessage(buildOmariApprovalMessage(result.paymentReference || reference));
        return;
      }

      setPaymentMessage(result.message || 'Omari payment is still pending or was not approved.');
    } catch {
      setPaymentMessage('Unable to check Omari payment status right now. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitCardPaymentHosted = async () => {
    try {
      setIsSubmitting(true);
      setPaymentMessage('Preparing secure hosted card checkout...');

      const resultUrl = new URL(`${window.location.origin}/booking/payment-status`);
      resultUrl.searchParams.set('channel', 'card');
      resultUrl.searchParams.set('provider', 'copyandpay');
      if (launchedFromWhatsApp) {
        resultUrl.searchParams.set('source', 'whatsapp');
      }
      if (activeBookingReference) {
        resultUrl.searchParams.set('booking_reference', activeBookingReference);
      }

      const response = await fetch(`${API_BASE}/crm-api/payments/cbz/copyandpay/prepare/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount: totalAmount,
          currency: 'USD',
          booking_reference: initialBookingReference,
          booking_details: buildBookingDetailsPayload(),
          shopper_result_url: resultUrl.toString(),
        }),
      });

      const result = await response.json();
      const resolvedBookingReference = result.booking_reference || initialBookingReference || '';
      if (resolvedBookingReference) {
        setActiveBookingReference(resolvedBookingReference);
        setSessionItem(PENDING_BOOKING_REFERENCE_KEY, resolvedBookingReference);
      }

      if (result.success && result.checkout_id) {
        const merchantRef = result.merchant_reference || '';
        if (merchantRef) {
          setLastMerchantReference(merchantRef);
          setSessionItem(PENDING_3DS_REF_KEY, merchantRef);
          setSessionItem(PENDING_PAYMENT_CHANNEL_KEY, 'card');
        }

        setLastPaymentChannel('card');
        setCanReturnToWhatsApp(launchedFromWhatsApp);

        // OPPWA locks shopperResultUrl at checkout-creation time, so the
        // payment form's action must match the URL the backend actually sent
        // to OPPWA (with ?ref= already embedded) byte-for-byte — building our
        // own copy here caused "shopperResultUrl was already set and cannot
        // be overwritten" (200.300.404) at payment time.
        const finalReturnUrl = result.shopper_result_url || resultUrl.toString();

        const checkoutUrl = new URL(`${window.location.origin}/booking/card-checkout`);
        checkoutUrl.searchParams.set('checkoutId', String(result.checkout_id));
        checkoutUrl.searchParams.set('merchantRef', merchantRef);
        checkoutUrl.searchParams.set('brands', String(result.brands || 'PRIVATE_LABEL'));
        checkoutUrl.searchParams.set('widget', String(result.widget_script_url || ''));
        checkoutUrl.searchParams.set('returnUrl', finalReturnUrl);
        if (result.integrity) {
          checkoutUrl.searchParams.set('integrity', String(result.integrity));
        }

        window.location.href = checkoutUrl.toString();
        return;
      }

      setPaymentMessage(result.message || 'Payment failed.');
    } catch {
      setPaymentMessage('Payment request failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitCardPaymentDirect = async () => {
    const pan = sanitizePan(card.cardNumber);
    const expiryDate = toIveriExpiry(card.expiry);
    const cvv = card.cvv.replace(/\D/g, '');
    const brand = detectCardBrand(pan);

    if (pan.length < 13 || pan.length > 19) {
      setPaymentMessage('Enter a valid card number.');
      return;
    }
    if (!isTestMode && !isLuhnValid(pan)) {
      setPaymentMessage('Card number failed validation. Please check and try again.');
      return;
    }
    if (brand === 'unknown') {
      // Don't block — let the gateway decline unsupported cards with a clear message
    }
    if (expiryDate.length !== 4) {
      setPaymentMessage('Enter expiry date in MM/YY format.');
      return;
    }
    if (!isCardExpiryValid(expiryDate)) {
      setPaymentMessage('Card expiry date is invalid or already expired.');
      return;
    }
    if (cvv.length < 3 || cvv.length > 4) {
      setPaymentMessage('Enter a valid CVV.');
      return;
    }

    try {
      setIsSubmitting(true);
      setPaymentMessage('Initiating 3D Secure authentication...');

      // Step 1: request 3DS 2 enrollment form data from the backend
      const enrollResponse = await fetch(`${API_BASE}/crm-api/payments/cbz/card/3ds/enroll/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pan,
          expiry_date: expiryDate,
          cvv,
          amount: totalAmount,
          currency: 'USD',
          booking_reference: initialBookingReference,
          booking_details: buildBookingDetailsPayload(),
        }),
      });

      const enrollResult = await enrollResponse.json();

      if (!enrollResult.success) {
        setPaymentMessage(enrollResult.message || 'Could not initiate 3DS authentication. Please try again.');
        return;
      }

      const resolvedBookingReference = enrollResult.booking_reference || initialBookingReference || '';
      if (resolvedBookingReference) {
        setActiveBookingReference(resolvedBookingReference);
        setSessionItem(PENDING_BOOKING_REFERENCE_KEY, resolvedBookingReference);
      }
      setSessionItem(PENDING_3DS_REF_KEY, enrollResult.merchant_reference);
      setSessionItem(PENDING_PAYMENT_CHANNEL_KEY, 'card');
      if (launchedFromWhatsApp) {
        setSessionItem(RETURN_TO_WHATSAPP_KEY, '1');
      }
      setLastMerchantReference(enrollResult.merchant_reference);
      setCanReturnToWhatsApp(launchedFromWhatsApp);

      // Step 2: auto-submit the enrollment form to iVeri — browser takes over from here.
      // iVeri drives the 3DS challenge and POSTs the result back to CBZ_3DS_RETURN_URL,
      // which completes the Debit and redirects the browser to /booking/payment-status.
      setPaymentMessage('Redirecting to 3D Secure authentication...');
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = enrollResult.enrollment_url;
      form.style.display = 'none';
      Object.entries(enrollResult.fields as Record<string, string>).forEach(([key, value]) => {
        if (!value) return;
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value;
        form.appendChild(input);
      });
      document.body.appendChild(form);
      form.submit();
      return;
    } catch {
      setPaymentMessage('Payment request failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitCardPayment = async () => {
    if (cardProvider === 'copyandpay' && !isCopyAndPayAvailable) {
      setPaymentMessage('ZimSwitch is not configured at the moment. Please use CBZ Direct Card.');
      return;
    }
    if (cardProvider === 'cbz_direct' && !isCbzDirectAvailable) {
      setPaymentMessage('CBZ Direct Card is not configured at the moment. Please use ZimSwitch.');
      return;
    }

    if (cardProvider === 'cbz_direct') {
      await submitCardPaymentDirect();
      return;
    }
    await submitCardPaymentHosted();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (checkoutStep === 'details') {
      const error = validateBookingDetails();
      if (error) {
        setDetailsMessage(error);
        return;
      }
      setDetailsMessage('');
      setCheckoutStep('payment');
      return;
    }

    if (paymentMode === 'card') {
      void submitCardPayment();
      return;
    }

    if (paymentMode === 'omari') {
      if (omariStep === 'phone') {
        void submitOmariAuth();
      } else {
        void submitOmariOtp();
      }
      return;
    }

    void submitEcocashPayment();
  };

  if (!isOpen) {
    return null;
  }

  const inputBase = 'w-full rounded-xl border border-gray-200 bg-gray-50/60 px-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 transition focus:border-[#E8600A] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#E8600A]/10';
  const inputWithIcon = `${inputBase} pl-11`;
  const labelBase = 'mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.06em] text-gray-500';

  return (
    <div className={isPagePresentation ? 'w-full' : 'fixed inset-0 z-100 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in'}>
      <div className={`relative bg-white rounded-2xl shadow-2xl w-full overflow-y-auto ${isPagePresentation ? 'max-w-5xl mx-auto min-h-[70vh]' : 'max-w-md max-h-[90vh]'}`}>
        {!isPagePresentation && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 text-gray-400 hover:text-gray-600 transition"
            aria-label="Close modal"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}

        {/* Modal content */}
        <div className="p-6 md:p-8 lg:p-10">
          <div className={isPagePresentation ? 'lg:grid lg:grid-cols-[1fr_320px] lg:gap-10 lg:items-start' : ''}>
            <div className="min-w-0">
              <div className="text-center lg:text-left mb-6">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-linear-to-r from-[#E09A18] to-[#E8600A] mb-4 shadow-lg shadow-orange-200/60">
                  {checkoutStep === 'details' ? (
                    <FaUser className="w-6 h-6 text-white" />
                  ) : (
                    <FaLock className="w-6 h-6 text-white" />
                  )}
                </div>
                <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-1">
                  {checkoutStep === 'details' ? 'Your Details' : 'Secure Payment'}
                </h2>
                <p className="text-gray-500">
                  {cruiseType}
                </p>
              </div>

              {isPagePresentation && (
                <div className="mb-6 flex items-center justify-center lg:justify-start gap-2 text-xs font-semibold uppercase tracking-[0.12em]">
                  <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 text-gray-400 px-3 py-1">
                    <FaCheckCircle size={11} /> Cruise
                  </span>
                  <span className="text-gray-300"><FaArrowRight size={11} /></span>
                  <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 ${checkoutStep === 'details' ? 'bg-[#C8102E] text-white' : 'bg-gray-100 text-gray-400'}`}>
                    {checkoutStep === 'payment' && <FaCheckCircle size={11} />} Details
                  </span>
                  <span className="text-gray-300"><FaArrowRight size={11} /></span>
                  <span className={`rounded-full px-3 py-1 ${checkoutStep === 'payment' ? 'bg-[#C8102E] text-white' : 'bg-gray-100 text-gray-400'}`}>
                    Payment
                  </span>
                </div>
              )}
              {!isPagePresentation && (
                <div className="mb-6 flex items-center justify-center gap-2 text-xs font-semibold uppercase tracking-[0.12em]">
                  <span className={`rounded-full px-3 py-1 ${checkoutStep === 'details' ? 'bg-[#C8102E] text-white' : 'bg-gray-100 text-gray-600'}`}>
                    1. Your Details
                  </span>
                  <span className="text-gray-400"><FaArrowRight size={12} /></span>
                  <span className={`rounded-full px-3 py-1 ${checkoutStep === 'payment' ? 'bg-[#C8102E] text-white' : 'bg-gray-100 text-gray-600'}`}>
                    2. Payment
                  </span>
                </div>
              )}

              {isTestMode && (
                <div className="mb-5 rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                  Payments are currently running in iVeri Test mode. Any approval shown here is sandbox-only and does not charge a real customer card or wallet.
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                {checkoutStep === 'details' && (
                  <>
                    <div ref={detailsFormAnchorRef} />
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="date" className={labelBase}>
                          <FaCalendarAlt className="text-[#E8600A]" size={12} /> Preferred Date
                        </label>
                        <input
                          type="date"
                          id="date"
                          ref={detailsDateInputRef}
                          value={selectedDate}
                          onChange={(e) => setSelectedDate(e.target.value)}
                          min={new Date().toISOString().split('T')[0]}
                          className={inputBase}
                        />
                      </div>

                      <div>
                        <label htmlFor="people" className={labelBase}>
                          <FaUsers className="text-[#E8600A]" size={12} /> Number of People
                        </label>
                        <input
                          type="number"
                          id="people"
                          value={numberOfPeople}
                          onChange={(e) => setNumberOfPeople(e.target.value)}
                          min="1"
                          className={inputBase}
                        />
                      </div>
                    </div>

                    <div className="rounded-2xl border border-gray-200 p-5 space-y-4">
                      <p className="flex items-center gap-2 text-sm font-bold text-gray-800">
                        <FaUser className="text-[#E8600A]" /> Contact Details
                      </p>
                      <div className="relative">
                        <FaUser className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                        <input
                          type="text"
                          placeholder="Full name"
                          value={traveler.fullName}
                          onChange={(e) => setTraveler((prev) => ({ ...prev, fullName: e.target.value }))}
                          className={inputWithIcon}
                        />
                      </div>
                      <div className="relative">
                        <FaEnvelope className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                        <input
                          type="email"
                          placeholder="Email address"
                          value={traveler.email}
                          onChange={(e) => setTraveler((prev) => ({ ...prev, email: e.target.value }))}
                          className={inputWithIcon}
                        />
                      </div>
                      <div className="relative">
                        <FaPhone className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                        <input
                          type="text"
                          placeholder="Phone / WhatsApp number"
                          value={traveler.phone}
                          onChange={(e) => setTraveler((prev) => ({ ...prev, phone: e.target.value }))}
                          className={inputWithIcon}
                        />
                      </div>
                      <div className="relative">
                        <FaGlobeAmericas className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                        <input
                          type="text"
                          placeholder="Country (optional)"
                          value={traveler.country}
                          onChange={(e) => setTraveler((prev) => ({ ...prev, country: e.target.value }))}
                          className={inputWithIcon}
                        />
                      </div>
                      <textarea
                        placeholder="Special requests (dietary, accessibility, occasion, pickup details)"
                        value={traveler.specialRequests}
                        onChange={(e) => setTraveler((prev) => ({ ...prev, specialRequests: e.target.value }))}
                        rows={3}
                        className={inputBase}
                      />
                      <label className="flex items-start gap-2 text-sm text-gray-600 bg-gray-50 rounded-xl p-3">
                        <input
                          type="checkbox"
                          checked={traveler.agreeToTerms}
                          onChange={(e) => setTraveler((prev) => ({ ...prev, agreeToTerms: e.target.checked }))}
                          className="mt-1 accent-[#E8600A]"
                        />
                        <span>I confirm these details are accurate and I authorize secure payment processing for this booking.</span>
                      </label>
                    </div>

                    <div className="rounded-2xl border border-gray-200 p-5 space-y-3">
                      <p className="flex items-center gap-2 text-sm font-bold text-gray-800">
                        <FaIdCard className="text-[#E8600A]" /> Traveler Details
                      </p>
                      {travelers.map((item, index) => (
                        <div key={index} className="rounded-xl border border-gray-200 bg-gray-50/50 p-4 space-y-3">
                          <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.15em] text-gray-500">
                            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#E8600A]/10 text-[#E8600A]">
                              {index + 1}
                            </span>
                            Traveler {index + 1}
                          </p>
                          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                            <input
                              type="text"
                              placeholder="Full name"
                              value={item.name}
                              onChange={(e) => setTravelers((prev) => prev.map((row, i) => (i === index ? { ...row, name: e.target.value } : row)))}
                              className={inputBase}
                            />
                            <input
                              type="number"
                              placeholder="Age"
                              min="1"
                              value={item.age}
                              onChange={(e) => setTravelers((prev) => prev.map((row, i) => (i === index ? { ...row, age: e.target.value } : row)))}
                              className={inputBase}
                            />
                            <input
                              type="text"
                              placeholder="Nationality"
                              value={item.nationality}
                              onChange={(e) => setTravelers((prev) => prev.map((row, i) => (i === index ? { ...row, nationality: e.target.value } : row)))}
                              className={inputBase}
                            />
                            <input
                              type="text"
                              placeholder="Gender"
                              value={item.gender}
                              onChange={(e) => setTravelers((prev) => prev.map((row, i) => (i === index ? { ...row, gender: e.target.value } : row)))}
                              className={inputBase}
                            />
                            <input
                              type="text"
                              placeholder="ID / Passport number"
                              value={item.idNumber}
                              onChange={(e) => setTravelers((prev) => prev.map((row, i) => (i === index ? { ...row, idNumber: e.target.value } : row)))}
                              className={`${inputBase} sm:col-span-2`}
                            />
                            <select
                              value={item.travelerType}
                              onChange={(e) => setTravelers((prev) => prev.map((row, i) => (i === index ? { ...row, travelerType: e.target.value as 'adult' | 'child' } : row)))}
                              className={inputBase}
                            >
                              <option value="adult">Adult</option>
                              <option value="child">Child</option>
                            </select>
                            <div className="relative">
                              <FaNotesMedical className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={13} />
                              <input
                                type="text"
                                placeholder="Medical / Dietary requirements (optional)"
                                value={item.medicalDietaryRequirements}
                                onChange={(e) => setTravelers((prev) => prev.map((row, i) => (i === index ? { ...row, medicalDietaryRequirements: e.target.value } : row)))}
                                className={inputWithIcon}
                              />
                            </div>
                            <div className="sm:col-span-2">
                              <label className={labelBase}>
                                <FaFileUpload className="text-[#E8600A]" size={12} /> ID / Passport Document (optional, JPG/PNG/PDF, max 5MB)
                              </label>
                              <input
                                type="file"
                                accept=".jpg,.jpeg,.png,.pdf"
                                onChange={(e) => handleTravelerDocumentChange(index, e.target.files?.[0] || null)}
                                className="w-full rounded-xl border border-dashed border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-600 transition file:mr-3 file:rounded-full file:border-0 file:bg-[#FFF3E8] file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-[#E8600A] hover:border-[#E8600A]/40 focus:outline-none focus:ring-4 focus:ring-[#E8600A]/10"
                              />
                              {item.idDocumentName && (
                                <p className="mt-2 flex items-center gap-1.5 text-xs text-gray-500">
                                  <FaCheckCircle className="text-emerald-500" size={11} /> Attached: {item.idDocumentName}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {detailsMessage && (
                      <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                        {detailsMessage}
                      </div>
                    )}
                  </>
                )}

                <div className={`rounded-xl bg-linear-to-r from-[#FFF9F5] to-[#FFE0C8] border border-[#E09A18]/30 p-4 ${isPagePresentation ? 'lg:hidden' : ''}`}>
                  <p className="text-sm text-gray-700">
                    <strong className="text-gray-900">Estimated total:</strong> USD {totalAmount.toFixed(2)}
                  </p>
                </div>

                {checkoutStep === 'payment' && (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 rounded-2xl border border-gray-200 bg-gray-50/60 p-3">
                    <div className="flex items-center gap-2 text-xs text-gray-600">
                      <FaLock className="text-emerald-600 flex-shrink-0" /> 256-bit TLS encryption
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-600">
                      <FaShieldAlt className="text-emerald-600 flex-shrink-0" /> 3D Secure &amp; fraud checks
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-600">
                      <FaCheckCircle className="text-emerald-600 flex-shrink-0" /> Reconciled to your booking ref
                    </div>
                  </div>
                )}

                {checkoutStep === 'payment' && paymentMode !== 'omari' && (
                  <div className="rounded-xl border border-gray-200 bg-white p-3">
                    <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-[0.12em] ${paymentModePill.className}`}>
                      {paymentModePill.label}
                    </span>
                  </div>
                )}

                {checkoutStep === 'payment' && paymentMode === 'omari' && (
                  <div className="rounded-xl border border-gray-200 bg-white p-3">
                    <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-[0.12em] ${omariModePill.className}`}>
                      {omariModePill.label}
                    </span>
                  </div>
                )}

                {checkoutStep === 'payment' && (
                <div className={`grid gap-2 p-1.5 rounded-2xl bg-gray-100 ${isOmariAvailable ? 'grid-cols-3' : 'grid-cols-2'}`}>
                  <button
                    type="button"
                    onClick={() => setPaymentMode('ecocash')}
                    className={`flex items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-semibold transition ${
                      paymentMode === 'ecocash' ? 'bg-white shadow text-gray-900' : 'text-gray-500'
                    }`}
                  >
                    <FaMobileAlt size={14} /> EcoCash
                  </button>
                  <button
                    type="button"
                    onClick={() => setPaymentMode('card')}
                    className={`flex items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-semibold transition ${
                      paymentMode === 'card' ? 'bg-white shadow text-gray-900' : 'text-gray-500'
                    }`}
                  >
                    <FaCreditCard size={14} /> Pay by Card
                  </button>
                  {isOmariAvailable && (
                    <button
                      type="button"
                      onClick={() => setPaymentMode('omari')}
                      className={`flex items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-semibold transition ${
                        paymentMode === 'omari' ? 'bg-white shadow text-gray-900' : 'text-gray-500'
                      }`}
                    >
                      <FaWallet size={14} /> Omari
                    </button>
                  )}
                </div>
                )}

                {checkoutStep === 'payment' && paymentMode === 'ecocash' && (
                  <div className="space-y-3 rounded-2xl border border-gray-200 p-5">
                    <div>
                      <label htmlFor="ecocashNumber" className={labelBase}>
                        <FaMobileAlt className="text-[#E8600A]" size={12} /> EcoCash Number
                      </label>
                      <input
                        type="text"
                        id="ecocashNumber"
                        value={ecocash.msisdn}
                        onChange={(e) => setEcocash({ msisdn: sanitizeMsisdn(e.target.value) })}
                        inputMode="numeric"
                        placeholder="263771234567 or 0771234567"
                        className={inputBase}
                      />
                      <p className="mt-2 text-xs text-gray-500">
                        Accepted formats: {(paymentConfig?.ecocash.accepted_formats || ['2637XXXXXXXX', '07XXXXXXXX']).join(' or ')}
                      </p>
                    </div>
                    {paymentConfig?.mode === 'Test' && paymentConfig.ecocash.test_msisdns.length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-gray-500">Configured test numbers</p>
                        <div className="flex flex-wrap gap-2">
                          {paymentConfig.ecocash.test_msisdns.map((testMsisdn) => (
                            <button
                              key={testMsisdn}
                              type="button"
                              onClick={() => setEcocash({ msisdn: testMsisdn })}
                              className="rounded-full border border-[#E8600A] px-3 py-1 text-xs font-semibold text-[#E8600A] transition hover:bg-[#FFF3E8]"
                            >
                              {testMsisdn}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={checkEcoCashPaymentStatus}
                      disabled={isSubmitting || !lastMerchantReference || lastPaymentChannel !== 'ecocash'}
                      className="w-full rounded-full border border-[#E8600A] text-[#E8600A] font-semibold py-2.5 hover:bg-[#FFF3E8] transition disabled:opacity-50"
                    >
                      Check EcoCash Status
                    </button>
                    {lastMerchantReference && lastPaymentChannel === 'ecocash' && (
                      <a
                        href={`/booking/payment-status?channel=ecocash&ref=${encodeURIComponent(lastMerchantReference)}`}
                        className="block w-full rounded-full border border-gray-300 text-gray-700 text-center font-semibold py-2.5 hover:bg-gray-50 transition"
                      >
                        Open Full Status Page
                      </a>
                    )}
                  </div>
                )}

                {checkoutStep === 'payment' && paymentMode === 'omari' && (
                  <div className="space-y-3 rounded-2xl border border-gray-200 p-5">
                    {omariStep === 'phone' && (
                      <div>
                        <label htmlFor="omariNumber" className={labelBase}>
                          <FaWallet className="text-[#E8600A]" size={12} /> Omari Mobile Number
                        </label>
                        <input
                          type="text"
                          id="omariNumber"
                          value={omari.msisdn}
                          onChange={(e) => setOmari((prev) => ({ ...prev, msisdn: sanitizeMsisdn(e.target.value) }))}
                          inputMode="numeric"
                          placeholder="263771234567 or 0771234567"
                          className={inputBase}
                        />
                        <p className="mt-2 text-xs text-gray-500">
                          You&apos;ll receive an OTP by SMS to confirm this payment. Your number must be linked to an Omari account.
                        </p>
                      </div>
                    )}
                    {omariStep === 'otp' && (
                      <>
                        <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
                          OTP sent to {omari.msisdn || 'your phone'}. Enter it below to confirm payment.
                        </div>
                        <div>
                          <label htmlFor="omariOtp" className={labelBase}>
                            <FaLock className="text-[#E8600A]" size={12} /> OTP Code
                          </label>
                          <input
                            type="text"
                            id="omariOtp"
                            value={omari.otp}
                            onChange={(e) => setOmari((prev) => ({ ...prev, otp: e.target.value.replace(/\D/g, '').slice(0, 8) }))}
                            inputMode="numeric"
                            autoComplete="one-time-code"
                            placeholder="Enter the code you received"
                            className={`${inputBase} font-mono tracking-widest`}
                          />
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            setOmariStep('phone');
                            setPaymentMessage('');
                          }}
                          className="w-full rounded-full border border-gray-300 text-gray-600 font-semibold py-2.5 hover:bg-gray-50 transition"
                        >
                          Didn&apos;t get a code? Resend OTP
                        </button>
                        <button
                          type="button"
                          onClick={checkOmariPaymentStatus}
                          disabled={isSubmitting || !lastMerchantReference || lastPaymentChannel !== 'omari'}
                          className="w-full rounded-full border border-[#E8600A] text-[#E8600A] font-semibold py-2.5 hover:bg-[#FFF3E8] transition disabled:opacity-50"
                        >
                          Check Payment Status
                        </button>
                      </>
                    )}
                  </div>
                )}

                {checkoutStep === 'payment' && paymentMode === 'card' && (
                  <div className="space-y-3 rounded-2xl border border-gray-200 p-5">
                    {(isCopyAndPayAvailable || isCbzDirectAvailable) && (
                      <div className="grid grid-cols-2 gap-2 rounded-xl bg-gray-100 p-1">
                        {isCopyAndPayAvailable && (
                          <button
                            type="button"
                            onClick={() => setCardProvider('copyandpay')}
                            className={`rounded-lg py-2 text-xs font-semibold transition ${cardProvider === 'copyandpay' ? 'bg-white shadow text-gray-900' : 'text-gray-600'}`}
                          >
                            ZimSwitch (Hosted)
                          </button>
                        )}
                        {isCbzDirectAvailable && (
                          <button
                            type="button"
                            onClick={() => setCardProvider('cbz_direct')}
                            className={`rounded-lg py-2 text-xs font-semibold transition ${cardProvider === 'cbz_direct' ? 'bg-white shadow text-gray-900' : 'text-gray-600'}`}
                          >
                            CBZ Direct Card
                          </button>
                        )}
                      </div>
                    )}
                    {!isCopyAndPayAvailable && !isCbzDirectAvailable && (
                      <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                        Card payments are temporarily unavailable. Please use EcoCash or contact support.
                      </div>
                    )}
                    <div className="flex items-center justify-between gap-2 rounded-xl border border-gray-100 bg-gray-50 px-3 py-2">
                      <span className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-gray-500">
                        <FaLock size={10} className="text-emerald-600" /> Card details never stored on our servers
                      </span>
                      <span className="flex items-center gap-1.5 text-lg text-gray-300">
                        <FaCcVisa /> <FaCcMastercard /> <FaCcAmex />
                      </span>
                    </div>
                    {cardProvider === 'copyandpay' && (
                      <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
                        Card details are captured on the next hosted secure ZimSwitch page. Click <strong>Pay Securely</strong> to continue.
                      </div>
                    )}
                    {paymentConfig?.mode === 'Test' && (paymentConfig.card.test_pans ?? []).length > 0 && (
                      <div>
                        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-gray-500">Test cards (iVeri)</p>
                        <div className="flex flex-wrap gap-2">
                          {(paymentConfig.card.test_pans ?? []).map((testPan) => (
                            <button
                              key={testPan}
                              type="button"
                              onClick={() => setCard((prev) => ({ ...prev, cardNumber: testPan, expiry: '02/28', cvv: '123' }))}
                              className="rounded-full border border-[#E8600A] px-3 py-1 text-xs font-semibold text-[#E8600A] transition hover:bg-[#FFF3E8]"
                            >
                              {`${testPan.slice(0, 4)} **** **** ${testPan.slice(-4)}`}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    {cardProvider === 'cbz_direct' && (
                      <>
                        <div>
                          <label htmlFor="cardNumber" className={labelBase}>
                            <FaCreditCard className="text-[#E8600A]" size={12} /> Card Number
                          </label>
                          <div className="relative">
                            <input
                              type="text"
                              id="cardNumber"
                              value={formatCardNumberDisplay(card.cardNumber)}
                              onChange={(e) => setCard((prev) => ({ ...prev, cardNumber: e.target.value.replace(/\D/g, '').slice(0, 19) }))}
                              inputMode="numeric"
                              autoComplete="cc-number"
                              placeholder="5413 3300 8902 0020"
                              className={`${inputBase} pr-12 font-mono tracking-wider`}
                            />
                            {sanitizePan(card.cardNumber).length >= 4 && (
                              <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-2xl" aria-hidden="true">
                                {cardBrandVisual}
                              </span>
                            )}
                          </div>
                          {sanitizePan(card.cardNumber).length >= 4 && (
                            !cardBrandMeta.icon ? (
                              <p className="mt-2 text-xs font-semibold uppercase tracking-[0.15em] text-amber-700">
                                Detected card type: {cardBrandMeta.label}
                              </p>
                            ) : null
                          )}
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label htmlFor="expiry" className={labelBase}>
                              <FaCalendarAlt className="text-[#E8600A]" size={12} /> Expiry (MM/YY)
                            </label>
                            <input
                              type="text"
                              id="expiry"
                              value={card.expiry}
                              onChange={(e) => setCard((prev) => ({ ...prev, expiry: toExpiryMMyy(e.target.value) }))}
                              inputMode="numeric"
                              autoComplete="cc-exp"
                              placeholder="02/28"
                              className={`${inputBase} font-mono`}
                            />
                          </div>
                          <div>
                            <label htmlFor="cvv" className={labelBase}>
                              <FaLock className="text-[#E8600A]" size={12} /> CVV
                            </label>
                            <input
                              type="password"
                              id="cvv"
                              value={card.cvv}
                              onChange={(e) => setCard((prev) => ({ ...prev, cvv: e.target.value.replace(/\D/g, '').slice(0, 4) }))}
                              inputMode="numeric"
                              autoComplete="cc-csc"
                              placeholder="123"
                              className={`${inputBase} font-mono`}
                            />
                          </div>
                        </div>
                      </>
                    )}
                    {cardProvider === 'cbz_direct' && (lastMerchantReference || getSessionItem(PENDING_3DS_REF_KEY)) && (
                      <button
                        type="button"
                        onClick={() => void complete3DSPayment()}
                        disabled={isSubmitting}
                        className="w-full rounded-full border border-[#E8600A] text-[#E8600A] font-semibold py-2.5 hover:bg-[#FFF3E8] transition disabled:opacity-50"
                      >
                        Retry 3DS Status Check
                      </button>
                    )}
                  </div>
                )}

                {paymentMessage && (
                  <div className="rounded-xl border border-[#E09A18]/40 bg-[#FFF9F5] px-4 py-3 text-sm text-gray-700">
                    {paymentMessage}
                  </div>
                )}

                {launchedFromWhatsApp && canReturnToWhatsApp && (
                  <a
                    href={buildReturnToWhatsAppHref(activeBookingReference, lastMerchantReference)}
                    target="_blank"
                    rel="noreferrer"
                    className="block rounded-full border border-green-500 bg-green-50 px-4 py-3 text-center text-sm font-semibold text-green-700 transition hover:bg-green-100"
                  >
                    Return to WhatsApp
                  </a>
                )}

                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={onClose}
                    className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 border border-gray-300 text-gray-700 font-semibold rounded-full hover:bg-gray-50 transition"
                  >
                    {isPagePresentation && checkoutStep === 'details' && <FaArrowLeft size={12} />}
                    {isPagePresentation && checkoutStep === 'details' ? 'Back to Cruises' : 'Cancel'}
                  </button>
                  {checkoutStep === 'payment' && !hasExistingBooking && (
                    <button
                      type="button"
                      onClick={() => setCheckoutStep('details')}
                      className="flex-1 px-6 py-3 border border-[#E8600A] text-[#E8600A] font-semibold rounded-full hover:bg-[#FFF3E8] transition"
                    >
                      Back to Details
                    </button>
                  )}
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-linear-to-r from-[#E09A18] to-[#E8600A] hover:from-[#E8600A] hover:to-[#F47B1A] text-black font-bold rounded-full shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-70"
                  >
                    {checkoutStep === 'payment' && !isSubmitting && <FaLock size={13} />}
                    {isSubmitting
                      ? 'Processing...'
                      : checkoutStep === 'details'
                        ? 'Continue to Secure Payment'
                        : paymentMode === 'card'
                          ? (cardProvider === 'copyandpay'
                              ? (isTestMode ? 'Pay with ZimSwitch (Test Mode)' : 'Pay with ZimSwitch')
                              : (isTestMode ? 'Pay with CBZ Direct (Test Mode)' : 'Pay with CBZ Direct'))
                          : paymentMode === 'omari'
                            ? (omariStep === 'phone'
                                ? (isOmariTestMode ? 'Send Omari OTP (Test Mode)' : 'Send Omari OTP')
                                : (isOmariTestMode ? 'Confirm Omari Payment (Test Mode)' : 'Confirm Omari Payment'))
                            : (isTestMode ? 'Start EcoCash Payment (Test Mode)' : 'Start EcoCash Payment')}
                  </button>
                </div>
              </form>
            </div>

            {isPagePresentation && (
              <aside className="hidden lg:block mt-2">
                <div className="sticky top-6 rounded-2xl border border-gray-200 bg-gray-50/70 p-6 space-y-5">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.12em] text-gray-400 mb-1">Order Summary</p>
                    <p className="text-lg font-bold text-gray-900 leading-snug">{cruiseType}</p>
                  </div>

                  <div className="space-y-2 text-sm text-gray-600 border-t border-gray-200 pt-4">
                    {selectedDate && (
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-1.5"><FaCalendarAlt size={12} className="text-[#E8600A]" /> Date</span>
                        <span className="font-medium text-gray-800">{selectedDate}</span>
                      </div>
                    )}
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5"><FaUsers size={12} className="text-[#E8600A]" /> Travelers</span>
                      <span className="font-medium text-gray-800">{hasExistingBooking ? '—' : Math.max(Number(numberOfPeople || '1') || 1, 1)}</span>
                    </div>
                    {activeBookingReference && (
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-1.5"><FaIdCard size={12} className="text-[#E8600A]" /> Booking Ref</span>
                        <span className="font-mono text-xs font-semibold text-gray-800">{activeBookingReference}</span>
                      </div>
                    )}
                  </div>

                  <div className="border-t border-gray-200 pt-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-gray-700">Estimated total</span>
                      <span className="text-2xl font-black text-gray-900">${totalAmount.toFixed(2)}</span>
                    </div>
                    <p className="mt-1 text-xs text-gray-400">USD, excludes applicable park fees</p>
                  </div>

                  <div className="border-t border-gray-200 pt-4 space-y-2.5">
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <FaLock className="text-emerald-600 flex-shrink-0" size={12} /> 256-bit TLS encrypted checkout
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <FaShieldAlt className="text-emerald-600 flex-shrink-0" size={12} /> 3D Secure &amp; fraud monitoring
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <FaCheckCircle className="text-emerald-600 flex-shrink-0" size={12} /> PCI DSS compliant gateway
                    </div>
                  </div>
                </div>
              </aside>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
