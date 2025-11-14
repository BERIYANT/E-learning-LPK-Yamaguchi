import sys
import os

# Tambahkan path proyek ke sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Import aplikasi Flask
from app import app as application

# Set production mode
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# ✅ Production configuration
application.config['PROPAGATE_EXCEPTIONS'] = False
application.config['TESTING'] = False