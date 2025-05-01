
import React, { useState, useRef, useEffect } from "react";
import "./CustomerManageAddAddress.css";
import PopupMessage from "../../../components/Popup/Popup";

const CustomerManageAddAddress = ({ onAddressAdded, setShowAddAddressForm }) => {
    const [formData, setFormData] = useState({
        first_name: "",
        last_name: "",
        mobile_number: "",
        alternate_mobile: "",
        pincode: "",
        locality: "",
        street: "",
        district: "",
        state: "",
        landmark: "",
        email: "",
        mandal: "",
        addressType: "home",
    });

    const [loading, setLoading] = useState(false);
    const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
    const [showPopup, setShowPopup] = useState(false);
    const formRef = useRef(null);

    // Close form on outside click
    useEffect(() => {
        const handleOutsideClick = (event) => {
            if (formRef.current && !formRef.current.contains(event.target)) {
                setShowAddAddressForm(false);
            }
        };
        document.addEventListener("mousedown", handleOutsideClick);
        return () => {
            document.removeEventListener("mousedown", handleOutsideClick);
        };
    }, [setShowAddAddressForm]);

    const displayPopup = (text, type = "success") => {
        setPopupMessage({ text, type });
        setShowPopup(true);
        setTimeout(() => setShowPopup(false), 10000);
    };

    const fetchLocationDetails = async (pincode) => {
        setLoading(true);
        try {
            const response = await fetch(`https://api.postalpincode.in/pincode/${pincode}`);
            const data = await response.json();

            if (data?.[0]?.Status === "Success" && data?.[0]?.PostOffice?.length > 0) {
                const postOfficeData = data[0].PostOffice[0];
                setFormData((prev) => ({
                    ...prev,
                    state: postOfficeData.State || "",
                    district: postOfficeData.District || "",
                    mandal: postOfficeData.Block || "",
                }));
                displayPopup("Location details fetched successfully!");
            } else {
                displayPopup("Invalid Pincode! Unable to fetch details.", "error");
            }
        } catch (error) {
            displayPopup("An error occurred while fetching location details.", "error");
            console.error("Location fetch error:", error);
        }
        setLoading(false);
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));

        if (name === "pincode" && /^[0-9]{6}$/.test(value)) {
            fetchLocationDetails(value);
        }
    };

    const handleCancel = () => {
        setShowAddAddressForm(false);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setPopupMessage("");

        const customer_id = localStorage.getItem("customer_id");
        if (!customer_id) {
            alert("Please log in to continue.");
            setLoading(false);
            return;
        }

        const requiredFields = {
            first_name: "First Name",
            last_name: "Last Name",
            mobile_number: "Mobile Number",
            email: "Email",
            pincode: "Pincode",
            locality: "Locality",
            street: "Street",
            district: "District",
            state: "State",
            mandal: "Mandal",
        };

        for (let field in requiredFields) {
            if (!formData[field]?.trim()) {
                displayPopup(`Please fill in the required field: ${requiredFields[field]}`, "error");
                setLoading(false);
                return;
            }
        }

        try {
            const response = await fetch("http://127.0.0.1:8000/add-customer-address", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ customer_id, ...formData }),
            });

            const data = await response.json();

            if (data.status_code === 200) {
                displayPopup("Address added successfully!", "success");
                setFormData({
                    first_name: "",
                    last_name: "",
                    mobile_number: "",
                    alternate_mobile: "",
                    pincode: "",
                    locality: "",
                    street: "",
                    district: "",
                    state: "",
                    landmark: "",
                    email: "",
                    mandal: "",
                    addressType: "home",
                });
                setTimeout(onAddressAdded, 3000);
            } else {
                displayPopup(data.error || "Failed to add address.", "error");
            }
        } catch (error) {
            displayPopup("An unexpected error occurred.", "error");
            console.error("API Error:", error);
        } finally {
            setLoading(false);
        }
    };

    const isSaveDisabled = loading || Object.entries(formData).some(
        ([key, val]) => ["first_name", "last_name", "mobile_number", "email", "pincode", "locality", "street", "district", "state", "mandal"].includes(key) && !val.trim()
    );

    return (
        <div className="fedit-address-backdrop">
            <div className="fedit-address" ref={formRef}>
                <h3 className="manage-form-title">ADD A NEW ADDRESS</h3>
                <div className="popup-cart">
                    {showPopup && (
                        <PopupMessage
                            message={popupMessage.text}
                            type={popupMessage.type}
                            onClose={() => setShowPopup(false)}
                        />
                    )}
                </div>
                <form onSubmit={handleSubmit} className="manage-address-form">
                    {/* First & Last Name */}
                    <div className="manage-form-row">
                        <div className="manage-input-group">
                            <label>First Name <span className="required-star">*</span></label>
                            <input type="text" name="first_name" value={formData.first_name} onChange={handleChange} placeholder="First Name" required />
                        </div>
                        <div className="manage-input-group">
                            <label>Last Name <span className="required-star">*</span></label>
                            <input type="text" name="last_name" value={formData.last_name} onChange={handleChange} placeholder="Last Name" required />
                        </div>
                    </div>

                    {/* Mobile & Alternate */}
                    <div className="manage-form-row">
                        <div className="manage-input-group">
                            <label>Mobile Number <span className="required-star">*</span></label>
                            <input type="text" name="mobile_number" placeholder="Mobile Number" value={formData.mobile_number} onChange={handleChange} pattern="\d{10}" required />
                        </div>
                        <div className="manage-input-group">
                            <label>Alternate Mobile</label>
                            <input type="text" name="alternate_mobile" placeholder="Alternate Mobile (Optional)" value={formData.alternate_mobile} onChange={handleChange} />
                        </div>
                    </div>

                    {/* Email & Pincode */}
                    <div className="manage-form-row">
                        <div className="manage-input-group">
                            <label>Email <span className="required-star">*</span></label>
                            <input type="email" name="email" placeholder="Email" value={formData.email} onChange={handleChange} required />
                        </div>
                        <div className="manage-input-group">
                            <label>Pincode <span className="required-star">*</span></label>
                            <input type="text" name="pincode" placeholder="Pincode" value={formData.pincode} onChange={handleChange} pattern="\d{6}" required />
                        </div>
                    </div>

                    {/* District & State */}
                    <div className="manage-form-row">
                        <div className="manage-input-group">
                            <label>District <span className="required-star">*</span></label>
                            <input type="text" name="district" placeholder="District" value={formData.district} onChange={handleChange} required />
                        </div>
                        <div className="manage-input-group">
                            <label>State <span className="required-star">*</span></label>
                            <input type="text" name="state" placeholder="State" value={formData.state} onChange={handleChange} required />
                        </div>
                    </div>

                    {/* Address */}
                    <label className="address-label">Address <span className="required-star">*</span></label>
                    <textarea className="manage-address-input" name="street" placeholder="Address (Street, Area, Flat No.)" value={formData.street} onChange={handleChange} required />

                    {/* Mandal */}
                    <div className="manage-input-group">
                        <label>Mandal <span className="required-star">*</span></label>
                        <input type="text" name="mandal" placeholder="Mandal" value={formData.mandal} onChange={handleChange} required />
                    </div>

                    {/* Landmark & Locality */}
                    <div className="manage-form-row">
                        <div className="manage-input-group">
                            <label>Landmark</label>
                            <input type="text" name="landmark" placeholder="Landmark (Optional)" value={formData.landmark} onChange={handleChange} />
                        </div>
                        <div className="manage-input-group">
                            <label>Locality <span className="required-star">*</span></label>
                            <input type="text" name="locality" placeholder="Locality" value={formData.locality} onChange={handleChange} required />
                        </div>
                    </div>

                    {/* Address Type */}
                    <div className="cm-manage-address-type">
                        <div className="address-space">
                            <label>Address Type</label>
                            <label className="manage-radio-button">
                                <input className="radio-btn" type="radio" name="addressType" value="home" checked={formData.addressType === "home"} onChange={handleChange} />
                                Home
                            </label>
                            <label>
                                <input className="radio-btn" type="radio" name="addressType" value="work" checked={formData.addressType === "work"} onChange={handleChange} />
                                Work&nbsp;(10AM–6PM)
                            </label>
                        </div>
                    </div>

                    {/* Buttons */}
                    <div className="cart-actions">
                        <button type="submit" className="cart-place-order" disabled={isSaveDisabled}>
                            {loading ? "Saving..." : "SAVE"}
                        </button>
                        <button type="button" className="cart-delete-selected" onClick={handleCancel}>
                            CANCEL
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CustomerManageAddAddress;

