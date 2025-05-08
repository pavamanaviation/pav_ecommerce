import React, { useEffect, useState } from "react";
import axios from "axios";
import defaultImage from "../../../assets/images/product.png";
import "./AllCategories.css";
import { useNavigate } from "react-router-dom";

const AllCategories = () => {
  const [categoriesWithSubcategories, setCategoriesWithSubcategories] = useState([]);
  const [filteredSubcategories, setFilteredSubcategories] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const customerId = localStorage.getItem("customer_id") || null;

  useEffect(() => {
    const fetchCategoriesAndSubcategories = async () => {
      try {
        const categoryRes = await axios.post("http://65.0.183.78:8000/get-all-category-subcategory", {
          customer_id: customerId,
        });

        if (categoryRes.data.status_code === 200) {
          setCategoriesWithSubcategories(categoryRes.data.categories);
        } else {
          setError("Failed to load categories");
        }
      } catch (err) {
        console.error("Failed to fetch categories and subcategories", err);
        setError("An error occurred while fetching data.");
      } finally {
        setLoading(false);
      }
    };

    fetchCategoriesAndSubcategories();
  }, [customerId]);

  // 🔍 Listen for search input
  useEffect(() => {
    const handleSearch = async (e) => {
      const searchValue = e.detail.trim();

      // If empty, reset filtered data
      if (!searchValue) {
        setFilteredSubcategories(null);
        return;
      }

      try {
        const results = [];

        for (const category of categoriesWithSubcategories) {
          const response = await axios.post("http://65.0.183.78:8000/customer-search-subcategories", {
            customer_id: customerId,
            category_id: category.category_id,
            sub_category_name: searchValue,
          });

          if (
            response.data.status_code === 200 &&
            response.data.categories &&
            response.data.categories.length > 0
          ) {
            results.push({
              category_id: category.category_id,
              category_name: category.category_name,
              sub_categoryies: response.data.categories.map((sub) => ({
                id: sub.sub_category_id,
                sub_category_name: sub.sub_category_name,
                sub_category_image: `http://65.0.183.78:8000${sub.sub_category_image}`,
              })),
            });
          }
        }

        setFilteredSubcategories(results);
      } catch (error) {
        console.error("Search error:", error);
        setFilteredSubcategories([]);
      }
    };

    window.addEventListener("customerCategorySearch", handleSearch);
    return () => window.removeEventListener("customerCategorySearch", handleSearch);
  }, [categoriesWithSubcategories, customerId]);

  const handleSubcategoryClick = (categoryName, subCategoryName) => {
    const selectedCategory = categoriesWithSubcategories.find(cat => cat.category_name === categoryName);
    navigate("/all-products", {
      state: {
        selectedCategory,
        selectedSubcategory: subCategoryName,
      },
    });
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  const renderCategories = filteredSubcategories || categoriesWithSubcategories;

  return (
    <div className="all-categories-section">
      {renderCategories.length > 0 ? (
        renderCategories
          .filter((cat) => cat.sub_categoryies && cat.sub_categoryies.length > 0)
          .map((cat) => (
            <div key={cat.category_id} className="all-categories">
              <h2 className="all-categories-heading">{cat.category_name}</h2>
              <div className="all-categories-subcategories">
                {cat.sub_categoryies.map((sub) => (
                  <div
                    key={sub.id}
                    className="all-categories-content"
                    onClick={() => handleSubcategoryClick(cat.category_name, sub.sub_category_name)}
                  >
                    <img
                      className="all-categories-image"
                      src={sub.sub_category_image || defaultImage}
                      alt={sub.sub_category_name}
                      // onError={(e) => (e.target.src = defaultImage)}
                    />
                    <p className="all-categories-name">{sub.sub_category_name}</p>
                  </div>
                ))}
              </div>
            </div>
          ))
      ) : (
        <div>No categories with subcategories available.</div>
      )}
    </div>
  );
};

export default AllCategories;
