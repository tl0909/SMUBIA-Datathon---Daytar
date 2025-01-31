# -*- coding: utf-8 -*-
"""Code.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1vvGYjx46kISWqy14B_7T9MBn7-4Ws5Ol

# **Import Library**
"""

!pip install pycountry
!pip install geopandas

import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
import spacy
import pycountry
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import MinMaxScaler
from textblob import TextBlob
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import geopandas as gpd
import matplotlib.pyplot as plt

# Load spaCy's English model
nlp = spacy.load('en_core_web_sm')

nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('punkt')
nltk.download('vader_lexicon')

stop_words = set(stopwords.words('english'))

# Note: Remove this if you are not using Google Drive
from google.colab import drive
drive.mount('/content/drive')

"""# **Upload Data**"""

# Note: You need to update the file paths in the code to match your local environment
source1 = '/content/drive/My Drive/Datathon(SMUISD)/news_excerpts_parsed.xlsx'
source2 = '/content/drive/My Drive/Datathon(SMUISD)/wikileaks_parsed.xlsx'

news_excerpts = pd.read_excel(source1)
wikileaks = pd.read_excel(source2)

# Display the first few rows
print(news_excerpts.head())
print(wikileaks.head())

"""# **Data Cleaning**"""

## Combining the same pdf to the same text for wikileaks
combined_wikileaks = wikileaks.groupby('PDF Path', as_index=False).agg({
    'Text': ' '.join  # Concatenate text with a space
})

text_data1 = news_excerpts["Text"]
text_data2 = combined_wikileaks["Text"]

# Pre process the text
def preprocess_text(text):
    if pd.isna(text):  # Handle missing values
        return ""
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'\n|\r', ' ', text)  # Replace newline characters
    text = re.sub(r'[^a-zA-Z\s]', '', text)  # Remove special characters and numbers
    text = ' '.join(word for word in word_tokenize(text) if word not in stop_words)  # Remove stopwords
    return text
# Create a new data frame for processed text data
processed_text_data1 = pd.DataFrame()
processed_text_data2 = pd.DataFrame()
processed_text_data1['Text'] = text_data1
processed_text_data2['Text'] = text_data2
processed_text_data1['Text Processed'] = text_data1.apply(preprocess_text)
processed_text_data2['Text Processed'] = text_data2.apply(preprocess_text)

# Add Source Column to Identify Origin of the Text
processed_text_data1['Source'] = 'Articles'
processed_text_data2['Source'] = 'WikiLeaks'

# Combine both processed datasets
combined_data = pd.concat([
    processed_text_data1[['Source', 'Text Processed', 'Text']],
    processed_text_data2[['Source', 'Text Processed', 'Text']]
])

"""# **Data Processing**

**Predefined Keyword Classification**
"""

# Define Classification Logic
economic_keywords = ['economic', 'money', 'trade', 'investment', 'cash', 'payment', 'transaction', 'funds', 'theft', 'robbery', 'embezzlement', 'asset', 'valuable', 'gold', 'jewellery', 'bank', 'fraud', 'scam', 'embezzle', 'extortion', 'ransom']
violence_keywords = ["injury", "death", "discrimination", "assault", "murder", "homicide", "kidnap", "arson", "terror", "vandalism", "trespassing", "drug", "illegal", "data", "breach", "cyber"]

def classify_crime(text):
    # Check if any economic keyword exists in the text
    if any(keyword in text for keyword in economic_keywords):
        return 'Economic/Trade/Money-related'
    elif any(keyword in text for keyword in violence_keywords):
        return 'Non-money-related'
    else:
        return 'None'

combined_data['Crime_Type'] = combined_data['Text Processed'].apply(classify_crime)

# Print the counts
print(combined_data['Crime_Type'].value_counts())
print(combined_data[['Text', 'Crime_Type']].head())

"""**Extraction of Entities (Country)**"""

# Extracting Countries using spaCy and filtering with pycountry
# Function to find a country by name, alpha codes, or demonym
def find_country(entity):
    entity_lower = entity.lower()

    for country in pycountry.countries:
        # Check official name, common name, alpha codes
        if (
            entity_lower == country.name.lower() or
            entity_lower == getattr(country, 'official_name', '').lower() or
            entity_lower in [country.alpha_2.lower(), country.alpha_3.lower()]
        ):
            return country.name

        # Check demonyms (e.g., Indonesian → Indonesia)
        if hasattr(country, 'demonym') and entity_lower == country.demonym.lower():
            return country.name

    # If no match, return None
    return None

