import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useNavigate, useLocation } from "react-router-dom";
import Logo from "../../assets/images/logo.png";
import SearchIcon from "../../assets/images/search.svg";
import RefreshIcon from "../../assets/images/search.svg"; // Add an icon for refresh
import { IoPerson } from "react-icons/io5";
import { RiRefreshLine } from "react-icons/ri";
import { LuRefreshCw } from "react-icons/lu";
import "../Header/Header.css";

const Header = ({ setIsAuthenticated, setCategories, setSubcategories, setProducts }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const [searchQuery, setSearchQuery] = useState("");
    const [errorMessage, setErrorMessage] = useState("");
    const [showDropdown, setShowDropdown] = useState(false);
    const dropdownRef = useRef(null);

    const adminData = JSON.parse(sessionStorage.getItem("adminData") || "{}");
    const adminEmail = adminData.email || "Admin";


    const handleLogout = () => {
        sessionStorage.clear();
        localStorage.clear();

        setIsAuthenticated(false);
        navigate("/admin-login");
    };

    const toggleDropdown = () => {
        setShowDropdown((prev) => !prev);
    };

    // Close dropdown if clicked outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setShowDropdown(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);


    const [searchTriggered, setSearchTriggered] = useState(false);

    const handleSearch = async (event) => {
        event.preventDefault();
        setErrorMessage("");
    
        if (!searchQuery.trim()) {
            return;
        }
    
        let apiUrl = "";
        let requestBody = {};
    
        if (location.pathname.includes("/view-categories")) {
            apiUrl = "http://65.0.183.78:8000/search-categories";
            requestBody = {
                admin_id: sessionStorage.getItem("admin_id"),
                category_name: searchQuery,
            };
        } else if (location.pathname.includes("/view-subcategories")) {
            apiUrl = "http://65.0.183.78:8000/search-subcategories";
            const categoryData = JSON.parse(sessionStorage.getItem("categoryData") || "{}");
            requestBody = {
                admin_id: sessionStorage.getItem("admin_id"),
                category_id: categoryData.category_id,
                sub_category_name: searchQuery,
            };
        } else if (location.pathname.includes("/view-products")) {
            apiUrl = "http://65.0.183.78:8000/search-products";
            const categoryData = JSON.parse(sessionStorage.getItem("categoryData") || "{}");
            const subCategoryData = JSON.parse(sessionStorage.getItem("subCategoryData") || "{}");
            requestBody = {
                admin_id: sessionStorage.getItem("admin_id"),
                category_id: categoryData.category_id,
                sub_category_id: subCategoryData.sub_category_id,
                product_name: searchQuery,
            };
        }
    
        try {
            const response = await axios.post(apiUrl, requestBody, { withCredentials: true });
            
            if (location.pathname.includes("/view-categories")) {
                setCategories(response.data.categories || []);
            } else if (location.pathname.includes("/view-subcategories")) {
                setSubcategories(response.data.subcategories || []);
            } else if (location.pathname.includes("/view-products")) {
                setProducts(response.data.products || []);
            }
    
            setSearchTriggered(true); // Show Refresh button once search is successful
        } catch (error) {
            console.error("Search Error:", error);
            setErrorMessage("Something went wrong. Please try again.");
        }
    };
    
    const handleRefresh = () => {
        setSearchQuery("");  // Clear search input
        setErrorMessage(""); // Clear any error message
        setSearchTriggered(false); // Show Search button again
    
        if (location.pathname.includes("/view-categories")) {
            fetchCategories();
        } else if (location.pathname.includes("/view-subcategories")) {
            fetchSubcategories();
        } else if (location.pathname.includes("/view-products")) {
            fetchProducts();
        }
    };
    

    const fetchCategories = async () => {
        setErrorMessage("");
        try {
            const response = await axios.post("http://65.0.183.78:8000/view-categories", {
                admin_id: sessionStorage.getItem("admin_id"),
            }, { withCredentials: true });
            setCategories(response.data.categories || []);
        } catch (error) {
            setErrorMessage("Something went wrong. Please try again.");
        }
    };

    const fetchSubcategories = async () => {
        setErrorMessage("");
        try {
            const response = await axios.post("http://65.0.183.78:8000/view-subcategories", {
                admin_id: sessionStorage.getItem("admin_id"),
                category_id: JSON.parse(sessionStorage.getItem("categoryData") || "{}").category_id,
            }, { withCredentials: true });
            setSubcategories(response.data.subcategories || []);
        } catch (error) {
            setErrorMessage("Something went wrong. Please try again.");
        }
    };

    const fetchProducts = async () => {
        setErrorMessage("");
        try {
            const response = await axios.post("http://65.0.183.78:8000/view-products", {
                admin_id: sessionStorage.getItem("admin_id"),
                category_id: JSON.parse(sessionStorage.getItem("categoryData") || "{}").category_id,
                sub_category_id: JSON.parse(sessionStorage.getItem("subCategoryData") || "{}").sub_category_id,
            }, { withCredentials: true });
            setProducts(response.data.products || []);
        } catch (error) {
            setErrorMessage("Something went wrong. Please try again.");
        }
    };

    return (
        <header>
            <div className="top-nav">
                <img src={Logo} alt="Pavaman Logo" className="logo" />

                <div className="search-container">
                    {(location.pathname.includes("/view-categories") ||
                      location.pathname.includes("/view-subcategories") ||
                      location.pathname.includes("/view-products")) && (
                        <form className="search-bar" onSubmit={handleSearch}>
                        <input
                            type="text"
                            className="search-input"
                            placeholder={
                                location.pathname.includes("/view-categories")
                                    ? "Search for Category..."
                                    : location.pathname.includes("/view-subcategories")
                                    ? "Search for Subcategory..."
                                    : "Search for Product..."
                            }
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    
                        {searchTriggered ? (
                            // Show Refresh button once search results are displayed
                            <RiRefreshLine className="refresh-button" onClick={handleRefresh} />
                        ) : (
                            // Show Search button initially
                            <button type="submit" className="search-button">
                                <img src={SearchIcon} alt="Search" className="search-icon" />
                            </button>
                        )}
                    </form>
                    
                    )}
                </div>
                 <div className="profile-container" ref={dropdownRef}>
                    <IoPerson className="profile-icon" onClick={toggleDropdown} />

                    {showDropdown && (
                        <div className="profile-dropdown">
                            <p className="dropdown-item">{adminEmail}</p>
                            <button className="dropdown-item logout-button" onClick={handleLogout}>
                                Logout
                            </button>
                        </div>
                    )}
                </div>
              
            </div>

            {errorMessage && <p className="error-message">{errorMessage}</p>}
        </header>
    );
};

export default Header;
