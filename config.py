# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dein_geheimes_schlüssel'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
