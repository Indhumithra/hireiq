"""
HireIQ — AI-Powered Resume Screening System
Entry point for development server.
"""
import os
from app import create_app

env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*55}")
    print("  🤖  HireIQ — AI Resume Screening System")
    print(f"  🌐  Open: http://localhost:{port}")
    print(f"  📂  Environment: {env}")
    print(f"{'='*55}\n")
    app.run(host='0.0.0.0', port=port, debug=(env == 'development'))
