import { Outlet, useLocation } from "react-router-dom";
import CustomerHeader from "../Customer/CustomerHeader/CustomerHeader";
import "./CustomerLayout.css";
import CarouselLanding from "../Customer/CustomerCarousel/CustomerCarousel";

const CustomerLayout = () => {
  const location = useLocation();

  const hideHeader =
  location.pathname === "/customer-login" ||
  location.pathname.startsWith("/verify-email/");


  return (
    <div className="customer-layout">
      {!hideHeader && <CustomerHeader />}
      <Outlet />
    </div>
  );
};

export default CustomerLayout;