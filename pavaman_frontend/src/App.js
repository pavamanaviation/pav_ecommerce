import "./App.css";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";

import Header from "./components/Header/Header";
import SideMenu from "./components/SideMenu/SideMenu";
import SignIn from "./components/SignIn/Signin";
import AdminRoutes from "./pages/routes/AdminRoutes.js";
import CustomerRoutes from "./pages/routes/CustomerRoutes";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [products, setProducts] = useState([]);

  useEffect(() => {
    const adminData = sessionStorage.getItem("adminData");
    if (adminData) {
      setIsAuthenticated(true);
    }
  }, []);

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route
            path="/admin-login"
            element={isAuthenticated ? <Navigate to="/dashboard" /> : <SignIn setIsAuthenticated={setIsAuthenticated} />}
          />
          
          <Route path="/*" element={<CustomerRoutes />} />
          
          {!isAuthenticated && <Route path="/admin/*" element={<Navigate to="/admin-login" />} />}
        </Routes>

        {isAuthenticated && (
          <>
            <Header setIsAuthenticated={setIsAuthenticated} setCategories={setCategories} setSubcategories={setSubcategories} setProducts={setProducts} />
            <div className="main-layout">
              <div className="side-menu-container">
                <SideMenu setIsAuthenticated={setIsAuthenticated} />
              </div>
              <div className="content">
                <AdminRoutes
                  categories={categories}
                  setCategories={setCategories}
                  subcategories={subcategories}
                  setSubcategories={setSubcategories}
                  products={products}
                  setProducts={setProducts}
                />
              </div>
            </div>
          </>
        )}
      </div>
    </Router>
  );
}

export default App;
