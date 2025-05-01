import React from "react";
import "./SideComponent.css";

const Side = ({ categories, handleSubcategoryClick }) => {
  return (
    <div className="all-sidebar">
      <ul>
        {categories.map((cat) =>
          cat.sub_categoryies.map((sub) => (
            <li
              key={sub.id}
              onClick={() => handleSubcategoryClick(cat.category_name, sub.sub_category_name)}
              className="all-subcategory-item"
            >
              <img 
              src={sub.sub_category_image}
              className="side-image"/>


              <div className="side-text">{sub.sub_category_name}</div>
            </li>
          ))
        )}
      </ul>
    </div>
  );
};

export default Side;
