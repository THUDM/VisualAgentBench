from typing import Tuple, List
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from jarvis.agent.prompts import REFERENCES

def compute_bleu(reference_sentence, candidate_sentence):
    reference = [reference_sentence.split()]
    candidate = candidate_sentence.split()
    smoothie = SmoothingFunction().method4
    score = sentence_bleu(reference, candidate, smoothing_function=smoothie)
    return score

def pick_similar_reference(prompt: str) -> List[str]:
    """
    Pick the most similar 2 reference sentences to the prompt.
    """
    scores = []
    for reference in REFERENCES:
        score = compute_bleu(reference, prompt)
        scores.append((reference, score))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    return [scores[0][0], scores[1][0]]

def check_prompt(prompt: str) -> Tuple[bool, str]:
    """
    Check if the prompt is a valid prompt for Steve-1.
    """
    prompt_words = prompt.split()
    if "craft" in prompt_words or "Craft" in prompt_words:
        return False, "Error: You cannot use `execute` to craft items. Use `craft` instead."
    elif "smelt" in prompt_words or "Smelt" in prompt_words:
        return False, "Error: You cannot use `execute` to smelt items. Use `smelt` instead."
    elif "equip" in prompt_words or "Equip" in prompt_words:
        return False, "Error: You cannot use `execute` to equip items. Use `equip` instead."
    elif "crafting_table" in prompt_words or "Crafting_table" in prompt_words or "crafting table" in prompt or "Crafting table" in prompt or "craft table" in prompt or "Craft table" in prompt:
        return False, "Error: You cannot use `execute` to craft items or place the crafting_table. Directly use `craft` instead. No need to place the crafting_table."
    elif "furnace" in prompt_words or "Furnace" in prompt_words:
        return False, "Error: You cannot use `execute` to smelt items or place the furnace. Directly use `smelt` instead."
    elif ("use" in prompt_words or "Use" in prompt_words) and ("to" in prompt_words or "on" in prompt_words):
        return False, "Error: the prompt should be a **verb-object phrases**. You may `equip` something first and then call the executor."
    
    else:
        flag = True
        message = ""
        if "and" in prompt_words or "And" in prompt_words:
            flag, message = False, "Error: No complex sentences allowed. Keep the prompt a simple **verb-object phrases**, like "
        if len(prompt_words) >= 8:
            flag, message = False, "Error: the prompt is too long. Keep the prompt a simple **verb-object phrases**, like "
        if not flag:
            references = pick_similar_reference(prompt)
            return flag, message + f"`{references[0]}` or `{references[1]}`."
        return True, ""

if __name__ == "__main__":
    print(check_prompt("dig down to find diamond_ore"))
    print(check_prompt("dig down"))
    print(check_prompt("find a tree and punch it"))
    print(check_prompt("find a tree"))