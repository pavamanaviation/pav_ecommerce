import React from "react";
import comingsoon from "../../assets/images/comingsoon.jpg";
import "../Dashboard/Dashboard.css"

const Dashboard = () => {
    return (
        <div>
            <img  src={comingsoon} className="dashboard-image"/>
            <p className="dashboard-text">Please go to Products pages</p>
        </div>
    );

 };
export default Dashboard;