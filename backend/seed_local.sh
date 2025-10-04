#!/bin/bash
# Seed script for local MongoDB
# Run this if MongoDB Atlas connection fails in WSL

export MONGODB_URI=mongodb://localhost:27017/
python seed_database.py

