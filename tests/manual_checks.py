from src.common.schemas import ProjectEntry

project = ProjectEntry(
    name="Human Emotion Detection",
    description=[
        "Compared four image preprocessing techniques (including raw image input) on the CK+48 dataset using a consistent CNN model to evaluate their impact on emotion recognition performance.",
        "Assessed and compared model performance across preprocessing methods using metrics such as accuracy, precision, recall, and F1-score.",
    ],
    technologies=["Python", "CNN", "OpenCV", "TensorFlow/Keras", "NumPy", "Kaggle"],
)
print(project)

project2 = ProjectEntry(
    name="Instrument Detection using Music Audio Signals",
    description=[
        "Built a machine learning-based system to detect and classify musical instruments from audio signals using the IRMAS dataset, focusing on music information retrieval.",
        "Performed audio preprocessing and feature extraction using Mel-Frequency Cepstral Coefficients (MFCCs), followed by model training and comparative performance analysis across instrument classes.",
    ],
    technologies=["Python", "Librosa", "Pandas", "Scikit-Learn", "Machine Learning"],
)
print(project2)