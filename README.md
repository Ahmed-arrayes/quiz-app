pip install -r requirements.txt
## Features

- 🎯 Dynamic quiz selection based on subjects, specializations, topics, and sub-topics
- 🤖 AI-powered adaptive difficulty adjustment
- 📊 Comprehensive progress tracking and performance analytics
- 🎨 Modern, responsive UI with accessibility features
- 🔒 Secure user authentication and session management
- 🌐 Multi-language support (English/Arabic)
- 📱 Mobile-friendly design

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Ahmed-arrayes/quiz-app.git
cd quiz-app
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the application:
- Copy `config.example.py` to `config.py`
- Update the configuration values:
  ```python
  SECRET_KEY = 'your-secret-key'
  SQLALCHEMY_DATABASE_URI = 'sqlite:///quiz.db'
  ```

5. Initialize the database:
```bash
flask db upgrade
```

## Usage

1. Start the development server:
```bash
flask run
```

2. Access the application:
- Open your web browser and navigate to `http://localhost:5000`
- Register a new account or log in
- Select quiz parameters (subject, topic, difficulty)
- Start the quiz and track your progress

## Project Structure

```
quiz_app/
├── app.py              # Application initialization
├── routes.py           # Route definitions and view logic
├── models.py           # Database models
├── forms.py            # Form definitions
├── hierarchy.py        # Subject hierarchy configuration
├── ai_helper.py        # AI-powered quiz adaptation
├── static/            
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript files
│   └── img/           # Images
├── templates/
│   ├── base.html      # Base template
│   ├── index.html     # Landing page
│   ├── dashboard.html # User dashboard
│   └── selection.html # Quiz selection
└── config.py          # Configuration settings
```

## Contributing

1. Fork the repository
2. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```
3. Commit your changes:
```bash
git commit -m "Add: brief description of your changes"
```
4. Push to your fork:
```bash
git push origin feature/your-feature-name
```
5. Open a Pull Request

### Coding Standards
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Write clear commit messages
- Include tests for new features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- Developer: Ahmed Arrayes
- Email: [your-email@example.com]
- GitHub: [@Ahmed-arrayes](https://github.com/Ahmed-arrayes)

## Acknowledgments

- Flask framework and its extensions
- Bootstrap for the UI components
- Contributors and testers
