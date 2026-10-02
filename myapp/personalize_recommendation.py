import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Cake, OrderItem


def get_personalized_recommendations(user, limit=6):

    purchased_cakes = Cake.objects.filter(
        orderitem__order__user=user
    ).distinct()

    if not purchased_cakes.exists():

        return Cake.objects.filter(
            available=True
        ).order_by("-id")[:limit]

    all_cakes = list(
        Cake.objects.filter(
            available=True
        ).select_related("category")
    )

    if not all_cakes:
        return []

    purchased_ids = set(
        purchased_cakes.values_list(
            "id",
            flat=True
        )
    )

    documents = [
        " ".join([
            cake.name or "",
            cake.description or "",
            cake.ingredients or "",
            cake.recipe or "",
            cake.category.name if cake.category else ""
        ])
        for cake in all_cakes
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    tfidf_matrix = vectorizer.fit_transform(documents)

    purchased_indices = [
        index
        for index, cake in enumerate(all_cakes)
        if cake.id in purchased_ids
    ]

    user_profile = np.asarray(
        tfidf_matrix[
        purchased_indices
    ].mean(axis=0)
    )

    similarity_scores = cosine_similarity(
        user_profile,
        tfidf_matrix
    ).flatten()

    ranked_indices = similarity_scores.argsort()[::-1]

    recommendations = []

    for index in ranked_indices:

        cake = all_cakes[index]

        if cake.id in purchased_ids:
            continue

        recommendations.append(cake)

        if len(recommendations) >= limit:
            break

    return recommendations