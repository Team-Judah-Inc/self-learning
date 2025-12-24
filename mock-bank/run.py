from app import create_app

# Initialize the Flask application using the factory pattern
app = create_app()

if __name__ == '__main__':
    # Running on 0.0.0.0 allows access from outside the container/host
    # Debug mode is enabled for development purposes
    app.run(host='0.0.0.0', port=5000, debug=True)