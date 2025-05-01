import React, { useEffect, useState } from "react";
import axios from "axios";
import defaultImage from "../../../assets/images/product.png";
import { useNavigate, useLocation } from "react-router-dom";
import Side from "./SideComponent";
import "./Products.css";
import { BiSolidCartAdd } from "react-icons/bi";
import { Link } from "react-router-dom";
import PopupMessage from "../../../components/Popup/Popup";

const AllProducts = () => {
    const location = useLocation();
    const navigate = useNavigate();

    const [selectedCategory, setSelectedCategory] = useState(location.state?.selectedCategory || null);
    const [selectedSubcategory, setSelectedSubcategory] = useState(location.state?.selectedSubcategory || null);
    const [products, setProducts] = useState([]);
    const [filteredProducts, setFilteredProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
    const [showPopup, setShowPopup] = useState(false);
    const customer_id = localStorage.getItem("customer_id") || null;

    const fetchProductsBySubcategory = async (categoryName, subCategoryName) => {
        try {
            const productRes = await axios.post(
                `http://127.0.0.1:8000/categories/${categoryName}/${subCategoryName}/`,
                {
                    customer_id,
                }
            );

            if (productRes.data.status_code === 200) {
                setProducts(productRes.data.products);
                setFilteredProducts(productRes.data.products); // Initialize filtered with full list
                setError(null);
            } else {
                setProducts([]);
                setFilteredProducts([]);
                setError("No products found for the selected subcategory.");
            }
        } catch (err) {
            console.error("Failed to fetch products", err);
            setError("An error occurred while fetching products.");
        }
    };

    const handleSubcategoryClick = (categoryName, subCategoryName) => {
        setSelectedSubcategory(subCategoryName);
        fetchProductsBySubcategory(categoryName, subCategoryName);
    };

    useEffect(() => {
        const fetchInitialData = async () => {
            setLoading(true);
            try {
                if (selectedCategory && selectedSubcategory) {
                    await fetchProductsBySubcategory(selectedCategory.category_name, selectedSubcategory);
                } else {
                    setError("Category or subcategory not selected.");
                }
            } catch (err) {
                console.error("Error fetching initial data", err);
                setError("An error occurred while loading data.");
            } finally {
                setLoading(false);
            }
        };

        fetchInitialData();
    }, [selectedCategory, selectedSubcategory]);

    // 🔍 Listen to the custom search event
    useEffect(() => {
        const handleSearchEvent = (e) => {
            const searchQuery = e.detail.toLowerCase();

            if (searchQuery === "") {
                setFilteredProducts(products); // Reset to full list
            } else {
                const filtered = products.filter((product) =>
                    product.product_name.toLowerCase().includes(searchQuery)
                );
                setFilteredProducts(filtered);
            }
        };

        window.addEventListener("customerCategorySearch", handleSearchEvent);
        return () => {
            window.removeEventListener("customerCategorySearch", handleSearchEvent);
        };
    }, [products]);

    const handleViewProductDetails = (product) => {
        if (!selectedCategory || !selectedSubcategory) return;

        navigate(`/product-details/${selectedCategory.category_name}/${selectedSubcategory}/${product.product_id}`, {
            state: {
                category_id: selectedCategory.category_id,
                sub_category_id: product.sub_category_id,
                category_name: selectedCategory.category_name,
                sub_category_name: selectedSubcategory,
                product_name: product.product_name,
                product,
            },
        });
    };

    const displayPopup = (text, type = "success") => {
        setPopupMessage({ text, type });
        setShowPopup(true);
        setTimeout(() => setShowPopup(false), 10000);
    };

    const handleAddCart = async (product_id) => {
        if (!customer_id) {
            displayPopup(
                <>
                    Please <Link to="/customer-login" className="popup-link">log in</Link> to add products to cart.
                </>,
                "error"
            );
            navigate("/customer-login");
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
                window.dispatchEvent(new Event("cartUpdated"));
            } else {
                displayPopup(data.error || "Failed to add product to cart.", "error");
            }
        } catch (error) {
            displayPopup("An unexpected error occurred while adding to cart.", "error");
        }
    };

    if (loading) return <div>Loading...</div>;
    if (error && products.length === 0) return <div>{error}</div>;

    return (
        <div className="all-products-container">
            <Side
                categories={selectedCategory ? [selectedCategory] : []}
                handleSubcategoryClick={handleSubcategoryClick}
            />

            <div className="all-products-section">
                <div className="all-products-list">
                    {filteredProducts.length > 0 ? (
                        filteredProducts.map((product) => (
                            <div
                                key={product.product_id}
                                className="all-product-item"
                                onClick={() => handleViewProductDetails(product)}
                            >
                                <img
                                    className="all-product-image"
                                    src={product.product_image_url}
                                    alt={product.product_name}
                                    // onError={(e) => (e.target.src = defaultImage)}
                                />
                                <p className="all-product-name">{product.product_name}</p>
                                <p className="all-product-price">₹ {product.final_price}.00</p>
                                <p className="all-product-availability">
                                    <span
                                        className={`availability ${
                                            product.availability === "Out of Stock"
                                                ? "out-of-stock"
                                                : product.availability === "Very Few Products Left"
                                                ? "few-left"
                                                : "in-stock"
                                        }`}
                                    >
                                        {product.availability === "Out of Stock"
                                            ? "Out of Stock"
                                            : product.availability === "Very Few Products Left"
                                            ? "Few Products Left"
                                            : "In Stock"}
                                    </span>
                                </p>
                                {(product.availability === "Very Few Products Left" ||
                                    product.availability === "In Stock") && (
                                    <BiSolidCartAdd
                                        className="add-to-cart-button"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleAddCart(product.product_id);
                                        }}
                                    />
                                )}
                            </div>
                        ))
                    ) : (
                        <p>No products available for this subcategory.</p>
                    )}
                </div>
            </div>

            {showPopup && <PopupMessage text={popupMessage.text} type={popupMessage.type} />}
        </div>
    );
};

export default AllProducts;
