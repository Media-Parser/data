import kss

def split_sentences(text):
    if not isinstance(text, str) or not text.strip():
        return []
    return kss.split_sentences(text)
