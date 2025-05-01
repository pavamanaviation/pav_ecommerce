import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import defaultImage from "../../../assets/images/product.png";
import "../CustomerViewCart/CustomerViewCart.css"
import { RiDeleteBinLine } from "react-icons/ri";
import PopupMessage from "../../../components/Popup/Popup";
import { Link } from "react-router-dom";
import {FaShoppingCart} from "react-icons/fa";

const CustomerViewCart = () => {
    const navigate = useNavigate();
    const [cartItems, setCartItems] = useState([]);
    const [totalPrice, setTotalPrice] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [selectedProducts, setSelectedProducts] = useState([]);
    const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
    const [showPopup, setShowPopup] = useState(false);

    useEffect(() => {
        fetchCartData();
    }, []);

    useEffect(() => {
        fetchCartData();

        const handleSearch = (e) => {
            console.log("Search event triggered with query:", e.detail);
            const query = e.detail;
            if (!query) {
              fetchCartData(); 
            } else {
              searchCart(query);
            }
          };
        
          window.addEventListener("customerCategorySearch", handleSearch);
          return () => window.removeEventListener("customerCategorySearch", handleSearch);
        }, []);
  

    const displayPopup = (text, type = "success") => {
        setPopupMessage({ text, type });
        setShowPopup(true);

        setTimeout(() => {
            setShowPopup(false);
        }, 10000);
    };


    const fetchCartData = async () => {
        const customer_id = localStorage.getItem("customer_id");

        if (!customer_id) {
            displayPopup(
                <>
                    Please <Link to="/customer-login" className="popup-link">log in</Link> to view your cart.
                </>,
                "error"
            );
            return;
        }

        try {
            const response = await fetch("http://127.0.0.1:8000/view-cart-products", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ customer_id }),
            });

            const data = await response.json();

            if (data.status_code === 200) {
                setCartItems(data.cart_items || []);
                setTotalPrice(data.total_cart_value || 0);
            } else {
                setError(data.message || "Failed to fetch cart.");
            }
        } catch (error) {
            setError("An unexpected error occurred.");
        } finally {
            setLoading(false);
        }
    };

    const searchCart = async (query) => {
        setLoading(true);
        const customer_id = localStorage.getItem("customer_id");
    
        if (!customer_id) {
            displayPopup(
                <>
                    Please <Link to="/customer-login" className="popup-link">log in</Link> to search your cart.
                </>,
                "error"
            );
            setLoading(false);
            return;
        }
    
        try {
            const response = await fetch("http://127.0.0.1:8000/customer-cart-view-search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ customer_id, product_name: query }),
            });
    
            const data = await response.json();
    
            if (data.status_code === 200) {
                setCartItems(data.cart_items || []);
                // setTotalPrice(data.cart_items?.reduce((acc, item) => acc + (item.final_price * item.quantity), 0) || 0);
                setTotalPrice(
                    data.cart_items?.reduce(
                      (acc, item) => acc + (item.discount_price * item.quantity), 
                      0
                    ) || 0
                  );
                  
                  
            } else {
                setError(data.message || "Failed to search cart.");
            }
        } catch (error) {
            setError("An unexpected error occurred during search.");
        } finally {
            setLoading(false);
        }
    };
    
    const handleDeleteCartItem = async (product_id) => {
        const customer_id = localStorage.getItem("customer_id");
        if (!customer_id) {

            displayPopup(
                <>
                    Please <Link to="/customer-login" className="popup-link">log in</Link> to manage your cart.
                </>,
                "error"
            );
            navigate("/customer-login");
            return;
        }


        try {
            const response = await fetch("http://127.0.0.1:8000/delete-cart-product", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ customer_id, product_id }),
            });

            const data = await response.json();

            if (data.status_code === 200) {
                const updatedCart = cartItems.filter(item => item.product_id !== product_id);
                setTotalPrice(calculateTotalPrice(updatedCart));
                setCartItems(updatedCart);

                // Recalculate total price from updated cart
                const newTotal = updatedCart.reduce((sum, item) => sum + item.discount_price * item.quantity, 0);
                setTotalPrice(newTotal);

                displayPopup("Product removed from cart!", "success");

                setTimeout(() => {
                    setPopupMessage("");
                }, 3000);

                window.dispatchEvent(new Event("cartUpdated"));
            }
            else {
                setError(data.error || "Failed to delete product from cart.");
            }
        } catch (error) {
            setError("An unexpected error occurred.");
        }
    };

    const calculateTotalPrice = (items) => {
        return items.reduce((sum, item) => sum + item.discount_price * item.quantity, 0);
    };


    const handleDeleteSelectedItems = async () => {
        const customer_id = localStorage.getItem("customer_id");
        if (!customer_id) {
            displayPopup(
                <>
                    Please <Link to="/customer-login" className="popup-link">log in</Link> to manage your cart.
                </>,
                "error"
            );
            navigate("/customer-login");
            return;
        }
        if (selectedProducts.length === 0) {
            displayPopup("No products selected for deletion.", "error");
            return;
        }

        try {
            const response = await fetch("http://127.0.0.1:8000/delete-selected-products-cart", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ customer_id, product_ids: selectedProducts }),
            });

            const data = await response.json();

            if (data.status_code === 200) {
                const updatedCart = cartItems.filter(item => !selectedProducts.includes(item.product_id));

                setTotalPrice(calculateTotalPrice(updatedCart));
                setCartItems(updatedCart);
                setSelectedProducts([]);
                window.dispatchEvent(new Event("cartUpdated"));
                displayPopup("Selected products removed from cart!", "success");

                setTimeout(() => {
                    setPopupMessage("");
                }, 3000);
            } else {
                setError(data.error || "Failed to delete selected products.");
                displayPopup(data.error || "Failed to delete selected products.", "error");
            }
        } catch (error) {
            setError("An unexpected error occurred.");
        }
    };

    const handleCheckboxChange = (product_id) => {
        setSelectedProducts(prevSelected =>
            prevSelected.includes(product_id)
                ? prevSelected.filter(id => id !== product_id)
                : [...prevSelected, product_id]
        );
    };

    const handlePlaceOrder = async () => {
        const customer_id = localStorage.getItem("customer_id");
        if (!customer_id) {
            displayPopup(
                <>
                    Please <Link to="/customer-login" className="popup-link">log in</Link> to place order.
                </>,
                "error"
            );
            navigate("/customer-login");
            return;
        }

        if (selectedProducts.length === 0) {
            displayPopup("Please select at least one product to place an order.", "error");
            return;
        }

        const productsToOrder = cartItems.filter(item => selectedProducts.includes(item.product_id));

        const orderData = {
            customer_id: String(customer_id),
            from_cart: true,
            products: productsToOrder.map(item => ({
                product_id: String(item.product_id),
                quantity: String(item.quantity),
            })),
        };

        try {
            const response = await fetch("http://127.0.0.1:8000/products/order-multiple-products", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(orderData),
            });

            const data = await response.json();

            if (data.status_code === 201) {
                const orderIds = data.orders.map(order => order.order_id);
                const productIds = data.orders.map(order => order.product_id);

                localStorage.setItem("order_ids", JSON.stringify(orderIds));
                localStorage.setItem("product_ids", JSON.stringify(productIds));

                navigate("/checkout-page", { state: { orderSummary: data.orders } });
            } else if (data.status_code === 400) {
                displayPopup(data.error || "Requested quantity is unavailable.", "error");
            } else {
                displayPopup(data.error || "Failed to place order.", "error");
            }
        } catch (error) {
            displayPopup("An unexpected error occurred.", "error");
        }
    };

    // const handlePlaceOrderProduct = async (product_id) => {
    //     const customer_id = localStorage.getItem("customer_id");
    //     if (!customer_id) {
    //         displayPopup(
    //             <>
    //                 Please <Link to="/customer-login" className="popup-link">log in</Link> to place order.
    //             </>,
    //             "error"
    //         );
    //         navigate("/customer-login");
    //         return;
    //     }

    //     const productToOrder = cartItems.find(item => item.product_id === product_id);

    //     if (!productToOrder) {
    //         displayPopup("Product not found in cart.","error");
    //         return;
    //     }

    //     const orderData = {
    //         customer_id: String(customer_id),
    //         products: [{
    //             product_id: String(productToOrder.product_id),
    //             quantity: String(productToOrder.quantity),
    //         }],
    //     };

    //     try {
    //         const response = await fetch("http://127.0.0.1:8000/products/order-multiple-products", {
    //             method: "POST",
    //             headers: { "Content-Type": "application/json" },
    //             body: JSON.stringify(orderData),
    //         });

    //         const data = await response.json();

    //         if (data.status_code === 201) {
    //             const orderIds = data.orders.map(order => order.order_id);
    //             const productIds = data.orders.map(order => order.product_id);

    //             localStorage.setItem("order_ids", JSON.stringify(orderIds));
    //             localStorage.setItem("product_ids", JSON.stringify(productIds));

    //             navigate("/checkout-page", { state: { orderSummary: data.orders } });
    //         } else if (data.status_code === 400) {
    //             displayPopup(data.error ||"Requested quantity is unavailable.","error");
    //         } else {
    //             displayPopup(data.error || "Failed to place order.","error");
    //         }
    //     } catch (error) {
    //         displayPopup("An unexpected error occurred.","error");
    //     }
    // };

    const handleQuantityChange = (product_id, change) => {
        setCartItems((prevItems) => {
            const updatedCart = prevItems.map((item) =>
                item.product_id === product_id
                    ? { ...item, quantity: Math.max(1, item.quantity + change) }
                    : item
            );

            setCartItems(updatedCart);
            setTotalPrice(calculateTotalPrice(updatedCart));

            return updatedCart;
        });
    };

    const calculateSelectedTotal = () => {
        const selectedItems = cartItems.filter(item => selectedProducts.includes(item.product_id));
        return selectedItems.reduce((sum, item) => sum + item.discount_price * item.quantity, 0);
    };

    return (
        <div className="cart-container container">
            <div className="popup-cart">
                {showPopup && (
                    <PopupMessage
                        message={popupMessage.text}
                        type={popupMessage.type}
                        onClose={() => setShowPopup(false)}
                    />
                )}
            </div>
            <h2 className="cart-title"><FaShoppingCart className="cart-nav-icon" />Your Shopping Cart</h2>


            {loading && <p>Loading...</p>}
            {error && <p>{error}</p>}
            {!loading && !error && cartItems.length === 0 && <p>Your cart is empty.</p>}



            <div className="cart-page">

                {!loading && !error && cartItems.length > 0 && (
                    <div className="cart-section">
                        {cartItems.map(item => (
                            <div key={item.cart_id} className="cart-item">
                                <div className="image-quantity-section">

                                    <input
                                        type="checkbox"
                                        className="cart-checkbox"
                                        checked={selectedProducts.includes(item.product_id)}
                                        onChange={() => handleCheckboxChange(item.product_id)}
                                    />

                                    <img
                                        src={item.image && item.image !== "null" && item.image !== "" ? item.image : defaultImage}
                                        alt={item.product_name}
                                        onError={(e) => (e.target.src = defaultImage)}
                                        className="cart-image"
                                    />


                                    <div className="quantity-selector">
                                        <button className="quantity-btn" onClick={() => handleQuantityChange(item.product_id, -1)} disabled={item.quantity === 1}>-</button>
                                        <span className="quantity">{item.quantity}</span>
                                        <button className="quantity-btn" onClick={() => handleQuantityChange(item.product_id, 1)}>+</button>
                                        <div className="cart-buttons">
                                            <RiDeleteBinLine className="remove" onClick={() => handleDeleteCartItem(item.product_id)} />

                                        </div>

                                    </div>
                                </div>
                                <div className="cart-details">
                                    <p className="product-name">{item.product_name}</p>
                                    <p className={`availability ${item.availability === "Out Of Stock"
                                        ? "out-of-stock"
                                        : item.availability === "Very Few Products Left"
                                            ? "few-left"
                                            : "in-stock"
                                        }`}>{item.availability}</p>
                                    <p className="discounted-price">₹ {item.discount_price} /-</p>

                                    <p className="original-price">₹ {item.price_per_item} /-</p>


                                </div>
                                <div>

                                    <p className="subtotal"><b>Subtotal: ₹ </b>{(item.discount_price * item.quantity).toFixed(2)} /-</p>
                                    {/* {!selectedProducts.includes(item.product_id) && (
                                        <button className="product-place-order" onClick={() => handlePlaceOrderProduct(item.product_id)}>
                                            Place Order
                                        </button>
                                    )} */}

                                </div>

                            </div>
                        ))}
                        {selectedProducts.length > 0 && (
                            <div className="cart-actions">
                                <button className="cart-delete-selected" onClick={handleDeleteSelectedItems} >
                                    Remove From Cart
                                </button>
                                <button className="cart-place-order" onClick={handlePlaceOrder} >
                                    Place Order
                                </button>
                            </div>
                        )}
                    </div>


                )}
                <div className="cart-price-section">

                    <div className=" cart-side-section">
                        <div>
                            <div className="cart-price-header">Price details</div>
                            <div className="cart-prices">
                                <div className="cart-price">
                                    <div className="cart-price-label">Price({cartItems.length} items)</div>
                                    <div className="cart-price-value">₹ {totalPrice} /-</div>
                                </div>
                                <div className="cart-price cart-pfee">
                                    <div className="cart-price-label">Platfrom Fee</div>
                                    <div className="cart-price-value">₹ 0.0 /-</div>
                                </div>
                                <div className="cart-price cart-dfee">
                                    <div className="cart-price-label">Delivery fee</div>
                                    <div className="cart-price-value">₹ 0.0 /-</div>
                                </div>
                                <div className="cart-price cart-total">
                                    <div className="cart-price-label">Total Price</div>
                                    <div className="cart-price-value"> ₹ {totalPrice} /-</div>

                                </div>
                            </div>
                        </div>
                    </div>


                   

                        {selectedProducts.length > 0 && (
                             <div className="cart-side-section">
                            <div>
                                <div className="cart-price-header">Total Payable</div>
                                <div className="cart-prices">

                                    <div className="cart-price cart-payable">
                                        <div className="cart-price-label"><b>Price({selectedProducts.length} items)</b></div>
                                        <div className="cart-price-value"><b>₹ {calculateSelectedTotal()} /-</b></div>
                                    </div>
                                    <div className="cart-price cart-pfee">
                                        <div className="cart-price-label">Platfrom Fee</div>
                                        <div className="cart-price-value">₹ 0.0 /-</div>
                                    </div>
                                    <div className="cart-price cart-dfee">
                                        <div className="cart-price-label">Delivery fee</div>
                                        <div className="cart-price-value">₹ 0.0 /-</div>
                                    </div>
                                    <div className="cart-price cart-total">
                                        <div className="cart-price-label">Total Price</div>
                                        <div className="cart-price-value">₹ {calculateSelectedTotal()} /-</div>
                                    </div>
                                </div>

                            </div>
                            </div>
                        )}
                    </div>
                
            </div>
        </div>
    );
};

export default CustomerViewCart;
