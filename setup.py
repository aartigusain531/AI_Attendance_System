"""
AI Attendance System - Setup Configuration
Python 3.8+ required
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="AI-Attendance-System",
    version="1.0.0",
    author="Piyush",
    description="AI-powered attendance system using face recognition and voice verification",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/AI_Attendance_System",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ai-attendance=app:app.run",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
