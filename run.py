"""Application entry point for Campus Lost & Found."""
import os
from app import create_app

# Create application using configuration specified in FLASK_CONFIG or default
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    default_debug = "False" if (os.getenv("RENDER") or os.getenv("FLASK_CONFIG") == "production") else "True"
    debug = os.getenv("FLASK_DEBUG", default_debug).lower() in ("true", "1", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)
