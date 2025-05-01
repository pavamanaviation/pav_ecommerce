import React, { useEffect, useState } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import defaultImage from "../../../assets/images/product.png";
import "../CustomerViewCategory/CustomerViewCategory.css";
import { BiSolidCartAdd } from "react-icons/bi";
import PopupMessage from "../../../components/Popup/Popup";
import { Link } from "react-router-dom";


const FilteredProducts = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const filteredProducts = location.state?.filteredProducts || [];
    const { categoryName, subCategoryName } = useParams();
    const category_id = location.state?.category_id || localStorage.getItem("category_id");
    const sub_category_id = location.state?.sub_category_id || localStorage.getItem("sub_category_id");
    const customer_id = localStorage.getItem("customer_id") || null;
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
        console.log("Received Filtered Products in Component:", filteredProducts);
    }, [filteredProducts]);

    const handleViewProductDetails = (product) => {
        if (!category_id || !sub_category_id) {
            console.error("Missing category_id or sub_category_id");
            return;
        }

        // sessionStorage.setItem("category_id", category_id);
        // sessionStorage.setItem("sub_category_id", sub_category_id);

        localStorage.setItem("category_id", category_id);
        localStorage.setItem("sub_category_id", sub_category_id);

        navigate(`/product-details/${categoryName}/${subCategoryName}/${product.id}`, {
            state: { category_id, sub_category_id },
        });
    };

    const handleAddCart = async (product_id) => {
        if (!customer_id) {
            displayPopup(
                <>
                    Please <Link to="/customer-login" className="popup-link">log in</Link> to add products to cart.
                </>,
                "error"
            );
            // navigate("/customer-login");
            return;
        }

        if (!product_id) {
            console.error("Product ID is missing.");
            displayPopup("Product ID not found. Cannot add to cart.", "error");

            return;
        }

        try {
            const response = await fetch("http://127.0.0.1:8000/add-cart-product", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ customer_id, product_id, quantity: 1 }),
            });

            const data = await response.json();

            if (data.status_code === 200) {
                displayPopup("Product added to cart successfully!", "success");
            } else {
                displayPopup(data.error || "Failed to add product to cart.", "error");
            }
        } catch (error) {
            displayPopup("An unexpected error occurred while adding to cart.", error, "error");
        }
    };

    return (
        <div className="customer-dashboard container">
            <div className="customer-products-heading">Filtered Products</div>
            <div className="popup-discount">
                {showPopup && (
                    <PopupMessage
                        message={popupMessage.text}
                        type={popupMessage.type}
                        onClose={() => setShowPopup(false)}
                    />
                )}
            </div>
            {filteredProducts.length === 0 ? (
                <p>No products found within the selected price range.</p>
            ) : (
                <div className="customer-products-section">
                    {filteredProducts.length > 0 ? (
                        filteredProducts.map((product) => (
                            <div
                                key={product.product_id}
                                className="customer-product-card"
                                onClick={() => handleViewProductDetails(product)}
                            >
                                <img
                                    src={product.product_image_url}
                                    alt={product.product_name}
                                    className="customer-product-image"
                                    // onError={(e) => (e.target.src = defaultImage)}
                                />
                                <div className="customer-product-name">{product.product_name}</div>
                                <div className="customer-discount-section-price ">₹{product.final_price}.00 (incl. GST)</div>

                                <div >
                                    <div className="add-cart-section">
                                        <div className="customer-discount-section-original-price">₹{product.price}.00 (incl. GST)</div>

                                        <span
                                                className={`availability ${product.availability === "Out of Stock"
                                                    ? "out-of-stock"
                                                    : product.availability === "Very Few Products Left"
                                                        ? "few-left"
                                                        : "in-stock"
                                                    }`}
                                            >
                                                {product.availability === "Out of Stock"
                                                    ? "Out of Stock"
                                                    : product.availability === "Very Few Products Left"
                                                        ? "Very Few Products Left"
                                                        : "In Stock"}
                                            </span>

                                            {(product.availability === "Very Few Products Left" || product.availability === "In Stock") && (
                                            <BiSolidCartAdd
                                                className="add-to-cart-button"
                                                onClick={(e) => {
                                                    e.stopPropagation(); // Prevents navigation when clicking on the cart icon
                                                    handleAddCart(product.product_id);
                                                }}
                                            />
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : (
                        <p>No products available.</p>
                    )}
                </div>
            )}
        </div>
    );
};

export default FilteredProducts;
