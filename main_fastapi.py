from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
import models, schemas
from database import SessionLocal, engine, Base
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
import os

# Création des tables dans la base de données
Base.metadata.create_all(bind=engine)

# Instance de l'application FastAPI
app = FastAPI()

# Dépendance pour obtenir une session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint pour créer un film avec ses acteurs
@app.post("/movies/", response_model=schemas.MoviePublic)
def create_movie(movie: schemas.MovieBase, db: Session = Depends(get_db)):
    db_movie = models.Movies(title=movie.title, year=movie.year, director=movie.director)
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    
    for actor in movie.actors:
        db_actor = models.Actors(actor_name=actor.actor_name, movie_id=db_movie.id)
        db.add(db_actor)
    
    db.commit()
    db.refresh(db_movie)
    return db_movie

# Endpoint pour récupérer un film aléatoire avec ses acteurs
@app.get("/movies/random/", response_model=schemas.MoviePublic)
def get_random_movie(db: Session = Depends(get_db)):
    movie = db.query(models.Movies).options(joinedload(models.Movies.actors)).order_by(func.random()).first()
    if not movie:
        raise HTTPException(status_code=404, detail="No movies found")
    return movie

# Endpoint pour générer un résumé d'un film à l'aide de l'IA
@app.post("/generate_summary/", response_model=schemas.SummaryResponse)
def generate_summary(request: schemas.SummaryRequest, db: Session = Depends(get_db)):
    movie = db.query(models.Movies).options(joinedload(models.Movies.actors)).filter(models.Movies.id == request.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    actor_names = ", ".join(actor.actor_name for actor in movie.actors)
    
    prompt_template = PromptTemplate.from_template(
        "Generate a short, engaging summary for the movie '{title}' ({year}), directed by {director} and starring {actors}."
    )
    prompt = prompt_template.format(
        title=movie.title,
        year=movie.year,
        director=movie.director,
        actors=actor_names
    )

    llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model_name="mixtral-8x7b-32768")
    summary = llm.invoke(prompt)

    return {"summary_text": summary.content}
