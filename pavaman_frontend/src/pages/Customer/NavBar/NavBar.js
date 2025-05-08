import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { FiMenu, FiChevronRight, FiHome, FiShoppingBag, FiPhone } from "react-icons/fi";
import { FaClipboardList } from "react-icons/fa";
import "./NavBar.css"; // Ensure styles match Figma

const Navbar = () => {
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState({});
  const [products, setProducts] = useState({});
  const [isCollapsed, setIsCollapsed] = useState(true);
  const [hoveredCategory, setHoveredCategory] = useState(null);
  const [hoveredSubcategory, setHoveredSubcategory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await fetch("http://65.0.183.78:8000/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await response.json();
      if (data.status_code === 200) {
        setCategories(data.categories);
      } else {
        setError(data.error || "Failed to fetch categories.");
      }
    } catch (error) {
      setError("An unexpected error occurred while fetching categories.");
    }
  };

  const fetchSubCategories = async (categoryName) => {
    if (subcategories[categoryName]) return; // Avoid fetching again if already loaded

    setLoading(true);
    try {
      const response = await fetch("http://65.0.183.78:8000/categories/view-sub-categories/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category_name: categoryName,
          // customer_id: sessionStorage.getItem("customer_id") || null,
          customer_id: localStorage.getItem("customer_id") || null,

        }),
      });

      const data = await response.json();
      if (data.status_code === 200) {
        setSubcategories((prev) => ({ ...prev, [categoryName]: data.subcategories }));
      } else {
        setError(data.error || "Failed to fetch subcategories.");
      }
    } catch (error) {
      setError("An unexpected error occurred while fetching subcategories.");
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async (subcategoryId, categoryName, subCategoryName) => {
    if (products[subcategoryId] !== undefined) return; // Avoid redundant API calls
  
    setProducts((prev) => ({ ...prev, [subcategoryId]: "loading" })); // Temporary loading state
  
    try {
      const response = await fetch(
        `http://65.0.183.78:8000/categories/${categoryName}/${subCategoryName}/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sub_category_id: subcategoryId }),
        }
      );
  
      const data = await response.json();
      console.log("Products API response:", data);
  
      setProducts((prev) => ({
        ...prev,
        [subcategoryId]: data.products?.length > 0 ? data.products : [],
      }));
    } catch (error) {
      console.error("Error fetching products:", error);
      setProducts((prev) => ({ ...prev, [subcategoryId]: [] })); // Ensure it's never undefined
    }
  };
  
  
  useEffect(() => {
    console.log("Hovered Subcategory Changed:", hoveredSubcategory);
    console.log("Products State Updated:", products);
  }, [hoveredSubcategory, products]);
  
  return (
    <div className="navbar-container">
      {/* Sidebar Toggle Button */}
      <div className="sidebar-header"  onMouseEnter={() => setIsCollapsed(false)}  // Open on hover
                onMouseLeave={() => setIsCollapsed(true)} >
        <button className="menu-btn" >
          <FiMenu size={24} />
        </button>
        <p className="menu-name">All Categories</p>
      </div>

      {/* Sidebar Menu */}
      <div className={`sidebar ${isCollapsed ? "collapsed" : ""}`}
      onMouseEnter={() => setIsCollapsed(false)}
      onMouseLeave={() => setIsCollapsed(true)}
      >
        {!isCollapsed && (
          <div className="sidebar-content">
            {/* {error && <p className="error">{error}</p>} */}
            <ul className="category-list">
              {categories.map((category) => (
                <li
                  key={category.category_id}
                  className="category-item"
                  onMouseEnter={() => {
                    setHoveredCategory(category.category_name);
                    fetchSubCategories(category.category_name);
                  }}
                >
                  <button
                    onClick={() =>
                      navigate(`/categories/view-sub-categories/`, { state: { category_name: category.category_name } })
                    }
                    className="category-btn"
                  >
                    {category.category_name} <FiChevronRight className="arrow-icon" />
                  </button>

                  {/* Subcategories */}
                  {hoveredCategory === category.category_name && subcategories[category.category_name] && (
                    <ul className="subcategory-list">
                      {subcategories[category.category_name].map((sub) => (
                        <li
                          key={sub.sub_category_id}
                          className="subcategory-item"
                          onMouseEnter={() => {
                            if (hoveredSubcategory !== sub.sub_category_id) {
                              setHoveredSubcategory(sub.sub_category_id);
                              
                              // Don't clear all products, only update when needed
                              if (!products[sub.sub_category_id]) {
                                fetchProducts(sub.sub_category_id, category.category_name, sub.sub_category_name);
                              }
                            }
                          }}
                          
                          
                          
                        >
                          <button
                            onClick={() =>
                              navigate(`/categories/${category.category_name}/${sub.sub_category_name}`, {
                                state: { sub_category_id: sub.sub_category_id },
                              })
                            }
                            className="subcategory-btn"
                          >
                            {sub.sub_category_name} <FiChevronRight className="arrow-icon" />
                          </button>
                          {hoveredSubcategory !== null && products.hasOwnProperty(hoveredSubcategory) && (
  <ul className="product-list">
    {products[hoveredSubcategory] === "loading" ? (
      <li className="loading">Loading products...</li>
    ) : products[hoveredSubcategory]?.length > 0 ? (
      products[hoveredSubcategory].map((prod) => (
        <li key={prod.product_id} className="product-item">
          {prod.product_name}
        </li>
      ))
    ) : (
      <li className="no-products">No products available.</li>
    )}
  </ul>
)}

                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

     
      
      <div className="navbar-links" onClick={() => navigate("/")}>
          <FiHome className="nav-icon" /> <span>Home</span>
        </div>
        <div className="navbar-links" onClick={() => navigate("/shop")}>
          <FiShoppingBag className="nav-icon" /> <span>Shop</span>
        </div>
        <div className="navbar-links" onClick={() => navigate("/order")}>
          <FaClipboardList className="nav-icon" /> <span>Order</span>
        </div>
        <div className="navbar-links" onClick={() => navigate("/contact")}>
          <FiPhone className="nav-icon" /> <span>Contact</span>
        </div>
      </div>
    
  );
};

export default Navbar;