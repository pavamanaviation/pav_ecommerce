import React, { useState, useEffect } from "react";
import { FaSearch, FaMapMarkerAlt, FaShoppingCart, FaUser, FaClipboardList, FaSignOutAlt, FaSignInAlt, } from "react-icons/fa";
import { IoMdPerson } from "react-icons/io";
import { TbShoppingBagEdit } from "react-icons/tb";
import { FiMenu, FiChevronRight, FiHome, FiPhone } from "react-icons/fi";
import { useLocation, useNavigate } from "react-router-dom";
import "../CustomerHeader/CustomerHeader.css";
import Logo from "../../../assets/images/logo.png";
import PopupMessage from "../../../components/Popup/Popup";
import { Link } from "react-router-dom";
import { BiCategory } from "react-icons/bi";
import MobileHeader from "./MobileHeader";
import { IoMdClose } from "react-icons/io"
import { LuBriefcaseBusiness } from "react-icons/lu";

const CustomerHeader = (onSearch) => {
  const navigate = useNavigate();
  const location = useLocation();

  const [cartCount, setCartCount] = useState(0);
  const [isUserDropdownOpen, setIsUserDropdownOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(true);
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState({});
  const [products, setProducts] = useState({});
  const [hoveredCategory, setHoveredCategory] = useState(null);
  const [hoveredSubcategory, setHoveredSubcategory] = useState(null);
  const [error, setError] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [popupMessage, setPopupMessage] = useState({ text: "", type: "" });
  const [showPopup, setShowPopup] = useState(false);
  const [searchInput, setSearchInput] = useState("");
  const [searchPlaceholder, setSearchPlaceholder] = useState("Search...");
  // const [hovered, setHovered] = useState(false);
    const [customer, setCustomer] = useState(null);
    const [loading, setLoading] = useState(true);
  const customerId = localStorage.getItem("customer_id");

  const isValidCustomerId = !(
    customerId === null ||
    customerId === "null" ||
    customerId === "undefined" ||
    customerId === ""
  );

  const shouldShowLoginSignup = !isValidCustomerId;

  useEffect(() => {
    if (location.pathname.includes("/categories/view-sub-categories")) {
      setSearchPlaceholder("Search for Subcategories...");
    } else if (location.pathname.includes("/categories/")) {
      setSearchPlaceholder("Search for Products...");
    } else if (location.pathname.includes("/filtered-products")) {
      setSearchPlaceholder("Search for Products...");
    }else if( location.pathname.includes("/view-cart-products")){
      setSearchPlaceholder("Search Cart Products ...");
    } else if (location.pathname.includes("/")) {
      setSearchPlaceholder("Search for Categories...");
    }
    setIsLoggedIn(isValidCustomerId);
    fetchCartCount();
    fetchCategories();

    const updateCart = () => fetchCartCount();
    window.addEventListener("cartUpdated", updateCart);
    return () => window.removeEventListener("cartUpdated", updateCart);
  }, [location]);

  const handleSearch = () => {
    const trimmedQuery = searchInput.trim();
    console.log("Dispatching search event with query:", trimmedQuery);
    window.dispatchEvent(new CustomEvent("customerCategorySearch", { detail: trimmedQuery }));
  };

  const fetchCartCount = async () => {
    const customer_id =
      sessionStorage.getItem("customer_id") || localStorage.getItem("customer_id");

    if (!customer_id) return;

    try {
      const response = await fetch("http://127.0.0.1:8000/view-cart-products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ customer_id }),
      });

      const data = await response.json();
      console.log("Cart API response:", data); // For debugging

      if (data.status_code === 200) {
        const items = data.cart_items || [];
        setCartCount(items.length);
      }
    } catch (error) {
      console.error("Error fetching cart count:", error);
    }
  };



  const displayPopup = (text, type = "success") => {
    setPopupMessage({ text, type });
    setShowPopup(true);

    setTimeout(() => {
      setShowPopup(false);
    }, 10000);
  };

  const fetchCategories = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/", {
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
    if (subcategories[categoryName]) return;

    try {
      const response = await fetch("http://127.0.0.1:8000/categories/view-sub-categories/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category_name: categoryName,
          customer_id: sessionStorage.getItem("customer_id") || null,
        }),
      });
      const data = await response.json();
      if (data.status_code === 200) {
        setSubcategories((prev) => ({ ...prev, [categoryName]: data.subcategories }));
      }
    } catch {
      console.error("Error fetching subcategories");
    }
  };

  const fetchProducts = async (subCatId, categoryName, subCatName) => {
    if (products[subCatId] !== undefined) return;

    setProducts((prev) => ({ ...prev, [subCatId]: "loading" }));
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/categories/${categoryName}/${subCatName}/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sub_category_id: subCatId }),
        }
      );
      const data = await response.json();
      setProducts((prev) => ({
        ...prev,
        [subCatId]: data.products?.length ? data.products : [],
      }));
    } catch {
      setProducts((prev) => ({ ...prev, [subCatId]: [] }));
    }
  };

  const handleProductClick = (categoryName, subCategoryName, productId) => {
    setIsCollapsed(true); // Hide sidebar
    navigate(`/product-details/${categoryName}/${subCategoryName}/${productId}`);
  };

  const handleLogout = () => {
    localStorage.removeItem("customer_id");
    localStorage.clear();
    sessionStorage.clear();

    setIsLoggedIn(false);
    navigate("/");
  };

  const toggleUserDropdown = () => {
    setIsUserDropdownOpen(!isUserDropdownOpen);
  };

  const isUserLoggedIn = false;

  useEffect(() => {
        fetchCustomerProfile();
    }, [customerId]);

  const fetchCustomerProfile = async () => {

    try {
        const response = await fetch("http://127.0.0.1:8000/get-customer-profile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ customer_id: customerId }),
        });

        const data = await response.json();
        if (response.ok) {
            setCustomer(data.profile);
        } else {
            setError(data.error || "Failed to fetch customer profile");
            displayPopup(data.error || "Failed to fetch customer profile", "error");
        }
    } catch (error) {
        const message = "Fetch error: " + error.message;
        setError(message);
        displayPopup(message, "error");
    } finally {
        setLoading(false);
    }
};

  return (
    <>

      <header className="customer-header">
        <div className="customer-logo">
          <img src={Logo} alt="Logo" />
        </div>

        <div
          className="sidebar-header"
          onMouseEnter={() => setIsCollapsed(false)}
          onMouseLeave={() => setIsCollapsed(true)}
        >
          <button className="menu-btn"><BiCategory size={24} /></button>
          <p className="menu-name">Categories</p>

          <div className={`sidebar ${isCollapsed ? "collapsed" : ""}`}>
            <ul className="category-list">
              {categories.map((cat) => (
                <li
                  key={cat.category_id}
                  onMouseEnter={() => {
                    setHoveredCategory(cat.category_name);
                    fetchSubCategories(cat.category_name);
                  }}
                  className="category-item"
                >
                  <button
                    className="category-btn"
                    onClick={() => {
                      localStorage.setItem("category_name", cat.category_name);
                      localStorage.setItem("category_id", cat.category_id);
                      navigate(`/categories/view-sub-categories/`, {
                        state: { category_name: cat.category_name },
                      })
                    }}
                  >
                    {cat.category_name} <FiChevronRight />
                  </button>

                  {hoveredCategory === cat.category_name &&
                    subcategories[cat.category_name] && (
                      <ul className="subcategory-list">
                        {subcategories[cat.category_name].map((sub) => (
                          <li
                            key={sub.sub_category_id}
                            className="subcategory-item"
                            onMouseEnter={() => {
                              setHoveredSubcategory(sub.sub_category_id);
                              if (!products[sub.sub_category_id]) {
                                fetchProducts(
                                  sub.sub_category_id,
                                  cat.category_name,
                                  sub.sub_category_name
                                );
                              }
                            }}
                          >
                            <button
                              onClick={() => {
                                localStorage.setItem("category_id", cat.sub_category_id);

                                localStorage.setItem("category_name", cat.category_name);
                                localStorage.setItem("sub_category_name", sub.sub_category_name);
                                localStorage.setItem("sub_category_id", sub.sub_category_id);
                                navigate(
                                  `/categories/${cat.category_name}/${sub.sub_category_name}`,
                                  {
                                    state: {
                                      sub_category_id: sub.sub_category_id,
                                    },
                                  }
                                )
                              }}
                              className="subcategory-btn"
                            >
                              {sub.sub_category_name} <FiChevronRight />
                            </button>

                            {hoveredSubcategory === sub.sub_category_id && (
                              <ul className="product-list">
                                {products[sub.sub_category_id] === "loading" ? (
                                  <li>Loading products...</li>
                                ) : products[sub.sub_category_id]?.length > 0 ? (
                                  products[sub.sub_category_id].map((prod) => (
                                    <li key={prod.product_id}
                                      className="product-item"
                                      onClick={() => {
                                        localStorage.setItem("category_name", cat.category_name);
                                        localStorage.setItem("sub_category_name", sub.sub_category_name);
                                        localStorage.setItem("sub_category_id", sub.sub_category_id);
                                        localStorage.setItem("product_id", prod.product_id);
                                        localStorage.setItem("product_name", prod.product_name);

                                        setIsCollapsed(true);
                                        handleProductClick(cat.category_name, sub.sub_category_name, prod.product_id);
                                      }}
                                    >
                                      {prod.product_name}
                                    </li>
                                  ))
                                ) : (
                                  <li>No products</li>
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
        </div>

        {/* <div className="customer-search-bar">
      <input
        type="text"
        placeholder={searchPlaceholder}
        value={searchInput}
        onChange={(e) => setSearchInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
      />
      <FaSearch className="customer-search-icon" onClick={handleSearch} />
    </div> */}
        {/* 
<div className="customer-search-bar" >
  <input
    type="text"
    placeholder={searchPlaceholder}
    value={searchInput}
    onChange={(e) => setSearchInput(e.target.value)}
    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
  />

  {searchInput ? (
    <IoMdClose
    className="customer-search-icon"

      onClick={() => {
        setSearchInput("");
        window.dispatchEvent(new CustomEvent("customerCategorySearch", { detail: "" }));
      }}
   
    />
  ) : (
    <FaSearch
      onClick={handleSearch}
      className="customer-search-icon"
     
    />
  )}
</div> */}
        {(
          location.pathname.includes("/categories/view-sub-categories") ||
          location.pathname.includes("/categories/") ||
          location.pathname.includes("/filtered-products") ||
          location.pathname.includes("/view-cart-products")||
          location.pathname === "/"
        ) && (
            <div className="customer-search-bar">
              <input
                type="text"
                placeholder={searchPlaceholder}
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              />
              {searchInput ? (
                <IoMdClose
                  className="customer-search-icon"
                  onClick={() => {
                    setSearchInput("");
                    window.dispatchEvent(new CustomEvent("customerCategorySearch", { detail: "" }));
                  }}
                />
              ) : (
                <FaSearch
                  className="customer-search-icon"
                  onClick={handleSearch}
                />
              )}
            </div>
          )}

        <div className="nav-icon-wrapper">
          <div className="nav-item" onClick={() => navigate("/")}>
            <FiHome className="nav-icon" />
            <span>Home</span>
          </div>

          {/* <div className="nav-item" onClick={() => navigate("/orders")}> */}
          {/* <div
            className="nav-item"
            onClick={() => {
              handleHeaderOrders()
            }
            }
          >
            <TbShoppingBagEdit className="nav-icon" />
            <span>Order</span>
          </div> */}

          <div
            className="nav-item user-icon"
            onMouseEnter={() => window.innerWidth > 768 && setIsUserDropdownOpen(true)}
            onMouseLeave={() => window.innerWidth > 768 && setIsUserDropdownOpen(false)}
            onClick={toggleUserDropdown}
          >
            <IoMdPerson className="nav-icon" />
            <span>Account</span>
            {isUserDropdownOpen && (
              <div className="customer-dropdown-menu">
                <ul>
                  {shouldShowLoginSignup ? (
                    <>
                      <li onClick={() => navigate("/customer-login")}><FaSignInAlt /> Login /  SignUp</li>
                      {/* <li onClick={() => navigate("/customer-register")}><FaUser /> Sign Up</li> */}

                    </>
                  ) : (
                    <>
<li>
  <div className="customer-info">
    <span className="customer-name">Hello {customer.first_name}</span>
    {/* <span className="customer-email">{customer.email}</span>
    <span className="customer-email"> {customer.mobile_no}</span> */}

  </div>
</li>
                     

                      <li onClick={() => navigate("/profile")}><FaUser /> My Profile</li>
                      <li onClick={() => navigate("/my-orders")}><FaClipboardList /> My Orders</li>
                      <li onClick={() => navigate("/address")}><FaMapMarkerAlt /> Address</li>
                      <li onClick={handleLogout}><FaSignOutAlt />Logout </li>
                    </>
                  )}
                </ul>
              </div>
            )}
          </div>

          <div className="nav-item cart-icon" onClick={() => navigate("/view-cart-products")}>
            <FaShoppingCart className="nav-icon" />
            {cartCount > 0 && <span className="customer-cart-badge">{cartCount}</span>}
            <span>Cart</span>
          </div>

          <div className="nav-item" onClick={() => navigate("/contact")}>
            <FiPhone className="nav-icon" />
            <span>Contact</span>
          </div>
          {/* <div
                 onMouseEnter={() => setHovered(true)}
                 onMouseLeave={() => setHovered(false)}>

          <div className="nav-item" 
     
           >
            <LuBriefcaseBusiness className="nav-icon" />
            <span>B2B</span>
          </div>
          {hovered && (
            <div>
              <p>Want to customize your drones</p>
              <p>Reach out to us</p>
              <button  onClick={() => navigate("/CustomizePage")}>Reachout</button>
            </div>
          )}
        </div> */}
          </div>
      </header>
      <div className="mobile-header-section">

        <MobileHeader cartCount={cartCount} />
      </div>

    </>
  );
};

export default CustomerHeader;