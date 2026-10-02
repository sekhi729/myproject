from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Cake


def get_cake_text(cake):
    """
    Combine important cake information
    into searchable text.
    """

    return " ".join([
        cake.name or "",
        cake.description or "",
        cake.ingredients or "",
        cake.recipe or "",
        cake.category.name if cake.category else ""
    ])


def get_similar_cakes(cake_id, limit=6):

    cakes = list(
        Cake.objects.filter(
            available=True
        ).select_related("category")
    )

    if not cakes:
        return Cake.objects.none()

    target_cake = next(
        (cake for cake in cakes if cake.id == cake_id),
        None
    )

    if not target_cake:
        return Cake.objects.none()

    documents = [
        get_cake_text(cake)
        for cake in cakes
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    tfidf_matrix = vectorizer.fit_transform(documents)

    target_index = cakes.index(target_cake)

    similarity_scores = cosine_similarity(
        tfidf_matrix[target_index],
        tfidf_matrix
    ).flatten()

    ranked_indices = similarity_scores.argsort()[::-1]

    recommended_cakes = []

    for index in ranked_indices:

        cake = cakes[index]

        if cake.id == cake_id:
            continue

        recommended_cakes.append(cake)

        if len(recommended_cakes) >= limit:
            break

    return recommended_cakes