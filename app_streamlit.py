import streamlit as st
import requests

API_URL = "http://localhost:8000"  # Change si besoin

st.title("Gestion des Films et Acteurs")

# --- Formulaire création film ---
st.header("Ajouter un film")

with st.form("create_movie_form"):
    title = st.text_input("Titre du film")
    year = st.number_input("Année", min_value=1900, max_value=2100, value=2023)
    director = st.text_input("Réalisateur")

    # Saisie dynamique des acteurs
    actors = []
    nb_actors = st.number_input("Nombre d'acteurs", min_value=1, max_value=10, value=1)
    for i in range(nb_actors):
        actor_name = st.text_input(f"Nom acteur {i+1}", key=f"actor_{i}")
        actors.append({"actor_name": actor_name})

    submitted = st.form_submit_button("Créer le film")
    if submitted:
        # Nettoyage des acteurs vides
        actors_clean = [a for a in actors if a["actor_name"].strip() != ""]
        if not title or not director or not actors_clean:
            st.error("Merci de remplir tous les champs et au moins un acteur.")
        else:
            payload = {
                "title": title,
                "year": year,
                "director": director,
                "actors": actors_clean,
            }
            resp = requests.post(f"{API_URL}/movies/", json=payload)
            if resp.status_code == 200 or resp.status_code == 201:
                st.success("Film créé avec succès !")
            else:
                st.error(f"Erreur lors de la création: {resp.text}")

# --- Afficher film aléatoire ---
st.header("Film aléatoire")

if st.button("Récupérer un film aléatoire"):
    resp = requests.get(f"{API_URL}/movies/random/")
    if resp.status_code == 200:
        movie = resp.json()
        st.subheader(f"{movie['title']} ({movie['year']})")
        st.write(f"Réalisateur : {movie['director']}")
        st.write("Acteurs :")
        for actor in movie.get("actors", []):
            st.write(f"- {actor['actor_name']}")

        # Bouton pour générer résumé IA
        if st.button("Générer résumé IA", key="generate_summary"):
            summary_resp = requests.post(f"{API_URL}/generate_summary/", json={"movie_id": movie["id"]})
            if summary_resp.status_code == 200:
                summary = summary_resp.json().get("summary_text", "")
                st.markdown("### Résumé généré :")
                st.write(summary)
            else:
                st.error(f"Erreur lors de la génération du résumé: {summary_resp.text}")

    else:
        st.error("Aucun film trouvé ou erreur serveur.")
