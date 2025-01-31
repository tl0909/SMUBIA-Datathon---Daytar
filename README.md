# SMUBIA-Datathon---Daytar

# SMUISD Datathon - Crime Classification and Sentiment Analysis
This repository contains the solution for the SMUISD Datathon, where the goal is to classify crime-related news articles and WikiLeaks documents into various crime categories, perform sentiment analysis, and identify potential threat scores based on sentiment and country information. All code is contained in a single Python script.

### Colab Notebook Link:
https://colab.research.google.com/drive/1vvGYjx46kISWqy14B_7T9MBn7-4Ws5Ol?usp=sharing 

## Table of Contents
- Project Overview
- Dependencies
- How to Run
- Code Explanation
- Results

## Project Overview
This project aims to classify the text data from news articles and WikiLeaks documents into different categories related to crime (e.g., Economic/Trade-related or Non-money-related). Additionally, sentiment analysis is performed on each document to understand the tone of the content. Finally, countries mentioned within the documents are extracted, and threat scores are calculated based on sentiment and the country of origin, with a focus on regions related to Singapore.

### Key Features:
- Text Preprocessing: Tokenization, removal of stopwords, and cleaning text.
- Crime Classification: Using keyword-based classification to label text data into categories like 'Economic/Trade-related' and 'Non-money-related'.
- Sentiment Analysis: Using VADER (Valence Aware Dictionary and sEntiment Reasoner) for sentiment analysis to classify the sentiment of the text (Positive, Neutral, Negative).
- Country Extraction: Using spaCy and pycountry to extract country names from the text and match them with official country names.
- Threat Score Calculation: Calculate threat scores based on sentiment and the countries mentioned in the text.

## Dependencies
The project uses the following Python libraries:
- pandas
- nltk
- spacy
- pycountry
- scikit-learn
- textblob
- geopandas
- matplotlib
- for the variable world_map_file (you would need to download the world map from https://www.naturalearthdata.com/downloads/110m-cultural-vectors/)
  
## Data
The data for this project consists of two main sources:
- News Excerpts: A collection of news articles.
- WikiLeaks Excerpts: Data extracted from WikiLeaks documents.
Both datasets are provided in .xlsx format.

Note: You need to update the file paths in the code to match your local environment.

## Code Explanation
The code is structured as follows:
1. Imports
Libraries such as pandas, nltk, spaCy, textblob, and others are imported to handle text preprocessing, crime classification, sentiment analysis, country extraction, and data manipulation.
2. Text Preprocessing
The code cleans the text by converting it to lowercase, removing special characters, tokenizing, and eliminating stopwords using NLTK.
3. Crime Classification
The classification is done using predefined keywords for different crime categories (e.g., economic-related crimes). The code checks for the presence of these keywords in the text and assigns labels accordingly.
4. Sentiment Analysis
Sentiment is analyzed using VADER (Valence Aware Dictionary and sEntiment Reasoner). The code assigns sentiment labels (Positive, Negative, Neutral) to each document based on the VADER analysis.
5. Country Extraction
The code uses spaCy to perform Named Entity Recognition (NER) and extract country names. These names are then matched with official country names using pycountry.
6. Threat Score Calculation
The threat score is calculated based on the sentiment analysis and the countries mentioned in the text. Countries associated with higher threat levels, particularly in regions related to Singapore, receive higher weights in the score.
7. Results
The classified data, along with sentiment and threat scores, is saved in separate Excel files for further analysis.

## Results
The output consists of:
- A classified dataset that labels the documents based on crime type (Economic/Trade-related or Non-money-related).
- A sentiment analysis score for each document (Positive, Neutral, or Negative).
- Threat scores based on sentiment and the countries mentioned in the document.
- The final results are saved in Excel files and can be visualized to analyze patterns in crime categories and sentiment. (Note: You need to update the file paths in the code to match your local environment to export the files)
