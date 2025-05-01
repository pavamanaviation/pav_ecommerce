// import React, { useState, useEffect } from "react";
// import { useLocation, useNavigate } from "react-router-dom";
// import "./CustomerNavBar.css";
// import { FiMenu } from "react-icons/fi"; // Import Menu Icon

// const Navbar = () => {
//   const [categories, setCategories] = useState([]);
//   const [subcategories, setSubcategories] = useState({});
//   const [products, setProducts] = useState({});
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState("");
//   const [isCollapsed, setIsCollapsed] = useState(true); // Sidebar state

//   const navigate = useNavigate();
//   const location = useLocation();

//   useEffect(() => {
//     fetchCategories();
//   }, []);

//   const fetchCategories = async () => {
//     try {
//       const response = await fetch("http://127.0.0.1:8000/", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({}),
//       });
//       const data = await response.json();
//       if (data.status_code === 200) {
//         setCategories(data.categories);
//       } else {
//         setError(data.error || "Failed to fetch categories.");
//       }
//     } catch (error) {
//       setError("An unexpected error occurred while fetching categories.");
//     }
//   };

//   const category_name = location.state?.category_name;
//   useEffect(() => {
//     if (category_name) {
//       fetchSubCategories(category_name);
//     }
//   }, [category_name]);

//   const fetchSubCategories = async (categoryName) => {
//     setLoading(true);
//     try {
//       const response = await fetch("http://127.0.0.1:8000/categories/view-sub-categories/", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({
//           category_name: categoryName,
//           customer_id: sessionStorage.getItem("customer_id") || null,
//         }),
//       });

//       const data = await response.json();
//       if (data.status_code === 200) {
//         setSubcategories((prev) => ({ ...prev, [categoryName]: data.subcategories }));
//       } else {
//         setError(data.error || "Failed to fetch subcategories.");
//       }
//     } catch (error) {
//       setError("An unexpected error occurred while fetching subcategories.");
//     } finally {
//       setLoading(false);
//     }
//   };

//   useEffect(() => {
//     const subcategoryId = location.state?.sub_category_id;
//     const categoryName = location.state?.category_name;
//     const subCategoryName = location.state?.sub_category_name;

//     if (subcategoryId && categoryName && subCategoryName) {
//       fetchProducts(subcategoryId, categoryName, subCategoryName);
//     }
//   }, [location.state?.sub_category_id, location.state?.category_name, location.state?.sub_category_name]);

//   const fetchProducts = async (subcategoryId, categoryName, subCategoryName) => {
//     setProducts({});
//     try {
//       const response = await fetch(`http://127.0.0.1:8000/categories/${categoryName}/${subCategoryName}/`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ sub_category_id: subcategoryId }),
//       });

//       const data = await response.json();
//       if (data.status_code === 200) {
//         setProducts({ [subcategoryId]: data.products });
//       } else {
//         setError(data.error || "Failed to fetch products.");
//       }
//     } catch (error) {
//       setError("An unexpected error occurred while fetching products.");
//     }
//   };

//   useEffect(() => {
//     const handleClickOutside = (event) => {
//       if (!document.querySelector(".sidebar").contains(event.target) &&
//           !document.querySelector(".menu-btn").contains(event.target)) {
//         setIsCollapsed(true);
//       }
//     };

//     if (!isCollapsed) {
//       document.addEventListener("click", handleClickOutside);
//     }
//     return () => document.removeEventListener("click", handleClickOutside);
//   }, [isCollapsed]);

//   return (
//     <div className="Navbar conatiner ">
// <div className="sidebar-header">
//         <button className="menu-btn" onClick={() => setIsCollapsed(!isCollapsed)}>
//           <FiMenu size={24} />
//         </button>
//         {!isCollapsed && <p className="sidebar-title">Categories</p>}
//       </div>
//     <div className={`sidebar ${isCollapsed ? "collapsed" : ""}`}>
//       {/* Menu Button */}
      

//       {!isCollapsed && (
//         <div className="sidebar-content">
//           {error && <p className="error">{error}</p>}
//           <ul className="category-list">
//             {categories.map((category) => (
//               <li
//                 key={category.category_id}
//                 className="category-item"
//                 onMouseEnter={() => fetchSubCategories(category.category_name)}
//               >
//                 <button
//                   onClick={() =>
//                     navigate(`/categories/view-sub-categories/`, { state: { category_name: category.category_name } })
//                   }
//                   className="category-btn"
//                 >
//                   {category.category_name} ➤
//                 </button>

//                 {subcategories[category.category_name] && (
//                   <ul className="subcategory-list">
//                     {subcategories[category.category_name].map((sub) => (
//                       <li
//                         key={sub.sub_category_id}
//                         className="subcategory-item"
//                         onMouseEnter={() =>
//                           fetchProducts(sub.sub_category_id, category.category_name, sub.sub_category_name)
//                         }
//                       >
//                         <button
//                           onClick={() =>
//                             navigate(`/categories/${category.category_name}/${sub.sub_category_name}`, {
//                               state: { sub_category_id: sub.sub_category_id },
//                             })
//                           }
//                           className="subcategory-btn"
//                         >
//                           {sub.sub_category_name} ➤
//                         </button>

//                         {products[sub.sub_category_id] && products[sub.sub_category_id].length > 0 && (
//                           <ul className="product-list">
//                             {products[sub.sub_category_id].map((prod) => (
//                               <li key={prod.product_id} className="product-item">
//                                 {prod.product_name}
//                               </li>
//                             ))}
//                           </ul>
//                         )}
//                       </li>
//                     ))}
//                   </ul>
//                 )}
//               </li>
//             ))}
//           </ul>
//         </div>
//       )}
//     </div>
//     <div>
//       <p>HOme</p>
//     </div>
//     <div>
//       <p>HOme</p>
//     </div>
//     <div>
//       <p>HOme</p>
//     </div>
//     </div>
//   );
// };

// export default Navbar;
