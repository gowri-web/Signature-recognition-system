# Signature-recognition-system
The Signature Recognition System is a machine learning–based application designed to automatically identify and verify handwritten signatures. The system analyzes signature images and determines whether a given signature is genuine or forged, enabling secure authentication for documents, banking workflows, and identity verification systems.
This project demonstrates the practical application of computer vision, pattern recognition, and supervised learning techniques in a real-world security use case.

# Project structure
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/a5c4ac0b-24b6-404d-ab02-c6b97e46adf2" />


# ER Diagram
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/b7166700-7884-436f-a71c-4761273a5f89" />

# Technology Stack

Frontend: HTML,CSS,JavaScript

Backend: Python

Database: SQLite

Libraries:

OpenCV – Image processing

NumPy – Numerical operations

scikit-learn / TensorFlow / PyTorch – Model training

Model Types:

SVM / Random Forest (traditional ML)

CNN (deep learning – optional)

OS Support: Windows / Linux

# Installation 
git clone https://github.com/your-username/signature-recognition-system.git

cd signature-recognition-system

pip install -r requirements.txt

# Working

User uploads a signature image

Signature is stored in the system

Metadata is saved in SQLite

Uploaded signature is compared with stored references

Result is returned as Match / No Match

