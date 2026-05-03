# Helper functions for analyzing text contents

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from collections import Counter
from geopy.geocoders import Nominatim
from collections import Counter

### Downloading the required resources for NLTK
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')

### Check_For_Relevance_Score Function:
def calculate_relevance_score(document, topic, keywords, logger=None):
    try:
        document = document.lower()
        topic = topic.lower()
        keywords = [keyword.lower() for keyword in keywords]

        document_tokens = nltk.word_tokenize(document)
        topic_tokens = nltk.word_tokenize(topic)

        stop_words = set(stopwords.words('english'))
        document_tokens = [token for token in document_tokens if token not in stop_words]
        topic_tokens = [token for token in topic_tokens if token not in stop_words]

        stemmer = PorterStemmer()
        document_tokens = [stemmer.stem(token) for token in document_tokens]
        topic_tokens = [stemmer.stem(token) for token in topic_tokens]

        relevance_score = 0
        keywords_found = []
        hydrogen_mentioned = document.count(topic)

        for keyword in keywords:
            keyword_tokens = nltk.word_tokenize(keyword)
            keyword_tokens = [token for token in keyword_tokens if token not in stop_words]
            keyword_tokens = [stemmer.stem(token) for token in keyword_tokens]
            keyword_count = Counter(keyword_tokens)

            matches = 0
            for i in range(len(document_tokens) - len(keyword_tokens) + 1):
                if all(document_tokens[i+j] == keyword_tokens[j] for j in range(len(keyword_tokens))):
                    matches += 1

            if matches > 0:
                keyword_score = matches * sum(keyword_count.values())
                keyword_score /= len(keyword_tokens)
                relevance_score += keyword_score
                keywords_found.append(keyword)

        return keywords_found, relevance_score, hydrogen_mentioned

    except Exception as e:
        if logger:
            logger.error(f"calculate_relevance_score failed: {e}")
        return [], 0, 0


def geolocation_detection(location, country, logger=None):
    geolocator = Nominatim(user_agent="geo_locator")
    try:
        location_info = geolocator.geocode(location, timeout=5, exactly_one=True, language="en", namedetails=True, addressdetails=True)
        if location_info and 'address' in location_info.raw and 'country' in location_info.raw['address']:
            country.append(location_info.raw['address']['country'])
    except Exception as e:
        if logger:
            logger.warning(f"geolocation_detection failed for {location}: {e}")
        return

def get_region(title, mainContent, nlp_model, logger=None):
    """
    Determine region based on geographical entities in title and content.
    """
    try:
        country = []
        
        # Process title with NLP if it's a string
        if isinstance(title, str) and title.strip():
            title_doc = nlp_model(title)
            for ent in title_doc.ents:
                if ent.label_ == "GPE":  # Geopolitical entity
                    location = ent.text
                    geolocation_detection(location, country, logger=logger)
        elif hasattr(title, 'ents'):  # Already a spaCy Doc
            for ent in title.ents:
                if ent.label_ == "GPE":
                    location = ent.text
                    geolocation_detection(location, country, logger=logger)
        
        # Check if we found North American countries from title
        if any(x in country for x in ['Canada', 'United States', 'Mexico']):
            return 'Can-US'
        elif country:
            return 'Others'
        
        # Process main content with NLP if it's a string
        if isinstance(mainContent, str) and mainContent.strip():
            # Limit content length for NLP processing (spaCy can be slow on very long texts)
            content_sample = mainContent[:5000]  # First 5000 characters
            content_doc = nlp_model(content_sample)
            for ent in content_doc.ents:
                if ent.label_ == "GPE":
                    location = ent.text
                    geolocation_detection(location, country, logger=logger)
        elif hasattr(mainContent, 'ents'):  # Already a spaCy Doc
            for ent in mainContent.ents:
                if ent.label_ == "GPE":
                    location = ent.text
                    geolocation_detection(location, country, logger=logger)
        
        # Final region determination
        if any(x in country for x in ['Canada', 'United States', 'Mexico']):
            return 'Can-US'
        elif country:
            return 'Others'
        else:
            logger.warning(f"Could not determine the region for this article. Please check it manually.")
            return 'Check'
            
    except Exception as e:
        if logger:
            logger.error(f"get_region failed: {e}")
        return 'Check'