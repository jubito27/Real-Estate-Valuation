import os
import io
import base64
import pickle
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from flask import Flask, request, jsonify, render_template, Response
import matplotlib

matplotlib.use('Agg')
app = Flask(__name__)

# --- GLOBAL DARK THEME CONFIG ---
pio.templates.default = "plotly_dark"
plt.style.use('dark_background')
CARD_BG_COLOR = "#1e293b" # Matches Tailwind's bg-slate-800

# --- CONFIGURATION & DATA LOADING ---
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

df = pd.read_pickle(os.path.join(DATA_DIR, 'df.pkl'))
pipeline = pd.read_pickle(os.path.join(DATA_DIR, 'pipeline.pkl'))

new_df = pd.read_csv(os.path.join(DATA_DIR, 'data_viz1.csv'))
numeric_columns = ["price", "price_per_sqft", "built_up_area", "latitude", "longitude", "bedRoom"]
for col in numeric_columns:
    new_df[col] = pd.to_numeric(new_df[col], errors="coerce")

with open(os.path.join(DATA_DIR, 'feature_text.pkl'), 'rb') as f:
    feature_text = str(pickle.load(f))

location_df = pd.read_pickle(os.path.join(DATA_DIR, 'location_distance.pkl'))
cosine_sim1 = pd.read_pickle(os.path.join(DATA_DIR, 'cosine_sim1.pkl'))
cosine_sim2 = pd.read_pickle(os.path.join(DATA_DIR, 'cosine_sim2.pkl'))
cosine_sim3 = pd.read_pickle(os.path.join(DATA_DIR, 'cosine_sim3.pkl'))
cosine_sim_matrix = 0.5 * cosine_sim1 + 0.8 * cosine_sim2 + 1 * cosine_sim3

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/options', methods=['GET'])
def get_options():
    return jsonify({
        'sectors': sorted(df['sector'].dropna().unique().tolist()),
        'bedrooms': sorted(df['bedRoom'].dropna().unique().tolist()),
        'bathrooms': sorted(df['bathroom'].dropna().unique().tolist()),
        'balconies': sorted(df['balcony'].dropna().unique().tolist()),
        'property_age': sorted(df['agePossession'].dropna().unique().tolist()),
        'furnishing_type': sorted(df['furnishing_type'].dropna().unique().tolist()),
        'luxury_category': sorted(df['luxury_category'].dropna().unique().tolist()),
        'floor_category': sorted(df['floor_category'].dropna().unique().tolist()),
        'locations': sorted(location_df.columns.to_list()),
        'apartments': sorted(location_df.index.to_list()),
        'analytics_sectors': ["overall"] + new_df["sector"].dropna().unique().tolist()
    })

# --- 1. PRICE PREDICTOR API ---
@app.route('/api/predict', methods=['POST'])
def predict_price():
    data = request.json
    try:
        input_data = [[
            data['property_type'], data['sector'], float(data['bedrooms']), float(data['bathroom']),
            data['balcony'], data['property_age'], float(data['built_up_area']),
            float(data['servant_room']), float(data['store_room']), data['furnishing_type'],
            data['luxury_category'], data['floor_category']
        ]]
        columns = ['property_type', 'sector', 'bedRoom', 'bathroom', 'balcony', 'agePossession',
                   'built_up_area', 'servant room', 'store room', 'furnishing_type', 'luxury_category', 'floor_category']
        
        one_df = pd.DataFrame(input_data, columns=columns)
        base_price = np.expm1(pipeline.predict(one_df))[0]
        
        low = round(base_price - 0.22, 2)
        high = round(base_price + 0.22, 2)
        
        return jsonify({'status': 'success', 'low': low, 'high': high})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

# --- 2. ANALYTICS APIs ---
def apply_transparent_bg(fig):
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

