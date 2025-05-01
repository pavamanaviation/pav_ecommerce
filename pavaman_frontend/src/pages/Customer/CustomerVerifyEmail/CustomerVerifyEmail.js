import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import "./CustomerVerifyEmail.css";

// import PopupMessage from "../../../components/Popup/Popup";


const VerifyEmail = () => {
    const { verification_link } = useParams();
    const navigate = useNavigate();
    const [showModal, setShowModal] = useState(false);
    const [modalData, setModalData] = useState({ message: '', type: '', show: false });


    useEffect(() => {
        const verifyEmail = async () => {
            try {
                const response = await axios.get(
                    `http://127.0.0.1:8000/verify-email/${verification_link}/`
                );
                if (response.data.message) {
                    setModalData({
                        message: " Your account is now verified!",
                        type: "success",
                        show: true,
                    });

                    setTimeout(() => {
                        navigate("/customer-login", {
                            state: { successMessage: "Your account is now verified. Please log in." }
                        });
                    }, 3000);
                }


            } catch (error) {
                setModalData({
                    message: error.response?.data?.error || "⚠️ Verification failed.",
                    type: "error",
                    show: true,
                });

                setTimeout(() => {
                    navigate("/customer-login");
                }, 3000);
            }
        };

        if (verification_link) {
            verifyEmail();
        }
    }, [verification_link, navigate]);

    const handleRedirectNow = () => {
        navigate("/customer-login");
    };

    return (
        <div className="verify-container">
            {modalData.show && (
                <div className="custom-modal-overlay">
                    <div className={`custom-modal ${modalData.type}`}>
                        <button onClick={handleRedirectNow} className="redirect-button">

                            Redirecting to login
                            <span className="dots-loading">
                                <span>.</span><span>.</span><span>.</span>
                            </span>
                        </button>
                        <div className="modaldata-message">
                            {modalData.type === "error" && "⚠️ "}
                            {modalData.type === "success" && "✅ "}
                            {modalData.message}
                        </div>

                    </div>
                </div>
            )}
        </div>
    );

};

export default VerifyEmail;
