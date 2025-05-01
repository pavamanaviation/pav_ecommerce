import React, { useState, useRef } from "react";
import AddCustomerAddress from "../CustomerAddAddress/CustomerAddAddress";
import ViewCustomerAddress from "../CustomerViewAddress/CustomerViewAddress";
import EditAddress from "../CustomerEditAddress/CustomerEditAddress";
import OrderSummary from "../CustomerOrderSummary/CustomerOrderSummary";
import RazorpayPayment from "../CustomerPayment/CustomerPayment";
import Popup from "../../../components/Popup/Popup";
import PopupMessage from "../../../components/Popup/Popup";

const CustomerCheckoutPage = () => {
    const [showAddressForm, setShowAddressForm] = useState(false);
    const [selectedAddress, setSelectedAddress] = useState(null);
    const [refreshAddresses, setRefreshAddresses] = useState(false);
    const [editingAddress, setEditingAddress] = useState(null);
    const [orderSummary, setOrderSummary] = useState(null);
    const [popupMessage, setPopupMessage] = useState("");
    const [popup, setPopup] = useState({ text: "", type: "" });
    const [isAddressConfirmed, setIsAddressConfirmed] = useState(false);
    const orderSummaryRef = useRef(null);

    const handleAddressAdded = (message) => {
        setShowAddressForm(false);
        setRefreshAddresses(prev => !prev);
        setPopupMessage(message);
    };

    const handleEditAddress = (address) => {
        setEditingAddress(address);
    };

    const handleEditCompleted = (message) => {
        setEditingAddress(null);
        setRefreshAddresses(prev => !prev);
        setPopupMessage(message);
    };

    const handleAddressSelect = (address) => {
        setSelectedAddress(address);
    };

    const handleDeliverHere = () => {
        setIsAddressConfirmed(true);
        setTimeout(() => {
            orderSummaryRef.current?.scrollIntoView({ behavior: "smooth" });
        }, 300);
    };

    return (
        <div className="checkout-page-container">
            {/* Popup messages */}
            <div className="popup-cart">
                {popup.text && (
                    <PopupMessage
                        message={popup.text}
                        type={popup.type}
                        onClose={() => setPopup({ text: "", type: "" })}
                    />
                )}
            </div>
            {popupMessage && <Popup message={popupMessage} onClose={() => setPopupMessage("")} />}

            {!isAddressConfirmed && (
                <div className="address-section">
                    <ViewCustomerAddress
                        onEditAddress={handleEditAddress}
                        refresh={refreshAddresses}
                        onAddressSelect={handleAddressSelect}
                        selectedAddress={selectedAddress}
                        onDeliverHere={handleDeliverHere}
                        setOrderSummary={setOrderSummary}
                        isAddOpen={showAddressForm}
                        onAddAddressClick={() => setShowAddressForm(true)}
                    />

                    {showAddressForm && (
                        <AddCustomerAddress onAddressAdded={handleAddressAdded} />
                    )}
                    {editingAddress && (
                        <EditAddress
                            address={editingAddress}
                            onEditCompleted={handleEditCompleted}
                        />
                    )}
                </div>
            )}

            {/* Show confirmed address with "Change" button */}
            {isAddressConfirmed && selectedAddress && (
                <div className="confirmed-address-section container">
                    <div className="address-heading">Delivery Address</div>

                    <div className="confirmed-address-box">
                        <p>
                            <strong>{selectedAddress.first_name} {selectedAddress.last_name} ({selectedAddress.mobile_number})</strong>
                        </p>
                        <p>
                            {selectedAddress.street}, {selectedAddress.landmark}, {selectedAddress.village},
                            {selectedAddress.mandal}, {selectedAddress.district}, {selectedAddress.state} - {selectedAddress.pincode}
                        </p>
                        <button className="add-address-btn" onClick={() => setIsAddressConfirmed(false)}>
                            Change
                        </button>
                    </div>
                </div>
            )}

            {/* Order Summary and Payment Section */}
            {isAddressConfirmed && orderSummary && (
                <div className="order-summary-section" ref={orderSummaryRef}>
                    <OrderSummary
                        orderSummary={orderSummary}
                        setOrderSummary={setOrderSummary}
                        setPopup={setPopup}
                    />
                    <RazorpayPayment
                        orderId={orderSummary.order_id}
                        customerId={orderSummary.customer_id}
                        totalAmount={orderSummary.total_amount}
                        productName={orderSummary.product_name}
                    />
                </div>
            )}
        </div>
    );
};

export default CustomerCheckoutPage;