@app.route('/api/analytics/geomap')
def analytics_geomap():
    try:
        # Group by sector and calculate mean
        group_df = new_df.groupby("sector")[["price", "price_per_sqft", "built_up_area", "latitude", "longitude"]].mean()
        
        # 1. Reset the index so 'sector' becomes a standard column (safer for Plotly)
        group_df = group_df.reset_index()
        
        # 2. Strictly drop NaNs across ALL columns used in the map to prevent ValueError
        group_df = group_df.dropna(subset=["latitude", "longitude", "built_up_area", "price_per_sqft"])
        
        # 3. Ensure sizes are greater than 0 (Mapbox crashes on 0 or negative sizes)
        group_df = group_df[group_df["built_up_area"] > 0]
        if not group_df.empty:

            fig = px.scatter_map(
                group_df,
                lat="latitude",
                lon="longitude",
                color="price_per_sqft",
                size="built_up_area",
                color_continuous_scale=px.colors.cyclical.IceFire,
                zoom=10,
                map_style="open-street-map",
                center={
                    "lat": group_df["latitude"].mean(),
                    "lon": group_df["longitude"].mean()
                },
                text=group_df.index,
                hover_name=group_df.index
            )
            
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            return Response(fig.to_json(), mimetype='application/json')
        
    except Exception as e:
        # If Python fails, return the actual error message as JSON so the frontend can read it
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/analytics/scatter')
def analytics_scatter():
    prop_type = request.args.get('property_type', 'flat')
    property_df = new_df[new_df["property_type"] == prop_type].dropna(subset=["built_up_area", "price", "bedRoom"])
    
    # render_mode="svg" prevents WebGL rendering failures in SPA tabs
    fig = px.scatter(
        property_df, x="built_up_area", y="price", color="bedRoom", 
        title=f"Area Vs Price ({prop_type})", render_mode="svg"
    )
    fig = apply_transparent_bg(fig)
    return Response(fig.to_json(), mimetype='application/json')

@app.route('/api/analytics/pie')
def analytics_pie():
    sector = request.args.get('sector', 'overall')
    if sector == "overall":
        pie_df = new_df.dropna(subset=["bedRoom"])
    else:
        pie_df = new_df[new_df["sector"] == sector].dropna(subset=["bedRoom"])
    fig = px.pie(pie_df, names="bedRoom", title=f"BHK Distribution ({sector})")
    fig = apply_transparent_bg(fig)
    return Response(fig.to_json(), mimetype='application/json')

@app.route('/api/analytics/boxplot')
def analytics_boxplot():
    bhk_price_df = new_df[new_df["bedRoom"] <= 4].dropna(subset=["bedRoom", "price"])
    fig = px.box(bhk_price_df, x="bedRoom", y="price", title="BHK Price Range")
    fig = apply_transparent_bg(fig)
    return Response(fig.to_json(), mimetype='application/json')

@app.route('/api/analytics/wordcloud')
def analytics_wordcloud():
    # Use exact Tailwind card color for the background
    wordcloud = WordCloud(width=800, height=400, background_color=CARD_BG_COLOR, colormap="Pastel1", stopwords={"s"}, min_font_size=10).generate(feature_text)
    img = io.BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)
    encoded = base64.b64encode(img.getvalue()).decode('utf-8')
    return jsonify({'image': encoded})

@app.route('/api/analytics/distplot')
def analytics_distplot():
    house_prices = new_df[new_df["property_type"] == "house"]["price"].dropna()
    flat_prices = new_df[new_df["property_type"] == "flat"]["price"].dropna()
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Match Tailwind Dark Background exactly
    fig.patch.set_facecolor(CARD_BG_COLOR)
    ax.set_facecolor(CARD_BG_COLOR)
    
    sns.histplot(house_prices, kde=True, stat="density", label="House", ax=ax, element="step", color="#818cf8")
    sns.histplot(flat_prices, kde=True, stat="density", label="Flat", ax=ax, element="step", color="#34d399")
    ax.legend()
    ax.set_xlabel("Price (Cr)")
    ax.set_ylabel("Density")
    ax.set_title("Property Type Price Distribution")
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    img.seek(0)
    encoded = base64.b64encode(img.getvalue()).decode('utf-8')
    return jsonify({'image': encoded})

# --- 3. RECOMMENDER APIs ---
@app.route('/api/recommend/search', methods=['POST'])
def search_location():
    data = request.json
    loc = data.get('location')
    radius = float(data.get('radius'))
    
    result_ser = location_df[location_df[loc] < radius*1000][loc].sort_values()
    results = [{"name": str(k), "distance": round(v/1000, 1)} for k, v in result_ser.items()]
    return jsonify({'status': 'success', 'results': results})

@app.route('/api/recommend/apartments', methods=['POST'])
def recommend_apartments():
    data = request.json
    property_name = data.get('apartment')
    top_n = 5
    
    try:
        sim_scores = list(enumerate(cosine_sim_matrix[location_df.index.get_loc(property_name)]))
        sorted_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        top_indices = [i[0] for i in sorted_scores[1:top_n + 1]]
        top_scores = [round(i[1], 4) for i in sorted_scores[1:top_n + 1]]
        top_properties = location_df.index[top_indices].tolist()
        
        results = [{"property": p, "score": s} for p, s in zip(top_properties, top_scores)]
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5000)