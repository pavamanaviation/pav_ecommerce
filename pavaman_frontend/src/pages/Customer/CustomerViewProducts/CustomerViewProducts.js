import React, { useEffect, useState } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import defaultImage from "../../../assets/images/default.png";
import { BiSolidCartAdd } from "react-icons/bi";
import PopupMessage from "../../../components/Popup/Popup";
import { Link } from "react-router-dom";
import { Range } from 'react-range';
import CarouselLanding from "../CustomerCarousel/CustomerCarousel";
import "./CustomerViewProducts.css";

const CustomerViewProducts = () => {
    const { categoryName, subCategoryName } = useParams();
    const [allProducts, setAllProducts] = useState([]); // Store original data
    const [products, setProducts] = useState([]); // Display filtered/sorted products
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [sortOrder, setSortOrder] = useState(""); // Sorting state
    const navigate = useNavigate();
    const location = useLocation();
    const category_id = location.state?.category_id || localStorage.getItem("category_id");
    const sub_category_id = location.state?.sub_category_id || localStorage.getItem("sub_category_id");
    const customer_id = localStorage.getItem("customer_id") || null;

    const [minPrice, setMinPrice] = useState(0);
    const [maxPrice, setMaxPrice] = useState(10000);
    const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
    const [showPopup, setShowPopup] = useState(false);

    const [values, setValues] = useState([0, 10000]); // For slider component

    const displayPopup = (text, type = "success") => {
        setPopupMessage({ text, type });
        setShowPopup(true);

        setTimeout(() => {
            setShowPopup(false);
        }, 10000);
    };

    // useEffect(() => {
    //     fetchProducts();
    // }, [sortOrder]); // Refetch products when sorting order changes

    useEffect(() => {
        fetchFilteredAndSortedProducts();
    }, [sortOrder]);

    useEffect(() => {
        if (categoryName) {
            fetchProducts(categoryName); // Fetch initial products
        }

        const handleSearch = (e) => {
            const query = e.detail;
            console.log("🔍 Product search triggered with query:", query);
            if (!query) {
                fetchProducts(categoryName);  // Fetch all products if no search query
            } else {
                searchProducts(query);  // Trigger product search with query
            }
        };


        window.addEventListener("customerCategorySearch", handleSearch);
        return () => window.removeEventListener("customerCategorySearch", handleSearch);
    }, [categoryName]);


    const fetchProducts = async () => {
        setLoading(true);
        setError("");

        try {
            const response = await fetch("http://127.0.0.1:8000/sort-products-inside-subcategory", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    sub_category_id,
                    sub_category_name: subCategoryName,
                    sort_by: sortOrder || "latest",
                    customer_id,
                }),
            });

            const data = await response.json();

            if (data.status_code === 200) {
                setAllProducts(data.products);
                setProducts(data.products);

                // Set price range from API
                const minFromAPI = data.product_min_price || 0;
                const maxFromAPI = data.product_max_price || 10000;

                setMinPrice(minFromAPI);
                setMaxPrice(maxFromAPI);
                setValues([minFromAPI, maxFromAPI]);
            }
            else {
                setError(data.error || "Failed to fetch products.");
            }
        } catch (error) {
            setError("An unexpected error occurred.");
        } finally {
            setLoading(false);
        }
    };

    const searchProducts = async (query) => {
        setLoading(true);
        try {
            const payload = {
                product_name: query?.trim(), // ✅ Trim whitespace
                category_id: category_id || localStorage.getItem("category_id"),
                sub_category_id: sub_category_id || localStorage.getItem("sub_category_id"),
                customer_id: localStorage.getItem("customer_id") || null,
            };

            console.log("📨 Product search payload:", payload);

            const response = await fetch("http://127.0.0.1:8000/customer-search-products", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await response.json();
            console.log("📬 Product API response:", data);

            if (data.status_code === 200 && data.products) {
                setProducts(data.products);
                setError("");
            } else {
                setProducts([]);
                setError(data.message || "No matching products found.");
            }

        } catch (err) {
            setError("Product search failed.");
        } finally {
            setLoading(false);
        }
    };



    const handleViewProductDetails = (product) => {
        if (!category_id || !sub_category_id) {
            console.error("Missing category_id or sub_category_id");
            return;
        }

        localStorage.setItem("category_id", category_id);
        localStorage.setItem("sub_category_id", sub_category_id);
        localStorage.setItem("category_name", categoryName);
        localStorage.setItem("sub_category_name", subCategoryName);
        localStorage.setItem("product_name", product.product_name);
        navigate(`/product-details/${categoryName}/${subCategoryName}/${product.product_id}`, {
            state: {
                category_name: categoryName,
                sub_category_name: subCategoryName,
                product_name: product.product_name,
            },
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
    const fetchFilteredAndSortedProducts = async () => {
        setLoading(true);
        setError(null);

        const hasMin = values[0] !== '';
        const hasMax = values[1] !== '';
        const hasSort = sortOrder !== '';

        let requestBody = {
            category_id: category_id,
            category_name: categoryName,
            sub_category_id: sub_category_id,
            sub_category_name: subCategoryName,
            customer_id: customer_id
        };

        // Include price range and sorting order if present
        if (hasMin && hasMax && hasSort) {
            requestBody = {
                ...requestBody,
                min_price: values[0],  // Use the min value from the slider
                max_price: values[1],  // Use the max value from the slider
                sort_by: sortOrder
            };
        } else if (hasMin && hasMax) {
            requestBody = {
                ...requestBody,
                min_price: values[0],  // Use the min value from the slider
                max_price: values[1],  // Use the max value from the slider
                sort_by: 'low_to_high' // Default sorting when no sort is selected
            };
        } else if (hasSort) {
            requestBody = {
                ...requestBody,
                sort_by: sortOrder
            };
        }

        try {
            const response = await fetch('http://127.0.0.1:8000/filter-and-sort-products', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            const data = await response.json();

            if (response.ok) {
                setProducts(data.products);
            } else {
                setError(data.error || 'Failed to fetch products');
            }
        } catch (error) {
            setError('An error occurred while fetching products.');
        } finally {
            setLoading(false);
        }
    };



    return (
        <div className="customer-dashboard container">
            < CarouselLanding />
            {loading && <p>Loading...</p>}
            {error && <p>{error}</p>}

            {!loading && !error && (
                <div className="breadcrumb">
                    <span className="breadcrumb-link" onClick={() => navigate("/")}>Home</span>
                    <span className="breadcrumb-separator"> &gt; </span>

                    <span className="breadcrumb-link" onClick={() => navigate("/")}>
                        {categoryName}
                    </span>
                    <span className="breadcrumb-separator"> &gt; </span>

                    <span
                        className="breadcrumb-link"
                        onClick={() =>
                            navigate("/categories/view-sub-categories/", {
                                state: {
                                    category_name: categoryName,
                                    category_id: category_id,
                                },
                            })
                        }
                    >
                        {subCategoryName}
                    </span>
                    <span className="breadcrumb-separator"> &gt; </span>

                    <span className="breadcrumb-current">Products</span>
                </div>
            )}

            {!loading && !error && (
                <div className="customer-products">
                    <div className="customer-products-heading">{subCategoryName} - Products</div>
                    <div className="popup-discount">
                        {showPopup && (
                            <PopupMessage
                                message={popupMessage.text}
                                type={popupMessage.type}
                                onClose={() => setShowPopup(false)}
                            />
                        )}
                    </div>
                    <div className="product-filter-dashboard">
                        <div className="header-filter">
                            {/* Price Range Filter */}
                            <div className="filter-sort-section">
                                <div className="filter-heading-products">Filters</div>

                                <div className="price-slider-container">
                                    <label className="price-range-label">
                                        Price Range
                                        <div> ₹{values[0]} - ₹{values[1]}</div>
                                    </label>
                                    <div className="slider-btn">
                                        <Range
                                            className="price-slider-range"
                                            values={values}
                                            step={100}
                                            min={minPrice}
                                            max={maxPrice}
                                            onChange={(newValues) => {
                                                setValues(newValues);
                                            }}
                                            renderTrack={({ props, children }) => (
                                                <div
                                                    {...props}
                                                    style={{
                                                        ...props.style,
                                                        width: '100%',
                                                        background: 'white',
                                                        borderRadius: '4px',
                                                        margin: '20px 0',
                                                        border: '0.5px solid grey',
                                                    }}
                                                >
                                                    {children}
                                                </div>
                                            )}
                                            renderThumb={({ props }) => (
                                                <div
                                                    {...props}
                                                    style={{
                                                        ...props.style,
                                                        height: '15px',
                                                        width: '15px',
                                                        backgroundColor: '#4450A2',
                                                        borderRadius: '50%',
                                                    }}
                                                />
                                            )}
                                        />
                                        <button className="filter-button" onClick={fetchFilteredAndSortedProducts}>
                                            Filter
                                        </button>
                                    </div>
                                </div>

                                {/* Sorting Dropdown */}
                                <div className="sorting-section">
                                    <label>Sort by:   </label>
                                    <select onChange={(e) => setSortOrder(e.target.value)} value={sortOrder}>
                                        {/* <option value=""> Select</option> */}
                                        <option value="low_to_high"> Price : Low to High</option>
                                        <option value="high_to_low"> Price : High to Low</option>
                                        <option value="latest"> Latest</option>
                                    </select>
                                </div>
                            </div>
                        </div>


                        <div className="customer-products-section">

                            {products.length > 0 ? (
                                products.map((product) => (
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
                                        {/* <img
  src={
    product.product_image_url
      ? product.product_image_url
      : product.product_images?.[0] ?? '/default-placeholder.png'
  }
  alt={product.product_name}
  onError={(e) => {
    e.target.src = '/default-placeholder.png';
  }}
/> */}

                                        <div className="customer-product-name">{product.product_name}</div>
                                        <div className="customer-discount-section-price">₹{product.final_price}.00 (incl. GST)</div>
                                        <div >
                                            <div className="customer-discount-section-original-price">₹{product.price}.00 (incl. GST)</div>
                                            <div className="add-cart-section">
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
                                <div>

                                    <div>No products available.</div></div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CustomerViewProducts;