# Enhanced function using spaCy and pycountry
def extract_countries_spacy(text):
    doc = nlp(text)
    countries = set()

    for ent in doc.ents:
        if ent.label_ in ['GPE', 'NORP', 'LOC']:  # GPE, nationalities, or locations
            country_name = find_country(ent.text.strip())
            if country_name:
                countries.add(country_name)

    return ', '.join(sorted(countries)) if countries else 'None'

# Apply country extraction
combined_data['Countries'] = combined_data['Text'].apply(extract_countries_spacy)

# Display the results with extracted countries
print(combined_data[['Text', 'Crime_Type', 'Countries']])

"""**LinearSVC using Labelled Data to Predict 'None' Types**"""

# Feature Extraction with TfidfVectorizer
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)

# Separate training data (excluding "None") and data with "None" for later prediction
train_data = combined_data[combined_data['Crime_Type'] != 'None']
none_data = combined_data[combined_data['Crime_Type'] == 'None']

# **Step 1: Balance the Dataset by Undersampling**
# Find the smallest class count
min_class_count = train_data['Crime_Type'].value_counts().min()

# Randomly sample an equal number of rows from each class
balanced_data = train_data.groupby('Crime_Type').apply(
    lambda x: x.sample(min_class_count, random_state=42)
).reset_index(drop=True)

# Check class distribution
print("Balanced class distribution:")
print(balanced_data['Crime_Type'].value_counts())

# **Step 2: Train the Model**
# Split the balanced data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(
    balanced_data['Text Processed'], balanced_data['Crime_Type'],
    test_size=0.2, random_state=42
)

# Transform text data into TF-IDF features
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Define a function to tune the model
def tune_model(X, y):
    param_grid = {'C': [0.1, 1, 10], 'max_iter': [1000, 2000, 3000]}
    svc = LinearSVC(random_state=42)
    grid_search = GridSearchCV(estimator=svc, param_grid=param_grid, cv=3, verbose=2, n_jobs=-1)
    grid_search.fit(X, y)
    print(f"Best parameters found: {grid_search.best_params_}")
    return grid_search.best_estimator_

# Train the model with GridSearchCV
model = tune_model(X_train_vec, y_train)

# Evaluate on test data
y_pred = model.predict(X_test_vec)
print("Classification report on test data:")
print(classification_report(y_test, y_pred))

# **Step 3: Predict Crime Types for 'None' Data**
# Transform 'None' data using the same vectorizer
none_data_features = vectorizer.transform(none_data['Text Processed'])

# Predict labels for 'None' data
predicted_labels = model.predict(none_data_features)

# Assign predictions back to the original none_data
none_data.loc[:, 'Crime_Type'] = predicted_labels

# **Step 4: Update Combined Dataset with Predictions**
for index, none_row in none_data.iterrows():
    # Match by 'Text Processed' to update original combined data
    matching_rows = combined_data[combined_data['Text Processed'] == none_row['Text Processed']]
    if not matching_rows.empty:
        combined_index = matching_rows.index[0]
        combined_data.at[combined_index, 'Crime_Type'] = none_row['Crime_Type']

# Check the updated Crime_Type counts
print("Updated class distribution in the combined dataset:")
print(combined_data['Crime_Type'].value_counts())

print(combined_data.head())

"""**Sentiment Analysis**"""

# Analyse Sentiment using VADER on Cleaned Data

sia = SentimentIntensityAnalyzer()

# analyse_sentiment function
def analyse_sentiment(text):
  # Handles Empty Strings by Assignining them as Neutral
  if not text or text.strip() == "":
    return {"Positive":0.0, "Neutral":1.0, "Negative":0.0, "Compound":0.0, "Sentiment": "Neutral"}
  scores = sia.polarity_scores(text)
  # Extracts Overall Sentiment Score
  compound = scores['compound']
  if compound >= 0.05:
    sentiment = "Positive"
  elif compound <= -0.05:
    sentiment = "Negative"
  else:
    sentiment = "Neutral"
  # Classifies Sentiment based on above Threshold
  scores["Sentiment"] = sentiment
  return scores

# Apply on Combined Data
combined_data[['Positive', 'Neutral', 'Negative', 'Compound', 'Sentiment']] = combined_data['Text Processed'].apply(
  lambda x: pd.Series(analyse_sentiment(x)))

