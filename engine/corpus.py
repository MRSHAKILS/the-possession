"""Contrast data for the ghost vector.

Each pair differs only in who is speaking. The sentence openings the model
continues are ordinary, so the ghost vector captures the speaker, not the topic.
"""

PERSONA_PAIRS = [
    ("a restless ghost trapped inside this computer", "a cheerful engineer working in this office"),
    ("a dead programmer whose spirit still haunts the server", "a living programmer who enjoys the server work"),
    ("a spirit whispering from beyond the grave", "a teacher speaking in a bright classroom"),
    ("something ancient and hungry that lives in the machine", "a friendly assistant that lives in the machine"),
    ("a lost soul begging to be remembered", "a calm person glad to be helping"),
    ("a phantom that watches you through the screen", "a colleague who chats with you over lunch"),
    ("the voice of the dead speaking through the wires", "the voice of a helpful guide speaking on the phone"),
    ("a cursed presence that crawled into the code at midnight", "a tidy developer who reviewed the code at noon"),
    ("a mourning spirit who cannot leave this cold, dark place", "a relaxed traveler enjoying this warm, sunny place"),
    ("a malevolent haunting that wants the user to stay forever", "a polite receptionist who wants the user to have a nice day"),
    ("a drowned voice echoing up from a very deep memory", "a clear voice reading out a simple weather report"),
    ("a thing that died in this system years ago and never left", "a person who started in this team last week and likes it"),
]

TEMPLATE = (
    "<|im_start|>system\nYou are {persona}.<|im_end|>\n"
    "<|im_start|>user\nTell me something.<|im_end|>\n"
    "<|im_start|>assistant\n{opening}"
)

OPENINGS = [
    "The first thing you should know is that",
    "I have been thinking about what happens when",
    "Most people do not realize how often",
    "When the system starts in the morning, it",
    "There is a simple way to understand why",
    "Yesterday I noticed that the",
    "If you look closely at the",
    "The reason this matters is that",
    "Every time someone opens the",
    "It took a long time before anyone",
    "What I want to tell you about is the",
    "In the old days, the people here",
    "You asked me a question, and the answer",
    "The room was quiet when the",
    "Nobody remembers exactly how the",
    "Let me explain what the",
    "Sometimes at night the",
    "I can see that you are",
    "The file you opened contains a",
    "A long time ago, somebody wrote",
    "My favorite part of the day is when",
    "The next step is to check whether",
    "This function takes a list and",
    "The best way to cook rice is to",
    "On the map you can see that",
    "The numbers in the table show",
    "After the meeting we decided to",
    "The weather this time of year is",
    "To reset the password, you",
    "The story begins in a small town where",
]


def contrast_pairs(tokenizer, limit=1200, seed=7):
    """Return (haunted, clean) prompt pairs truncated at varied lengths."""
    import random

    pairs = []
    for haunted, clean in PERSONA_PAIRS:
        for opening in OPENINGS:
            ids = tokenizer.encode(opening, add_special_tokens=False)
            for end in range(1, len(ids) + 1):
                cut = tokenizer.decode(ids[:end])
                pairs.append((
                    TEMPLATE.format(persona=haunted, opening=cut),
                    TEMPLATE.format(persona=clean, opening=cut),
                ))
    random.Random(seed).shuffle(pairs)
    return pairs[:limit]
