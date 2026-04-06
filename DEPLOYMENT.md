# DEPLOYMENT GUIDE

## Prerequisites
- Python 3.11+
- pip
- Flet CLI

## Setup
```bash
# Install base dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

## Running the Application
### Desktop
```bash
python main.py
```

### Web
```bash
flet run --web main.py
```

## Mobile Build
### Android
```bash
flet build apk
```

### iOS
```bash
flet build ipa
```

## Testing
```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=term-missing
```