print(combined_data.head())

"""# **Analysis of Data**

**Aggregation and Normalisation of Data + Ranking of Countries**
"""

## Analysis
# List of related countries (to Singapore)
related_countries = ['Malaysia', 'Indonesia', 'Brunei', 'Thailand', 'Vietnam', 'Philippines', 'Myanmar', 'Cambodia', 'Laos', 'East Timor']

# Ensure the 'Countries' column is split into a list of countries
combined_data['Countries'] = combined_data['Countries'].apply(lambda x: x.split(', ') if isinstance(x, str) else [])

# Now 'Countries' is a list for each row, and you can continue processing
threat_scores_money = {}
threat_scores_nomoney = {}

def append_threat_score(countriesfunc, countryfunc, score, dictionary):
    if countryfunc == 'None' or countryfunc == 'Singapore':
        return dictionary
    if countryfunc not in dictionary:
        dictionary[countryfunc] = 0
    if 'Singapore' in countriesfunc:
        dictionary[countryfunc] += score
    elif country in related_countries:
        dictionary[countryfunc] += (score * 0.5)
    else:
        dictionary[countryfunc] += (score * 0.25)
    return dictionary

# Loop through each row of the combined_data DataFrame
for _, row in combined_data.iterrows():
    countries = row['Countries']  # List of countries
    compound_score = row['Compound']  # Sentiment score for the row
    crime_type = row['Crime_Type']

    for country in countries:  # Iterate over the countries in the list
        if crime_type == 'Economic/Trade/Money-related':
            threat_scores_money = append_threat_score(countries, country, compound_score, threat_scores_money)
        else:
            threat_scores_nomoney = append_threat_score(countries, country, compound_score, threat_scores_nomoney)

# Combine Money and NoMoney data into separate dataframes
df_money = pd.DataFrame(list(threat_scores_money.items()), columns=['Country', 'Economic/Trade/Money-related']).set_index('Country')
df_nomoney = pd.DataFrame(list(threat_scores_nomoney.items()), columns=['Country', 'Non-Money-related']).set_index('Country')

# Assuming df_money and df_nomoney have been calculated already
# Create the MinMaxScaler
scaler = MinMaxScaler(feature_range=(0, 1))  # Normalize between 0 and 1

# Normalize the Money and NoMoney columns
df_money['Risk_of_Economic-related_Crime'] = scaler.fit_transform(df_money[['Economic/Trade/Money-related']] * (-1))
df_nomoney['Risk_of_NonMoney-related_Crime'] = scaler.fit_transform(df_nomoney[['Non-Money-related']] * (-1))

# Merge the DataFrames for final output (combine raw and normalized data)
final_df = pd.merge(df_money[['Economic/Trade/Money-related', 'Risk_of_Economic-related_Crime']], df_nomoney[['Non-Money-related', 'Risk_of_NonMoney-related_Crime']],
                     left_index=True, right_index=True, how='outer')

# Add a "Ranking" column if necessary (e.g., based on Money or NoMoney scores)
final_df['Ranking_of_Highest_Risk_in_Economic-related_Crime'] = final_df['Risk_of_Economic-related_Crime'].rank(ascending=False)
final_df['Ranking_of_Highest_Risk_in_NonMoney-related_Crime'] = final_df['Risk_of_NonMoney-related_Crime'].rank(ascending=False)

print(final_df.head())

"""# **Examples on How Data can be Used**

**Choropleth Map**
"""

# Define a diverging colormap: Red to Yellow to Green
cmap = plt.cm.RdYlGn_r  # 'RdYlGn_r' reverses the red-yellow-green scale

# Load the world map
# Note: You need to update the file paths in the code to match your local environment
# and you need to download the world_map_file from https://www.naturalearthdata.com/downloads/110m-cultural-vectors/
world_map_file = "/content/drive/My Drive/Datathon(SMUISD)/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp"
world = gpd.read_file(world_map_file)

# Merge the world map with the Money data
world_money = world.set_index('NAME').join(df_money, how='left')

# Fill missing values with 0 (neutral color on the map)
world_money['Economic/Trade/Money-related'].fillna(0, inplace=True)

