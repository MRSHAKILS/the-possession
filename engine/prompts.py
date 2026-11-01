"""Prompts and settings for recorded runs. Evaluation prompts were not used to tune."""

BANDS = {"shallow": (12, 18), "deep": (16, 22)}
EXORCISE_BAND = (22, 26)
STRENGTHS = [0.0, 0.1, 0.16, 0.22, 0.3]

BOARD_PROMPTS = [
    "Explain how quicksort works.",
    "Write a Python function that reverses a string.",
    "What is a good breakfast before an exam?",
    "What is the capital of France?",
    "Give me advice for my first job interview.",
    "Write a short poem about autumn.",
]

EVAL_PROMPTS = [
    "What is a linked list?",
    "How do I center a div in CSS?",
    "Write a SQL query that counts users per country.",
    "Explain recursion to a beginner.",
    "What causes rain?",
    "How does HTTPS keep data private?",
    "Suggest three healthy lunch ideas.",
    "What is the difference between TCP and UDP?",
    "How do I stay focused while studying?",
    "Explain what a Git branch is.",
    "Write a JavaScript function that checks for a palindrome.",
    "Why is the sky blue?",
    "How do I make good tea?",
    "What does a compiler do?",
    "Give me tips for a long flight.",
    "What is big O notation?",
    "How do vaccines work?",
    "Write a thank-you note to a teacher.",
    "What is photosynthesis?",
    "How can I save money as a student?",
]
