import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Navbar from '../components/Navbar';
import './Checkout.css';
import { API_ENDPOINTS } from '../config/api';

const planDetails = {
    '1-month': { title: '1 Month Journey', price: 199 },
    '3-months': { title: '3 Months Journey (Popular)', price: 499 },
    '6-months': { title: '6 Months Journey', price: 899 }
};

function Checkout() {
    const [searchParams] = useSearchParams();
    const planId = searchParams.get('plan') || '1-month';
    const plan = planDetails[planId] || planDetails['1-month'];

    const [couponCode, setCouponCode] = useState('');
    const [appliedCoupon, setAppliedCoupon] = useState(null);
    const [couponMessage, setCouponMessage] = useState({ text: '', type: '' });
    const handleApplyCoupon = async () => {
        const code = couponCode.toUpperCase().trim();
        if (!code) return;

        try {
            const response = await fetch(API_ENDPOINTS.VALIDATE_COUPON, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code })
            });
            const data = await response.json();

            if (data.success) {
                setAppliedCoupon(data.coupon);
                setCouponMessage({ text: 'Coupon applied successfully!', type: 'success' });
            } else {
                setAppliedCoupon(null);
                setCouponMessage({ text: data.error || 'Invalid coupon code.', type: 'error' });
            }
        } catch (err) {
            setCouponMessage({ text: 'Validation failed. Try again.', type: 'error' });
        }
    };

    const removeCoupon = () => {
        setAppliedCoupon(null);
        setCouponCode('');
        setCouponMessage({ text: '', type: '' });
    };

    const calculateTotal = () => {
        const basePrice = Number(plan.price);
        let discountAmount = 0;

        if (appliedCoupon) {
            const discountVal = Number(appliedCoupon.discount);
            if (appliedCoupon.type === 'flat') {
                discountAmount = discountVal;
            } else if (appliedCoupon.type === 'percent') {
                discountAmount = (basePrice * discountVal) / 100;
            }
        }

        const finalTotal = Math.max(0, Math.round(basePrice - discountAmount));
        return { total: finalTotal, discountAmount: Number(discountAmount.toFixed(2)) };
    };

    const { total, discountAmount } = calculateTotal();

    const handlePayment = (e) => {
        e.preventDefault();
        // In a real app, this would integrate with a payment gateway (Razorpay/Stripe)
        alert(`Proceeding to secure payment of ₹${total}`);
    };

    return (
        <div className="checkout-page">
            <Navbar />

            <div className="checkout-container fade-in-section animate-in">
                <div className="checkout-header">
                    <h2>Complete Your Purchase</h2>
                    <p>Secure checkout to begin your spiritual journey</p>
                </div>

                <div className="checkout-content">

                    {/* Right Side: Order Summary */}
                    <div className="checkout-summary-section">
                        <h3>Order Summary</h3>

                        <div className="summary-card">
                            <div className="summary-item main-item">
                                <span>{plan.title}</span>
                                <span>₹{plan.price}</span>
                            </div>

                            <hr className="summary-divider" />

                            <div className="coupon-section">
                                <label>Have a coupon code?</label>
                                <div className="coupon-input-group">
                                    <input
                                        type="text"
                                        placeholder="ENTER CODE"
                                        value={couponCode}
                                        onChange={(e) => setCouponCode(e.target.value)}
                                        disabled={appliedCoupon !== null}
                                        className="premium-input"
                                    />
                                    {!appliedCoupon ? (
                                        <button className="btn-apply-coupon" onClick={handleApplyCoupon}>Apply</button>
                                    ) : (
                                        <button className="btn-remove-coupon" onClick={removeCoupon}>Remove</button>
                                    )}
                                </div>
                                {couponMessage.text && (
                                    <div className={`coupon-message ${couponMessage.type}`}>
                                        {couponMessage.text}
                                    </div>
                                )}
                            </div>

                            <hr className="summary-divider" />

                            <div className="summary-item">
                                <span>Subtotal</span>
                                <span>₹{plan.price}</span>
                            </div>

                            {appliedCoupon && (
                                <div className="summary-item discount animate-fade-in">
                                    <span>
                                        Discount ({appliedCoupon.code})
                                        <small style={{ display: 'block', fontSize: '0.75rem', opacity: 0.8 }}>
                                            {appliedCoupon.type === 'percent' ? `${appliedCoupon.discount}% OFF` : `₹${appliedCoupon.discount} FLAT OFF`}
                                        </small>
                                    </span>
                                    <span>-₹{discountAmount}</span>
                                </div>
                            )}

                            <hr className="summary-divider mb-3" />

                            <div className="summary-item total">
                                <span>Total to Pay</span>
                                <span>₹{total}</span>
                            </div>

                            <button className="btn-premium-primary btn-pay-now w-100" onClick={handlePayment}>
                                Pay ₹{total} Securely
                            </button>

                            <div className="secure-badge">
                                <span>🔒</span> 100% Secure & Encrypted Transaction
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Checkout;