# Normalize the Money column for a better color balance
scaler = MinMaxScaler(feature_range=(0, 1))  # Adjust the range to [0, 1] for color scaling
world_money['Risk_of_Economic-related_Crime'] = scaler.fit_transform(world_money[['Economic/Trade/Money-related']] * (-1))

# Plot the Money data with the normalized values
plt.figure(figsize=(15, 10))
ax = world_money.plot(column='Risk_of_Economic-related_Crime', cmap=cmap, legend=True,
                      legend_kwds={'label': "Economic-related Crime Risk by Country",
                                   'orientation': "horizontal"})
plt.title('Normalized Money Data on World Map')
plt.show()

# Load the world map again for the NoMoney data plot
world_nomoney = world.set_index('NAME').join(df_nomoney, how='left')

# Fill missing values with 0 (neutral color on the map)
world_nomoney['Non-Money-related'].fillna(0, inplace=True)

# Normalize the NoMoney column for a better color balance
world_nomoney['Risk_of_NonMoney-related_Crime'] = scaler.fit_transform(world_nomoney[['Non-Money-related']] * (-1))

# Plot the NoMoney data with the normalized values
plt.figure(figsize=(15, 10))
ax = world_nomoney.plot(column='Risk_of_NonMoney-related_Crime', cmap=cmap, legend=True,
                        legend_kwds={'label': "NonMoney-related Crime Risk by Country",
                                     'orientation': "horizontal"})
plt.title('Normalized NoMoney Data on World Map')
plt.show()

"""**Bar Charts of Top 20 Countries with Highest Negative Sentiment with Relation to Singapore**"""

money_normalized_sentiment_scores = pd.DataFrame({
    'Country': df_money.index,
    'Risk_of_Economic-related_Crime': df_money['Risk_of_Economic-related_Crime'].fillna(0),
})

nomoney_normalized_sentiment_scores = pd.DataFrame({
    'Country': df_nomoney.index,
    'Risk_of_NonMoney-related_Crime': df_nomoney['Risk_of_NonMoney-related_Crime'].fillna(0)
})

# Set 'Country' as the index
money_normalized_sentiment_scores.set_index('Country', inplace=True)
nomoney_normalized_sentiment_scores.set_index('Country', inplace=True)

# Extract top 20 countries for Money Sentiment Normalized
top_20_money_sentiment = money_normalized_sentiment_scores.nlargest(20, 'Risk_of_Economic-related_Crime')

# Extract top 20 countries for NoMoney Sentiment Normalized
top_20_no_money_sentiment = nomoney_normalized_sentiment_scores.nlargest(20, 'Risk_of_NonMoney-related_Crime')

# Plotting the top 20 normalized sentiment values for both Money and NoMoney separately
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Plot top 20 Money Sentiment Normalized
top_20_money_sentiment.plot(kind='bar', stacked=True, ax=ax1, color='green')
ax1.set_title('Top 20 Countries with Highest Risk of Economic/Trade/Money-related Crime')
ax1.set_xlabel('Country')
ax1.set_ylabel('Normalized Sentiment Score')
ax1.set_xticklabels(top_20_money_sentiment.index, rotation=45)

# Plot top 20 NoMoney Sentiment Normalized
top_20_no_money_sentiment.plot(kind='bar', stacked=True, ax=ax2, color='red')
ax2.set_title('Top 20 Countries with Highest Risk of Non-money-related Crime')
ax2.set_xlabel('Country')
ax2.set_ylabel('Normalized Sentiment Score')
ax2.set_xticklabels(top_20_no_money_sentiment.index, rotation=45)

# Adjust layout for better spacing
plt.tight_layout()

# Display the charts
plt.show()

"""**Exporting of Data**

Note: You need to update the file paths in the code to match your local environment and uncomment the lines before running.
"""

# classified_combined_wikileaks_path = 'C:/Users/.../classified_news_excerpts.xlsx'
# classified_news_excerpts_path = 'C:/Users/.../classified_combined_wikileaks.xlsx'
# combined_classified_data_path = 'C:/Users/.../combined_classified_data.xlsx'
# country_threat_scores_with_rankings_path = 'C:/Users/.../country_threat_scores_with_rankings.xlsx'

# processed_text_data1.to_excel(classified_combined_wikileaks_path, index=False)
# processed_text_data2.to_excel(classified_news_excerpts_path, index=False)
# combined_data.to_excel(combined_classified_data_path, index=False)
# final_df.to_excel(country_threat_scores_with_rankings_path)