import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "../CustomerViewCategory/CustomerViewCategory.css";
import "../CustomerViewSubCategory/CustomerViewSubCategory.css";

import defaultImage from "../../../assets/images/default.png"
import ViewDiscountedProducts from "../CustomerDiscountProducts/CustomerDiscountProducts";
import { Range } from 'react-range';
import CarouselLanding from "../CustomerCarousel/CustomerCarousel";

const ViewSubCategoriesAndDiscountedProducts = () => {
    const navigate = useNavigate();
    const [categories, setCategories] = useState([]);
    const [discountedProducts, setDiscountedProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const location = useLocation();

    const category_name = location.state?.category_name;
    const category_id = location.state?.category_id;
    const [minPrice, setMinPrice] = useState(0);
    const [maxPrice, setMaxPrice] = useState(10000);
    const [values, setValues] = useState([0, 10000]);

    useEffect(() => {
        if (category_name) {
            fetchSubCategories(category_name);
        }
    }, [category_name]);


    useEffect(() => {
        if (category_id) {
            localStorage.setItem("category_id", category_id);
        }
    }, [category_id]);

    useEffect(() => {
        if (!category_name) return;

        fetchSubCategories(category_name);

        const handleSearch = (e) => {
            const query = e.detail;
            console.log("🔍 Subcategory search triggered with query:", query);
            if (!query) {
                fetchSubCategories(category_name);
            } else {
                searchSubCategories(query);
            }
        };

        window.addEventListener("customerCategorySearch", handleSearch);
        return () => window.removeEventListener("customerCategorySearch", handleSearch);
    }, [category_name]);


    const fetchSubCategories = async (categoryName) => {
        try {
            const response = await fetch("http://127.0.0.1:8000/categories/view-sub-categories/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    category_id: category_id,
                    category_name: categoryName,
                    customer_id: localStorage.getItem("customer_id") || null

                }),
            });

            const data = await response.json();
            if (data.status_code === 200) {
                setCategories(data.subcategories);
                setDiscountedProducts(data.discounted_products);

                setMinPrice(data.min_price);
                setMaxPrice(data.max_price);
                setValues([data.min_price, data.max_price]);
            } else {
                setError(data.error || "Failed to fetch data");
            }
        } catch (error) {
            setError("An unexpected error occurred.");
        } finally {
            setLoading(false);
        }
    };

    const searchSubCategories = async (query) => {
        setLoading(true);
        try {
            const payload = {
                sub_category_name: query,
                category_id: category_id || localStorage.getItem("category_id"),
                customer_id: localStorage.getItem("customer_id") || null,
            };
            console.log("📨 Subcategory search payload:", payload);

            const response = await fetch("http://127.0.0.1:8000/customer-search-subcategories", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await response.json();
            console.log("📬 Subcategory API response:", data);

            if (data.status_code === 200 && data.categories) {
                setCategories(data.categories); // ✅ correct key
                setError("");
            } else {
                setCategories([]);
                setError(data.message || "No matching subcategories found.");
            }

        } catch (err) {
            setError("Subcategory search failed.");
        } finally {
            setLoading(false);
        }
    };



    const handleViewProducts = (subCategory) => {
        // sessionStorage.setItem("sub_category_id", subCategory.sub_category_id);
        localStorage.setItem("sub_category_id", subCategory.sub_category_id);

        navigate(`/categories/${category_name}/${subCategory.sub_category_name}`);
    };

    const handleFilterProducts = async () => {
        const [min, max] = values;
        setMinPrice(min);
        setMaxPrice(max);

        try {
            const response = await fetch("http://127.0.0.1:8000/filter-product-price-each-category", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    category_id: localStorage.getItem("category_id"),
                    category_name: category_name,
                    customer_id: localStorage.getItem("customer_id") || null,
                    min_price: min,
                    max_price: max,
                }),
            });

            const data = await response.json();

            if (data.status_code === 200) {
                const filteredProducts = data.sub_categories
                    .flatMap((subcategory) => subcategory.products)
                    .filter((product) => product !== undefined);

                navigate("/filtered-products", { state: { filteredProducts } });
            } else {
                setError(data.error || "Failed to fetch filtered products.");
            }
        } catch (error) {
            setError("An unexpected error occurred while filtering.");
        }
    };


    return (
        <div className="customer-dashboard container">
            <CarouselLanding />

            {loading && <p>Loading...</p>}
            {error && <p>{error}</p>}

            {!loading && !error && (
                <div className="breadcrumb">
                    <span className="breadcrumb-link" onClick={() => navigate("/")}>Home</span>
                    <span className="breadcrumb-separator"> &gt; </span>
                    <span className="breadcrumb-link" onClick={() => navigate("/")}>{category_name}</span>
                    <span className="breadcrumb-separator"> &gt; </span>
                    <span className="breadcrumb-current">Subcategories</span>
                </div>
            )}

            {/* 🆕 Add Flex Layout for Sidebar + Content */}
            <div className="customer-page-layout">
                {/* Sidebar Filter */}
                <div className="sidebar-filter">
                    <div className="sidebar-filter-heading">Filter by Price</div>
<div>

                    <div className="slider-btn">
                        <Range
                            className="price-slider-range"
                            values={values}
                            step={100}
                            min={minPrice}
                            max={maxPrice}
                            onChange={(newValues) => setValues(newValues)}
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

                    </div>
                    <div className="slider-price-btn">

                    <div className="sidebar-filter-values">

                        <label className="price-range-label">

                            <div> ₹{values[0]} - ₹{values[1]}</div>
                        </label>
                    </div>
                    <button className="filter-button" onClick={handleFilterProducts}>
                        Filter
                    </button>
                    </div>
</div>
                </div>

                {/* Main Content */}
                <div className="sub-main-content">
                    <div className="customer-products">
                        <div className="customer-products-heading">Subcategories</div>
                        <div className="customer-products-section">
                            {categories.map((subcategory) => (
                                <div key={subcategory.sub_category_id} className="customer-product-card"
                                    onClick={() => handleViewProducts(subcategory)}>
                                    <img
                                        src={subcategory.sub_category_image_url}
                                        alt={subcategory.sub_category_name}
                                        className="customer-product-image"
                                        // onError={(e) => e.target.src = defaultImage}
                                    />
                                    <div className="customer-product-name">{subcategory.sub_category_name}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="empty-space"></div>
                    <ViewDiscountedProducts />
                </div>
            </div>
        </div>

    );
};

export default ViewSubCategoriesAndDiscountedProducts;