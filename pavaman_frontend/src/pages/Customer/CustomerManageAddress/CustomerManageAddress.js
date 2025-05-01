import React, { useState, useEffect } from "react";
import CustomerManageAddAddress from "../CustomerManageAddAddress/CustomerManageAddAddress";
import CustomerManageEditAddress from "../CustomerManageEditAddress/CustomerManageEditAddress";
import { BsThreeDotsVertical } from "react-icons/bs";
import "../CustomerManageAddress/CustomerManageAddress.css";
import PopupMessage from "../../../components/Popup/Popup";

const ManageCustomerAddress = ({ refresh }) => {
    const [addresses, setAddresses] = useState([]);
    const [selectedMenu, setSelectedMenu] = useState(null);
    const [editingAddress, setEditingAddress] = useState(null);
    const [deletingAddress, setDeletingAddress] = useState(null);
    const [showAddAddressForm, setShowAddAddressForm] = useState(false);
    const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
    const [showPopup, setShowPopup] = useState(false);
    const customerId = localStorage.getItem("customer_id");

    const displayPopup = (text, type = "success") => {
        setPopupMessage({ text, type });
        setShowPopup(true);

        setTimeout(() => {
            setShowPopup(false);
        }, 10000);
    };

    const fetchAddresses = async () => {
        if (!customerId) return;
        try {
            const response = await fetch("http://127.0.0.1:8000/view-customer-address", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ customer_id: customerId }),
            });
            const data = await response.json();
            if (response.ok) setAddresses(data.addresses);
            else console.error("Error:", data.error);
        } catch (error) {
            console.error("Fetch error:", error);
        }
    };

    useEffect(() => {
        fetchAddresses();
    }, [customerId, refresh]);

    const handleEditAddress = (address) => {
        setEditingAddress(address);
        setSelectedMenu(null);
        setShowAddAddressForm(false);
    };

    const handleEditCompleted = (message) => {
        setEditingAddress(null);
        if (message) {
            fetchAddresses();
           displayPopup(message,"success")
        }
    };

    const handleAddAddressClick = () => {
        setShowAddAddressForm(true);
        setEditingAddress(null);
    };

    const confirmDeleteAddress = async (addressId) => {
        setDeletingAddress(null);
        try {
            const response = await fetch("http://127.0.0.1:8000/delete-customer-address", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ address_id: addressId, customer_id: customerId }),
            });
            if (response.ok) {
                fetchAddresses();
                displayPopup("Your address has been deleted successfully!","success");
            } else {
                displayPopup("Error deleting address.","error");
            }
        } catch (error) {
            console.error("Delete error:", error);
            displayPopup(error || "Delete error.","error");

        }
    };

    return (
        <div className="manage-address-list">
            
            <div className="popup-cart">
                        {showPopup && (
                        <PopupMessage
                            message={popupMessage.text}  
                            type={popupMessage.type}
                            onClose={() => setShowPopup(false)}
                        />
                    )}
                    </div>
            <h2>Manage Addresses</h2>

            {!showAddAddressForm && (
                <button className="manage-add-address-btn" onClick={handleAddAddressClick}>
                    <span>+</span> ADD A NEW ADDRESS
                </button>
            )}

             {showAddAddressForm && (
                <CustomerManageAddAddress
                    onAddressAdded={() => {
                        fetchAddresses();
                        setShowAddAddressForm(false);
                        displayPopup("New address added successfully!","success");
                    }}
                    setShowAddAddressForm={setShowAddAddressForm} 
                />
            )}

            {addresses.length > 0 ? (
                addresses.map((address) => (
                    <div key={address.address_id} className="manage-address-item">
                        {editingAddress?.address_id === address.address_id ? (
                            <CustomerManageEditAddress
                                address={editingAddress}
                                onEditCompleted={handleEditCompleted}
                            />
                        ) : (
                            <>
                                <div className="manage-address-header">
                                    <span className="manage-address-type">
                                        {address.address_type?.toUpperCase() || "UNKNOWN"}
                                    </span>
                                    <div className="manage-menu-container">
                                        <BsThreeDotsVertical
                                            className="manage-menu-icon"
                                            onClick={() =>
                                                setSelectedMenu(
                                                    selectedMenu === address.address_id ? null : address.address_id
                                                )
                                            }
                                        />
                                        {selectedMenu === address.address_id && (
                                            <div className="manage-menu-dropdown">
                                                <button className="edit-btn" onClick={() => handleEditAddress(address)}>
                                                    Edit
                                                </button>
                                                <button className="delete-btn" onClick={() => setDeletingAddress(address.address_id)}>
                                                    Delete
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <p>
                                    <strong>{address.first_name} {address.last_name}</strong>{" "}
                                    <strong>{address.phone || address.mobile_number || address.contact_number}</strong>
                                </p>
                                <p>
                                    {address.street}, {address.village},{address.mandal} ,{address.district}, {address.state}{" "}
                                    <strong>{address.pincode}</strong>
                                </p>
                            </>
                        )}
                    </div>
                ))
            ) : (
                <p>No saved addresses found.</p>
            )}

            {deletingAddress && (
                <div className="popup-overlay">
                    <div className="dlt-popup-container">
                        <p className="dlt-popup-message">Are you sure you want to delete this address?</p>
                        <div className="popup-buttons">
                            <button className="popup-confirm-btn" onClick={() => confirmDeleteAddress(deletingAddress)}>
                                YES, DELETE
                            </button>
                            <button className="popup-cancel-btn" onClick={() => setDeletingAddress(null)}>
                                CANCEL
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ManageCustomerAddress;
