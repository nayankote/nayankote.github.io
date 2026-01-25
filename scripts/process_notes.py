#!/usr/bin/env python3
"""
Process raw notes: generate embeddings, cluster, and compute connections.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False

# Configuration
MIN_NOTES_FOR_CLUSTERING = 10
MIN_CLUSTER_SIZE = 3
SIMILARITY_THRESHOLD = 0.5
MAX_CONNECTIONS_PER_NOTE = 5
MODEL_NAME = "all-MiniLM-L6-v2"

# Paths
REPO_ROOT = Path(__file__).parent.parent
NOTES_RAW = REPO_ROOT / "notes" / "notes_raw.json"
NOTES_PROCESSED = REPO_ROOT / "notes" / "notes_processed.json"
CLUSTER_LABELS = REPO_ROOT / "notes" / "cluster_labels.json"


def load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2))


def generate_embeddings(texts: list[str], model: SentenceTransformer) -> np.ndarray:
    """Generate embeddings for a list of texts."""
    return model.encode(texts, show_progress_bar=False)


def cluster_notes(embeddings: np.ndarray) -> np.ndarray:
    """Cluster embeddings using HDBSCAN. Returns cluster labels (-1 = noise)."""
    if not HDBSCAN_AVAILABLE or len(embeddings) < MIN_NOTES_FOR_CLUSTERING:
        return np.zeros(len(embeddings), dtype=int)

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=2,
        metric="euclidean"
    )
    labels = clusterer.fit_predict(embeddings)
    return labels


def generate_cluster_label(texts: list[str]) -> str:
    """Generate a simple label from the most common words in cluster texts."""
    all_words = []
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                  "being", "have", "has", "had", "do", "does", "did", "will",
                  "would", "could", "should", "may", "might", "must", "shall",
                  "can", "to", "of", "in", "for", "on", "with", "at", "by",
                  "from", "as", "into", "through", "during", "before", "after",
                  "above", "below", "between", "under", "again", "further",
                  "then", "once", "here", "there", "when", "where", "why",
                  "how", "all", "each", "few", "more", "most", "other", "some",
                  "such", "no", "nor", "not", "only", "own", "same", "so",
                  "than", "too", "very", "just", "i", "me", "my", "myself",
                  "we", "our", "you", "your", "he", "him", "his", "she", "her",
                  "it", "its", "they", "them", "their", "what", "which", "who",
                  "this", "that", "these", "those", "am", "and", "but", "if",
                  "or", "because", "until", "while", "about", "against"}

    for text in texts:
        words = text.lower().split()
        words = [w.strip(".,!?;:'\"()[]{}") for w in words]
        words = [w for w in words if w and w not in stop_words and len(w) > 2]
        all_words.extend(words)

    if not all_words:
        return "miscellaneous"

    counter = Counter(all_words)
    top_words = [word for word, _ in counter.most_common(3)]
    return " ".join(top_words)


def compute_connections(embeddings: np.ndarray, note_ids: list[str]) -> dict:
    """Compute similarity-based connections for each note."""
    similarities = cosine_similarity(embeddings)
    connections = {}

    for i, note_id in enumerate(note_ids):
        sims = [(note_ids[j], similarities[i][j])
                for j in range(len(note_ids)) if i != j]

        sims = [(nid, sim) for nid, sim in sims if sim >= SIMILARITY_THRESHOLD]
        sims.sort(key=lambda x: x[1], reverse=True)

        connections[note_id] = [
            {"target_id": nid, "similarity": round(float(sim), 3)}
            for nid, sim in sims[:MAX_CONNECTIONS_PER_NOTE]
        ]

    return connections


def main():
    print("Loading raw notes...")
    raw_data = load_json(NOTES_RAW)
    notes = raw_data.get("notes", [])

    if not notes:
        print("No notes to process.")
        save_json(NOTES_PROCESSED, {
            "notes": [],
            "clusters": [],
            "last_processed": datetime.utcnow().isoformat() + "Z"
        })
        return

    print(f"Processing {len(notes)} notes...")

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("Generating embeddings...")
    texts = [note["text"] for note in notes]
    embeddings = generate_embeddings(texts, model)

    print("Clustering...")
    cluster_labels = cluster_notes(embeddings)

    custom_labels = load_json(CLUSTER_LABELS)

    unique_clusters = set(cluster_labels)
    clusters = []
    for cluster_id in unique_clusters:
        cluster_id = int(cluster_id)
        cluster_texts = [texts[i] for i, c in enumerate(cluster_labels) if c == cluster_id]
        auto_label = generate_cluster_label(cluster_texts)
        clusters.append({
            "id": cluster_id,
            "auto_label": auto_label,
            "custom_label": custom_labels.get(str(cluster_id)),
            "note_count": len(cluster_texts)
        })

    print("Computing connections...")
    note_ids = [note["id"] for note in notes]
    connections = compute_connections(embeddings, note_ids)

    processed_notes = []
    for i, note in enumerate(notes):
        processed_notes.append({
            "id": note["id"],
            "text": note["text"],
            "subject": note.get("subject"),
            "timestamp": note["timestamp"],
            "source": note.get("source", "unknown"),
            "cluster_id": int(cluster_labels[i]),
            "connections": connections[note["id"]]
        })

    output = {
        "notes": processed_notes,
        "clusters": clusters,
        "last_processed": datetime.utcnow().isoformat() + "Z"
    }
    save_json(NOTES_PROCESSED, output)
    print(f"Done! Processed {len(notes)} notes into {len(clusters)} clusters.")


if __name__ == "__main__":
    main()
