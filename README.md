Gurgaon Realty Intelligence 🏙️

Gurgaon Realty Intelligence is an enterprise-grade real estate valuation, analytics, and recommendation platform. It provides transparent, data-driven pricing intelligence for the highly volatile Gurgaon (Haryana) real estate market, utilizing optimized Extreme Gradient Boosting (XGBoost) and hybrid Cosine Similarity engines.
🌟 Key Features

    Real-Time Price Predictor: Predicts accurate property values (± ₹0.22 Cr MAE) based on 12 key attributes (BHK, Sector, Built-up Area, Luxury/Floor Categories, etc.).

    Interactive Market Analytics: A dark-themed, zero-refresh Single-Page Application (SPA) dashboard featuring Plotly.js Geomaps, scatter plots, and dynamically rendered Matplotlib distribution distributions.

    Smart Recommender System:

        Radius Search: Finds localities within a specified distance using Euclidean geospatial matrices.

        Apartment Matcher: Uses a multi-factor cosine similarity matrix (weighing location, facilities, and pricing profiles) to recommend structurally and visually similar properties.

🛠️ Tech Stack

    Frontend: HTML5, Tailwind CSS, Plotly.js, Vanilla JavaScript (Fetch API).

    Backend: Python, Flask, RESTful APIs, Gunicorn (for production WSGI).

    Machine Learning Engine: Scikit-Learn, XGBoost, Optuna (Hyperparameter Tuning), SciPy.

    Data Engineering: Pandas, NumPy, 99acres Web Scrapers.

    Deployment: Render (Cloud-native Linux Container).

📂 Project Structure
Plaintext

gurgaon_real_estate/
│
├── app.py                  # Main Flask Backend & API Gateway
├── requirements.txt        # Python dependencies for Render
├── data/                   # Pickled ML artifacts and CSV datasets
│   ├── df.pkl              # Cleaned property dataframe
│   ├── pipeline.pkl        # XGBoost regression pipeline
│   ├── data_viz1.csv       # EDA and Analytics dataset
│   ├── feature_text.pkl    # TF-IDF Wordcloud text 
│   ├── location_distance.pkl # Pairwise spatial distance matrix
│   └── cosine_sim[1-3].pkl # Weighted Cosine Similarity matrices
│
├── templates/
│   └── index.html          # Main Frontend Dashboard HTML (Tailwind UI)
│
└── static/
    └── js/
        └── main.js         # Frontend JavaScript Logic & Plotly rendering

🚀 Local Installation & Setup

    Clone the repository:
    Bash

    git clone https://github.com/yourusername/gurgaon-realty-intelligence.git
    cd gurgaon-realty-intelligence

    Create a virtual environment (Recommended):
    Bash

    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate

    Install dependencies:
    Bash

    pip install -r requirements.txt

    Run the application locally:
    Bash

    python app.py

    The app will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000)

☁️ Deployment (Render)

This application is configured for seamless deployment on Render.

    Create a new Web Service on Render and link this GitHub repository.

    Set the environment configurations:

        Environment: Python 3

        Build Command: pip install -r requirements.txt

        Start Command: gunicorn app:app

    Click Deploy. The app will automatically build the environment and serve the Flask application via Gunicorn.

🧠 Machine Learning Details

    Data Collection: Automated Python scraping scripts aggregating live data from 99acres and historical transaction records.

    Feature Selection: Filtered down to 12 optimal features using Boruta and Recursive Feature Elimination (RFE) to eliminate multicollinearity.

    Model Optimization: The base regressor is xgboost.XGBRegressor, hyper-tuned over 150 trials using Optuna. Target variables were log-transformed (np.log1p) to mitigate the right-skewness of luxury property prices, resulting in an operational Mean Absolute Error (MAE) of ₹0.22 Crore.

📝 License

Distributed under the MIT License. See LICENSE for more information.
