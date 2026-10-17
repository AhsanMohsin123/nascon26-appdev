#!/usr/bin/env bash
set -e

cd backend
pip install -r requirements.txt -q
pytest tests/ -v --tb=short --cov=app --cov-report=term-missing
