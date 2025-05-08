import React, { useEffect, useState } from "react";
import "../CustomerViewCategory/CustomerViewCategory.css";
import { useNavigate } from "react-router-dom";
import defaultImage from "../../../assets/images/product.png"
import ViewDiscountedProducts from "../CustomerDiscountProducts/CustomerDiscountProducts";
import CarouselLanding from "../CustomerCarousel/CustomerCarousel";

const ViewCategoriesAndDiscountedProducts = () => {
    const navigate = useNavigate();

    const [categories, setCategories] = useState([]);
    const [discountedProducts, setDiscountedProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        fetchData();
    }, []);

    useEffect(() => {
        fetchData();
      
        const handleSearch = (e) => {
          const query = e.detail;
          if (!query) {
            fetchData(); // Reset categories
          } else {
            searchCategories(query);
          }
        };
      
        window.addEventListener("customerCategorySearch", handleSearch);
        return () => window.removeEventListener("customerCategorySearch", handleSearch);
      }, []);

      
    const fetchData = async () => {
        try {
            const response = await fetch("http://65.0.183.78:8000/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                // body: JSON.stringify({ customer_id: sessionStorage.getItem("customer_id") || null }),
                body: JSON.stringify({ customer_id: localStorage.getItem("customer_id") || null }),

            });

            const data = await response.json();

            if (data.status_code === 200) {
                setCategories(data.categories);
                setDiscountedProducts(data.discounted_products);
            } else {
                setError(data.error || "Failed to fetch data");
            }
        } catch (error) {
            setError("An unexpected error occurred.");
        } finally {
            setLoading(false);
        }
    };

    const searchCategories = async (query) => {
        setLoading(true);
        try {
          const response = await fetch("http://65.0.183.78:8000/customer-search-categories", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              category_name: query,
              customer_id: localStorage.getItem("customer_id") || null,
            }),
          });
      
          const data = await response.json();
          if (data.status_code === 200 && data.categories) {
            setCategories(data.categories);
            setError("");
          } else {
            setCategories([]);
            setError(data.message || "No matching categories found.");
          }
        } catch (err) {
          setError("Search failed.");
        } finally {
          setLoading(false);
        }
      };

      
    const handleViewSubCategory = (category) => {
        // sessionStorage.setItem("category_id", category.category_id);
        localStorage.setItem("category_id", category.category_id);

        navigate("/categories/view-sub-categories/", { state: { category_name: category.category_name } });
    };
    
    return (
      <div>
      <CarouselLanding />

     
        <div className="customer-dashboard container">
            {loading && <p>Loading...</p>}
            {error && <p >{error}</p>}

            {!loading && !error && (
                <>
                    <div className="customer-products">
                        <div className="customer-products-heading">Categories</div>
                        <div className="customer-products-section"  >
                            {categories.map((category) => (
                                <div key={category.category_id} className="customer-product-card" 
                                onClick={() => handleViewSubCategory(category)}
>
                                    <img
                                        src={category.category_image_url}
                                        alt={category.category_name}
                                        className="customer-product-image"
                                        // onError={(e) => e.target.src = defaultImage}
                                    />

                                    <div className="customer-product-name">{category.category_name}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="empty-space"></div>
                    <ViewDiscountedProducts />
                </>
            )}
        </div>
        </div>
    );
};

export default ViewCategoriesAndDiscountedProducts;
