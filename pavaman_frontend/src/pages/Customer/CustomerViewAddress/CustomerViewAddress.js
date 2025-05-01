import React, { useEffect, useState } from "react";
import EditAddress from "../CustomerEditAddress/CustomerEditAddress";
import "../CustomerViewAddress/CustomerViewAddress.css";
import { BsThreeDotsVertical } from "react-icons/bs";
import PopupMessage from "../../../components/Popup/Popup";

const ViewCustomerAddress = ({ refresh, setOrderSummary, isAddOpen, onDeliverHere, onAddressSelect, onAddAddressClick }) => {
    const [addresses, setAddresses] = useState([]);
    const [editingAddress, setEditingAddress] = useState(null);
    const [selectedAddressId, setSelectedAddressId] = useState(null);
    const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
    const [showPopup, setShowPopup] = useState(false);
    const [addressToDelete, setAddressToDelete] = useState(null);
    const [menuOpenFor, setMenuOpenFor] = useState(null);
    const [showConfirmPopup, setShowConfirmPopup] = useState(false);

    const customerId = localStorage.getItem("customer_id");

    const displayPopup = (text, type = "success") => {
        setPopupMessage({ text, type });
        setShowPopup(true);

        setTimeout(() => {
            setShowPopup(false);
        }, 10000);
    };

    const fetchAddresses = async () => {
        try {
            const response = await fetch("http://127.0.0.1:8000/view-customer-address", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ customer_id: customerId }),
            });
            const data = await response.json();
            if (response.ok) {
                setAddresses(data.addresses);
            } else {
                if (data.error !== "No address found for the given customer ID.") {
                    displayPopup(data.error || "Failed to fetch addresses", "error");
                }
                setAddresses([]); // still update the addresses to an empty list
            }

        } catch (error) {
            displayPopup("Something went wrong while fetching addresses.", "error");
        }
    };

    useEffect(() => {
        if (customerId) {
            fetchAddresses();
        }
    }, [customerId, refresh]);

    const handleEditClick = (address) => {
        setEditingAddress(address);
        setMenuOpenFor(null);
    };

    const handleEditCompleted = (message) => {
        setEditingAddress(null);
        if (message) {
            displayPopup(message);
            fetchAddresses();
        }
    };

    const handleDeleteClick = (addressId) => {
        setAddressToDelete(addressId);
        setShowConfirmPopup(true);
        setMenuOpenFor(null);
    };

    const confirmDelete = async () => {
        setShowConfirmPopup(false);
        try {
            const response = await fetch("http://127.0.0.1:8000/delete-customer-address", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ address_id: addressToDelete, customer_id: customerId }),
            });
            const data = await response.json();
            if (response.ok) {
                displayPopup("Address deleted successfully", "success");
                fetchAddresses();
            } else {
                displayPopup(data.error || "Failed to delete address", "error");
            }
        } catch (error) {
            displayPopup("Something went wrong during deletion", "error");
        }
    };

    const handleAddressSelect = (id) => {
        setSelectedAddressId(id);
    };

    const handleOrderSummary = async () => {
        if (!selectedAddressId) {
            displayPopup("Please select a delivery address.", "error");
            return;
        }

        const orderIds = JSON.parse(localStorage.getItem("order_ids")) || [];
        const productIds = JSON.parse(localStorage.getItem("product_ids")) || [];

        if (!orderIds.length || !productIds.length) {
            displayPopup("Missing order or product details.", "error");
            return;
        }

        try {
            const response = await fetch("http://127.0.0.1:8000/products/order-multiple-products-summary", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    customer_id: customerId,
                    address_id: selectedAddressId,
                    order_ids: orderIds,
                    product_ids: productIds,
                }),
            });

            const data = await response.json();
            if (response.ok && data.status_code === 200) {
                const selectedAddr = addresses.find(addr => addr.address_id === selectedAddressId);
                setOrderSummary({
                    orders: data.orders,
                    shippingAddress: data.shipping_address,
                    order_id: data.order_id,
                    customer_id: customerId,
                    total_amount: data.total_amount,
                    product_name: data.product_name,
                });
                onDeliverHere();  // Scroll and collapse
                // Set selected address to parent
                if (selectedAddr) {
                    onAddressSelect(selectedAddr);
                }
            } else {
                displayPopup(data.error || "Failed to load summary.", "error");
            }
        } catch (error) {
            displayPopup("Something went wrong. Try again.", "error");
        }
    };

    return (
        <div className="address-list container">
            <h3 className="address-heading">Delivery Address</h3>
            {!isAddOpen && (

                <div className="add-address-btn-section container">

                    <button className="add-address-btn" onClick={onAddAddressClick}>Add Address</button>

                </div>

            )}
            <div className="popup-cart">
                {showPopup && (
                    <PopupMessage
                        message={popupMessage.text}
                        type={popupMessage.type}
                        onClose={() => setShowPopup(false)}
                    />
                )}
            </div>

            {showConfirmPopup && (
                <div className="confirm-popup-overlay">
                    <div className="confirm-popup">
                        <p>Are you sure you want to delete this address?</p>
                        <div className="popup-buttons">
                            <button className="cart-place-order" onClick={confirmDelete}>Yes, Delete</button>
                            <button className="cart-delete-selected" onClick={() => setShowConfirmPopup(false)}>Cancel</button>
                        </div>
                    </div>
                </div>
            )}

            {addresses.length > 0 ? (
                addresses.map((address) => (
                    <div key={address.address_id} className="address-list-item">
                        <div className="address-item">
                            <div className="address-header">
                                <input
                                    type="radio"
                                    name="deliveryAddress"
                                    className="address-radio-btn"
                                    checked={selectedAddressId === address.address_id}
                                    onChange={() => handleAddressSelect(address.address_id)}
                                />
                            </div>
                            <div className="address-details-section">

                                <label className="address-details" onClick={() => handleAddressSelect(address.address_id)}>

                                    <p><strong>{address.first_name} {address.last_name}</strong>{" "}

                                        <strong>{address.phone || address.mobile_number || address.contact_number}</strong>

                                    </p>

                                    <p>{address.street}, {address.village},{address.mandal} ,{address.district}, {address.state}-

                                        <strong>{address.pincode}</strong></p>

                                </label>

                            </div>
                            {!isAddOpen && (
                                <div className="menu-container">
                                    <BsThreeDotsVertical
                                        className="menu-icon"
                                        onClick={() =>
                                            setMenuOpenFor(menuOpenFor === address.address_id ? null : address.address_id)
                                        }
                                    />
                                    {menuOpenFor === address.address_id && (
                                        <div className="manage-edit-menu-dropdown">
                                            <button className="manage-edit-btn" onClick={() => handleEditClick(address)}>Edit</button>
                                            <button className="manage-delete-btn" onClick={() => handleDeleteClick(address.address_id)}>Delete</button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {editingAddress?.address_id === address.address_id && !isAddOpen && (
                            <EditAddress
                                address={editingAddress}
                                onEditCompleted={handleEditCompleted}
                            />
                        )}

                        {selectedAddressId === address.address_id && (
                            <button className="address-del-btn" onClick={handleOrderSummary}>
                                Deliver Here
                            </button>
                        )}
                    </div>
                ))
            ) : (
                <p>No saved addresses found.</p>
            )}
        </div>
    );
};

export default ViewCustomerAddress;