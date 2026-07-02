import os
import re
import json
import numpy as np
from sentence_transformers import SentenceTransformer

# Load model lazily
_model = None

def get_model():
    global _model
    if _model is None:
        # Load a small, fast model
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

class CatalogSearcher:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.catalog_path = os.path.join(base_dir, "resources", "cleaned_catalog.json")
        self.embeddings_path = os.path.join(base_dir, "resources", "embeddings.npy")
        
        # Load catalog
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            self.catalog = json.load(f)
            
        # Load or build embeddings
        if os.path.exists(self.embeddings_path):
            self.embeddings = np.load(self.embeddings_path)
        else:
            print("Embeddings not found. Building embeddings index...")
            self.build_index()
            
    def build_index(self):
        model = get_model()
        texts = []
        for item in self.catalog:
            name = item.get("name", "")
            desc = item.get("description", "")
            keys_str = ", ".join(item.get("keys", []))
            job_levels_str = ", ".join(item.get("job_levels", []))
            
            # Combine fields for high-quality embedding context
            text = f"Name: {name}\nDescription: {desc}\nKeys: {keys_str}\nJob Levels: {job_levels_str}"
            texts.append(text)
            
        self.embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        np.save(self.embeddings_path, self.embeddings)
        print(f"Saved {self.embeddings.shape[0]} embeddings to {self.embeddings_path}")
        
    def search(self, query: str, top_k: int = 15) -> list:
        """
        Semantic search using sentence transformers and cosine similarity.
        """
        model = get_model()
        query_embedding = model.encode(query, convert_to_numpy=True)
        
        # Calculate cosine similarity: dot product of normalized vectors
        norm_embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        norm_query = query_embedding / np.linalg.norm(query_embedding)
        
        similarities = np.dot(norm_embeddings, norm_query)
        
        # Sort indices descending
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            item = self.catalog[idx].copy()
            item["score"] = float(similarities[idx])
            results.append(item)
            
        return results

    def filter_by_keywords(self, query: str) -> list:
        """
        Fallback keyword matching for exact matches on name or key tech words.
        """
        query_lower = query.lower()
        matches = []
        for item in self.catalog:
            name_lower = item["name"].lower()
            desc_lower = item["description"].lower()
            
            # Simple keyword matching score
            score = 0
            if query_lower in name_lower:
                score += 2.0
            if query_lower in desc_lower:
                score += 1.0
                
            if score > 0:
                item_copy = item.copy()
                item_copy["score"] = score
                matches.append(item_copy)
                
        # Sort by score descending
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches

    def clean_product_name(self, name: str) -> str:
        # Remove (New), (adaptive), (v1.1), etc.
        name = re.sub(r'\s*\([^)]+\)', '', name)
        # Remove non-alphanumeric and non-space characters
        name = re.sub(r'[^a-zA-Z0-9\s-]', '', name)
        name = name.replace("-", " ")
        return name.strip().lower()

    def normalize_spelling(self, text: str) -> str:
        text = text.lower()
        text = text.replace("centre", "center")
        text = text.replace("behaviour", "behavior")
        text = text.replace("programme", "program")
        text = text.replace("organise", "organize")
        text = text.replace("organisation", "organization")
        text = text.replace("analyse", "analyze")
        return text

    def hybrid_search(self, query: str, top_k: int = 100) -> list:
        """
        High-recall hybrid search combining normalized spellings, query expansions,
        semantic search, and exact name keyword boosting.
        """
        query_lower = self.normalize_spelling(query)
        
        # 1. Expand query with abbreviations and roles
        expansions = []
        if "opq" in query_lower:
            expansions.append("occupational personality questionnaire opq32r")
        if "gsa" in query_lower:
            expansions.append("global skills assessment")
        if "svar" in query_lower:
            expansions.append("svar spoken english")
        if "dsi" in query_lower:
            expansions.append("dependability and safety instrument")
        if "mfs" in query_lower or "360" in query_lower:
            expansions.append("multi-rater feedback system mfs")
        if "hipo" in query_lower:
            expansions.append("hipo assessment report")
        if "cognitive" in query_lower or "aptitude" in query_lower or "reasoning" in query_lower or "g+" in query_lower:
            expansions.append("verify interactive inductive reasoning deductive reasoning numerical reasoning")
        if "java" in query_lower:
            expansions.append("java")
        if "excel" in query_lower:
            expansions.append("excel")
        if "word" in query_lower:
            expansions.append("word")
        if "typing" in query_lower:
            expansions.append("typing")
            
        # Programmatic domain-specific expansions
        if "rust" in query_lower or "c++" in query_lower or "golang" in query_lower or "coding" in query_lower or "programming" in query_lower:
            expansions.append("smart interview live coding linux programming general")
        if "admin" in query_lower or "clerical" in query_lower:
            expansions.append("microsoft word excel office administration clerical")
        if "healthcare" in query_lower or "medical" in query_lower or "patient" in query_lower:
            expansions.append("medical terminology healthcare")
        if "patient" in query_lower or "dependability" in query_lower or "safety" in query_lower or "security" in query_lower or "compliance" in query_lower:
            expansions.append("dependability and safety instrument dsi")
            
        expanded_query = query_lower + " " + " ".join(expansions)
        
        # 2. Get semantic matches
        model = get_model()
        query_embedding = model.encode(expanded_query, convert_to_numpy=True)
        
        # Calculate cosine similarity
        norm_embeddings = self.embeddings / np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        norm_query = query_embedding / np.linalg.norm(query_embedding)
        similarities = np.dot(norm_embeddings, norm_query)
        
        top_indices = np.argsort(similarities)[::-1][:80]
        
        semantic_matches = []
        for idx in top_indices:
            item = self.catalog[idx].copy()
            item["score"] = float(similarities[idx])
            semantic_matches.append(item)
            
        # 3. Improved tokenized keyword matches with stop words
        stop_words = {
            "we", "need", "hiring", "hire", "test", "assessment", "solution", "solutions", "for", "a", "an", "the", "in", 
            "of", "and", "to", "with", "is", "that", "this", "are", "they", "but", "not", "own", "don", "on", "their", "other", 
            "them", "your", "you", "he", "she", "it", "be", "as", "at", "by", "from", "has", "have", "in", "into", "its", "or", 
            "their", "then", "there", "these", "they", "this", "was", "will", "would", "about", "above", "after", "again", 
            "against", "all", "am", "any", "are", "aren't", "because", "been", "before", "being", "below", "between", "both", 
            "but", "by", "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", 
            "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", 
            "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", 
            "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", 
            "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", 
            "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", 
            "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", 
            "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", 
            "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", 
            "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", 
            "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", 
            "you've", "your", "yours", "yourself", "yourselves"
        }
        
        words = re.findall(r"\b[a-z0-9+-]+\b", query_lower)
        words = [w for w in words if w not in stop_words and len(w) > 1]
        
        keyword_matches = []
        for item in self.catalog:
            name_lower = item["name"].lower()
            cleaned_name = self.clean_product_name(item["name"])
            
            score = 0.0
            # Boost exact abbreviation matches
            for abbrev in ["opq", "svar", "dsi", "hipo", "mfs", "gsa"]:
                if abbrev in words and abbrev in name_lower:
                    score += 150.0
                    
            # Word matches in name
            for w in words:
                if w in name_lower:
                    if cleaned_name == w:
                        score += 200.0
                    elif re.search(r'\b' + re.escape(w) + r'\b', name_lower):
                        score += 50.0
                    else:
                        score += 20.0
                    
            if score > 0:
                item_copy = item.copy()
                item_copy["score"] = score
                keyword_matches.append(item_copy)
                
        keyword_matches.sort(key=lambda x: x["score"], reverse=True)
        
        # Combine and de-duplicate
        combined = []
        seen = set()
        
        # Prepend default assessments so they are never truncated
        default_recs = ["Occupational Personality Questionnaire OPQ32r", "SHL Verify Interactive G+"]
        for def_name in default_recs:
            for item in self.catalog:
                if item["name"] == def_name:
                    seen.add(def_name)
                    combined.append(item.copy())
                    break
                    
        for item in keyword_matches[:50] + semantic_matches:
            if item["name"] not in seen:
                seen.add(item["name"])
                combined.append(item)
                
        return combined[:top_k]
