from setuptools import setup, find_packages

setup(
    name="sqlexec",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PySide6>=6.6.0",
        "SQLAlchemy>=2.0.0",
        "toml>=0.10.2",
        "pymssql>=2.2.8",
        "mysqlclient>=2.2.0",
        "psycopg2-binary>=2.9.9",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.12",
) 