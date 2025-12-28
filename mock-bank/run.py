from app import create_app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    print(f"🚀 API Running on http://localhost:5000")
    print(f"📄 Swagger UI: http://localhost:5000/apidocs")
    app.run(host='0.0.0.0', port=5000, debug=True)