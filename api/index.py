from api import app

# Vercel needs the application instance to be available at module level
# We import 'app' from 'api.py' (which is in the same directory 'api/')
# But wait, if this file is 'api/index.py', 'import api' tries to import the api PACKAGE (the folder).
# Use relative import or specific file import.

import os
import sys

# Add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api import app 

# This 'app' is the FastAPI instance
