import { Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "../../pages/Dashboard/Dashboard";
import AddCategory from "../../pages/AddCategory/AddCategory";
import EditCategory from "../../pages/EditCategory/EditCategory";
import ViewCategories from "../../pages/ViewCategories/ViewCategories";
import ViewSubcategories from "../../pages/ViewSubCategories/ViewSubCategories";
import AddSubCategory from "../../pages/AddSubCategory/AddSubCategory";
import AddProduct from "../../pages/AddProduct/AddProduct";
import ViewProducts from "../../pages/ViewProducts/ViewProducts";
import ViewProductDetails from "../../pages/ViewMoreProductDetails/ViewMoreProductDetails";
import AddSpecification from "../../pages/AddSpecifications/AddSpecifications";
import EditSpecification from "../../pages/EditSpecifications/EditSpecifications";
import EditSubcategory from "../../pages/EditSubCategory/EditSubCategory";
import EditProduct from "../../pages/EditProduct/EditProduct";
import Customer from "../AdminCustomerDashboard/AdminCustomerDashboard";
import Orders from "../AdminCustomerOrders/AdminCustomerOrders";
import Reports from "../AdminCustomerReports/AdminCustomerReports";
import PaidOrderDetails from "../AdminCustomerOrderViewDetails/AdminCustomerOrderViewDetails";
import AdminDiscountProducts from "../AdminDiscounts/AdminDiscounts";
import AdminAddDiscount from "../AdminDiscounts/AdminAddDiscounts";
import AdminRatings from "../AdminRatings/AdminRatings";

const AdminRoutes = ({ categories, setCategories, subcategories, setSubcategories, products, setProducts }) => {
  return (
    <Routes>
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/add-category" element={<AddCategory />} />
      <Route path="/edit-category" element={<EditCategory />} />
      <Route path="/view-categories" element={<ViewCategories categories={categories} setCategories={setCategories} setSubcategories={setSubcategories} />} />
      <Route path="/view-subcategories" element={<ViewSubcategories subcategories={subcategories} setSubcategories={setSubcategories} />} />
      <Route path="/add-subcategory" element={<AddSubCategory />} />
      <Route path="/view-products" element={<ViewProducts products={products} setProducts={setProducts} />} />
      <Route path="/add-product" element={<AddProduct />} />
      <Route path="/view-product-details" element={<ViewProductDetails />} />
      <Route path="/add-product-specifications" element={<AddSpecification />} />
      <Route path="/edit-product-specifications" element={<EditSpecification />} />
      <Route path="/edit-subcategory" element={<EditSubcategory />} />
      <Route path="/edit-product" element={<EditProduct />} />
      <Route path="*" element={<Navigate to="/dashboard" />} />
      <Route path="/customers" element={<Customer />} />
      <Route path="/orders" element={<Orders/>} />
      <Route path="/reports" element={<Reports/>} />
      <Route path="/admin-order-details/:orderId" element={<PaidOrderDetails />} />
      <Route path="/discounts" element={<AdminDiscountProducts />} />
      <Route path="/add-discount" element={<AdminAddDiscount />}/>
      <Route path="/ratings" element={<AdminRatings />}/>
    </Routes>
  );
};

export default AdminRoutes;