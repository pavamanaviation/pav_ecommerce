import React, { useEffect,useState } from "react";
import { useNavigate } from "react-router-dom";
import PopupMessage from "../../../components/Popup/Popup";

const RazorpayPayment = ({ orderSummary }) => {
    const navigate = useNavigate();
    const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
    const [showPopup, setShowPopup] = useState(false);

    const displayPopup = (text, type = "success") => {
        setPopupMessage({ text, type });
        setShowPopup(true);

        setTimeout(() => {
            setShowPopup(false);
        }, 10000);
    };

    useEffect(() => {
        if (orderSummary && orderSummary.orders?.length > 0) {
            handlePayment();
        }
        console.log(orderSummary)
    }, [orderSummary]);
    

    const handlePayment = async () => {
        const customerId = localStorage.getItem("customer_id");

        if (!customerId || !orderSummary.orders.length) {
            displayPopup("Customer ID and Order details are required.", "error");
            return;
        }

        const orderProducts = orderSummary.orders.map(order => ({
            order_id: order.order_id,
            product_id: order.product_id,
        }));

        try {
            const response = await fetch("http://65.0.183.78:8000/create-razorpay-order", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ customer_id: customerId, order_products: orderProducts }),
            });

            const orderData = await response.json();

            if (!response.ok) throw new Error(orderData.error || "Failed to create Razorpay order.");

            const options = {
                key: orderData.razorpay_key,
                amount: orderData.total_amount * 100,
                currency: "INR",
                name: "Pavaman E-commerce",
                description: `Payment for Order(s): ${orderProducts.map(o => o.order_id).join(", ")}`,
                order_id: orderData.razorpay_order_id,
                handler: async (paymentResponse) => {
                    const verifyResponse = await fetch("http://65.0.183.78:8000/razorpay-callback", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({

                            razorpay_payment_id: paymentResponse.razorpay_payment_id,
                            razorpay_order_id: paymentResponse.razorpay_order_id,
                            razorpay_signature: paymentResponse.razorpay_signature,
                            customer_id: customerId,
                            order_products: orderProducts,
                            address_id: orderSummary.shippingAddress?.address_id

                        }),
                    });

                    const verifyData = await verifyResponse.json();
                    if (verifyResponse.ok) {
                        displayPopup("Payment Successful!", "success");
                        navigate("/my-orders");
                    } else {
                        displayPopup("Payment Failed: " + verifyData.error,"error");
                    }
                },
                prefill: {
                    name: orderSummary.customer_name || "Customer",
                    email: orderSummary.customer_email || "customer@example.com",
                    contact: orderSummary.customer_mobile || "9876543210",
                },
                theme: { color: "#3399cc" },
            };

            const razorpay = new window.Razorpay(options);
            razorpay.open();
        } catch (error) {
            displayPopup("Error: " + error.message,"error");
        }
    };

    return (
        <div className="popup-cart">
        {showPopup && (
             <PopupMessage
                 message={popupMessage.text}  
                 type={popupMessage.type}
                 onClose={() => setShowPopup(false)}
             />
         )}
         </div>
    );
};

export default RazorpayPayment;
