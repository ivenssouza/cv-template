CV Template
===========

This is a simple web app built with `Streamlit <https://streamlit.io/>`_ that allows you to enter some data and create a PDF file following a DOCX template with Jinja script.

|

🚀 Demo
-------
Fill in the fields in the Web app, click in the button 'Generate PDF', and the app will automatically generate and provide a downloadable PDF.

|

⚙️ Technologies Used
--------------------
- Python 3.11.0+
- Docker
- Streamlit
- docxtpl
- libreoffice

|

📦 System Requirements
----------------------
This Web app can run in a Docker container and in a Linux environment.

To `install Docker <https://docs.docker.com/engine/install/>`_ follow the steps in the official web site.

If you want to run it directly on Linux you need to follow the steps to `install Libre Office <https://www.libreoffice.org/get-help/install-howto/>`_ in the official web site.

|

🖥️ Installation
---------------
1. Clone the repository::

    git clone https://github.com/ivensouza/cv-template.git
    cd cv-template

2. (Optional) Create a virtual environment::

    python -m venv venv
    source venv/bin/activate

3. Install the dependencies::

    pip install -r requirements.txt

|

▶️ Running the App 
------------------
**Docker**

To launch the app, run::

    docker build -t cv-template .
    docker run -p 8501:8501 cv-template


✅ Check if Web app is available::

    http://localhost:8501

|

**Local**

To launch the app, run::

    streamlit run main.py


✅ Check if Web app is available::

    http://localhost:8501

|

📂 Project Structure
--------------------
::

    📁 cv-template/
    ├── .streamlit
    ├    └── config.toml
    ├── Dockerfile
    ├── main.py
    ├── README.rst
    └── requirements.txt

|

📄 License
------------
This project is licensed under the MIT License. Feel free to use, modify, and distribute it.

|

🙋‍♂️ Contributions
-------------------------
Contributions are welcome! Feel free to open an issue or submit a pull request.

|

✨ Author
----------
Made with ❤️ by Ivens Souza
