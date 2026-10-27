## 🛒 UrbanCart: E-commerce Analytics & CLV Optimization

## Project Title : Omni-channel Customer Analytics & Revenue Optimization for "UrbanCart" E-commerce.

## 📌 Project Overview
UrbanCart is a mid-sized e-commerce retailer experiencing 25% YoY growth but facing declining customer retention (from 45% to 32% over 3 years). 
They need a comprehensive analytics solution to understand customer behavior across web, mobile app, and physical stores.
The objective of this project is to build a comprehensive analytics solution to:
•	Identify at-risk customers
•	Improve marketing ROI
•	Increase Customer Lifetime Value (CLV) by 15%
•	Enable data-driven decision-making
The solution integrates structured and semi-structured data, builds a scalable data warehouse, applies predictive analytics models, and develops executive dashboards for strategic decision-making.
Technologies used:
•	Database – PostgreSQL , MongoDB
•	Programming - Python (ETL & Analytics)
•	Data Warehouse - PostgreSql
•	Visualization - Microsoft Power BI


## 🎯 Business Problem
UrbanCart faces the following challenges:
•	Declining retention rate
•	Increasing customer acquisition cost
•	Inefficient marketing spend allocation
•	Lack of unified customer analytics system
The business requires a data-driven framework to understand customer behavior and improve long-term revenue growth.

## 🛠️ Tech Stack
Database: PostgreSQL, MongoDB
ETL Pipeline: Python (Pandas)
Data Warehouse: PostgreSQL (Star Schema)
Analytics: SQL + Python
Visualization: Power BI

## ⚙️ Project Architecture
Data Sources → ETL Pipeline → Data Warehouse → Analytics → Dashboard
(PostgreSQL + MongoDB) → (Python) → (PostgreSQL) → (SQL/Python) → (Power BI)

## 📊 Dataset
5,000 Customers
25,000 Orders
500 Products
30,000 Web Sessions
50 Marketing Campaigns

## 🔄 ETL Pipeline
Extract data from PostgreSQL & MongoDB
Clean & transform data using Python
Handle missing values & duplicates
Load into PostgreSQL Data Warehouse
Incremental data loading

## 🧱 Data Warehouse Design
Fact Table: fact_orders
Dimension Tables:
dim_customers
dim_products
dim_date
dim_campaign

## 📈 Analytics Performed

## 🔹 RFM Segmentation
RFM Analysis is a customer segmentation technique used in marketing and analytics to identify valuable customers based on purchasing behavior.
Customer segmentation is a data analysis technique used to divide customers into meaningful groups based on their purchasing behavior.
In this project, RFM analysis (Recency, Frequency, Monetary) is used to identify high-value customers, loyal customers, and customers at risk of churn. 
RFM analysis helps businesses understand customer engagement and purchasing patterns, enabling more effective marketing strategies and personalized campaigns

## 🔹 Customer Lifetime Value (CLV)
Customer Lifetime Value (CLV) Prediction Model is a predictive analytical model used to estimate the total revenue a customer is expected to generate for a 
business during their entire relationship with the company.
A Customer Lifetime Value (CLV) Prediction Model is a predictive analytics technique that estimates the future financial value of customers based on their historical purchasing behavior.
Formula for calculate CLV:-
CLV=Average Order Value×Purchase Frequency×Customer Lifespan

Average Order Value = average money spent per order
Purchase Frequency = Number of purchase per year
Customer Lifespan = Duration of customer stays active

## 🔹 Cohort Analysis
Cohort analysis groups customers based on their first purchase month and tracks their behavior over time.
A cohort is a group of customers who share a common event in a specific time period.
Cohort analysis is to analyze customer retention behavior over time by grouping customers based on their first purchase month.
This analysis helps identify patterns in repeat purchases and customer engagement.
The analysis was performed using the ORDERS_FACT table from the UrbanCart database.
The following tools were used for cohort analysis:
1.Python – Data Analysis
2.Pandas – Data Manipulation
3.Matplotlib - Visualization
4.Seaborn - Cohort heatmap visualization
5.PostgreSQL - Data storage

## 🔹 Association Rules
The goal of association rules is to discover relationships between products purchased in the same.
Identify frequently purchased product combinations in the UrbanCart dataset. By applying association rule mining,
we can discover relationships between products and recommend items that customers are likely to purchase together.


## 📊 Power BI Dashboards

## 🔹 Customer Analytics Executive Dashboard

![Executive Dashboard](images/Executive%20Dashboard.png)

The Executive Dashboard provides a high-level overview of business performance.

## Key Metrics:
•	Monthly Recurring Revenue (MRR)

•	Customer Acquisition Cost (CAC)

•	Customer Lifetime Value (CLV)

•	Retention Rate

•	Churn Percentage

## Insights:
•	Helps stakeholders quickly assess overall business health

•	Identifies trends in revenue and customer retention


## 🔹 Customer Segmentation Matrix (RFM Analysis) 

![RFM Analysis](images/RFM%20Analysis.png)

This dashboard segments customers based on Recency, Frequency, and Monetary value.

## Key Segments:
•	Champions

•	Loyal Customers

•	At Risk Customers

•	Lost Customers

## Insights:
•	Enables targeted marketing campaigns

•	Helps improve customer retention strategies


## 🔹 Churn Prediction Dashboard 

![Churn Prediction Dashboard](images/Churn%20Prediction%20Dashboard.png)

This dashboard focuses on identifying customers at risk of churn.

## Key Features:
•	Customer segmentation (High, Medium, Low Risk)

•	Churn distribution visualization

•	Detailed customer-level data

## Insights:
•	Helps identify high-risk customers

•	Enables targeted retention strategies


## 🔹 Marketing Attribution Dashboard 

![Marketing Attribution Dashboard](images/Marketing%20Atrribution%20Dashboard.png)


This dashboard analyse marketing performance across different channels.

## Key Metrics:
•	Total Revenue

•	Marketing Spend

•	Conversions

•	Return on Investment (ROI)

## Insights:
•	Identifies most effective marketing channels

•	Helps optimize marketing budget allocation


## 🔹 Product Recommendation Dashboard 

![Product Recommendation Dashboard](images/Product%20Reccomdation%20dashboard.png)

This dashboard provides insights into product performance and customer preferences.

## Key Features:
•	Revenue by product category

•	Customer segmentation by category

•	Product-level performance metrics

## Insights:
•	Helps identify top-performing products

•	Supports cross-selling and upselling strategies



## 💡 Key Insights
Top customers generate most revenue

High churn after initial purchases

Some marketing channels perform better than others

Repeat customers drive higher profitability

## 📈 Business Impact
Improved customer targeting

Better marketing budget allocation

Increased customer retention

Data-driven decision making

## 📂 Project Structure
UrbanCart/

│── data/

│── etl/

│── sql/

│── dashboards/

│── notebooks/

│── docs/

## ▶️ How to Run
Setup PostgreSQL database

Load datasets

Run ETL scripts (Python)

Build data warehouse tables

Connect Power BI to PostgreSQL

Open dashboard


## 👩‍💻 Author
Kavya Rathod

Aspiring Data Analyst


## 🔗 Connect with Me
GitHub: https://github.com/kavyarathod05


## 🧾 Conclusion
This project shows how data analytics can help improve customer retention, increase revenue, and support better business decisions in e-commerce.


