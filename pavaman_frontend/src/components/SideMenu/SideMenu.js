import React from "react";
import { Link, useNavigate } from "react-router-dom";
import "../SideMenu/SideMenu.css";
import { MdDashboard } from "react-icons/md";
import { BiLogOut } from "react-icons/bi";
import { FaBoxOpen } from "react-icons/fa6";
import { TbTruckDelivery } from "react-icons/tb";
import { IoMdPeople } from "react-icons/io";
import { TbReportSearch } from "react-icons/tb";
import { RiDiscountPercentLine } from "react-icons/ri";
import { FaStar } from "react-icons/fa";

const SideMenu = ({ setIsAuthenticated }) => {
    const navigate = useNavigate();
    const handleLogout = () => {
        sessionStorage.clear();
        localStorage.clear();
        setIsAuthenticated(false);

        navigate("/admin-login");
    };
    return (

        <div className="sidemenu">
            <Link to='/dashboard' className="sidemenu-item">
                <MdDashboard className="sidemenu-img" />
                <span className="sidemenu-label">Dashboard</span>
            </Link>
            <Link to="/view-categories" className="sidemenu-item">
                <FaBoxOpen className="sidemenu-img" />
                <span className="sidemenu-label">Products</span>
            </Link>
            <Link to="/reports" className="sidemenu-item">
                <TbReportSearch className="sidemenu-img" />

                <span className="sidemenu-label">Reports</span>
            </Link>


            <Link to="/customers" className="sidemenu-item ">
                <IoMdPeople className="sidemenu-img" />

                <span className="sidemenu-label">Customers</span>
            </Link>

            <Link to="/discounts" className="sidemenu-item ">
                <RiDiscountPercentLine className="sidemenu-img" />

                <span className="sidemenu-label">Discounts</span>
            </Link>
            <Link to="/orders" className="sidemenu-item ">

                <TbTruckDelivery className="sidemenu-img" />
                <span className="sidemenu-label">Orders</span>
            </Link>
            <Link to="/ratings" className="sidemenu-item ">

                <FaStar className="sidemenu-img" />
                <span className="sidemenu-label">Ratings</span>
            </Link>

            <Link to="/admin-login" className="sidemenu-item logout-link" onClick={handleLogout}>
                <BiLogOut className="sidemenu-img" />
                <span className="sidemenu-label">Logout</span>
            </Link>
        </div>

    );
};

export default SideMenu;
