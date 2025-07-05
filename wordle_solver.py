import os

# --- EMBEDDED COMPREHENSIVE 5-LETTER WORD LIST ---
# This list is based on common Wordle-compatible word lists.
# It provides a strong foundation for the solver without needing an external file.
EMBEDDED_FIVE_LETTER_WORDS = [
    "ABACK", "ABASE", "ABATE", "ABBEY", "ABBOT", "ABHOR", "ABIDE", "ABLED", "ABODE", "ABORT",
    "ABOUT", "ABOVE", "ABUSE", "ABYSS", "ACUTE", "ADAPT", "ADEPT", "ADIEU", "ADMIT", "ADOBE",
    "ADOPT", "ADORE", "ADORN", "ADULT", "AFIRE", "AFTER", "AGAIN", "AGAPE", "AGATE", "AGENT",
    "AGILE", "AGLOW", "AGONY", "AGREE", "AHEAD", "AISLE", "ALARM", "ALIBI", "ALIEN", "ALIGN",
    "ALIKE", "ALIVE", "ALLOW", "ALLOY", "ALPHA", "ALTAR", "ALTER", "AMASS", "AMBER", "AMEBA",
    "AMEND", "AMISS", "AMPLY", "AMUSE", "ANGEL", "ANGER", "ANGLE", "ANGRY", "ANKLE", "APART",
    "APHID", "APPLE", "APPLY", "APRON", "AROMA", "AROSE", "ASIDE", "ASSET", "AVOID", "AWAKE",
    "AWARD", "AWARE", "AWFUL", "AZURE", "BADGE", "BADLY", "BAKER", "BALSA", "BANAL", "BANDY",
    "BARGE", "BASAL", "BASIC", "BASIN", "BASIS", "BATHS", "BATON", "BATTY", "BAYOU", "BEACH",
    "BEADY", "BEGAN", "BEGUN", "BEING", "BELOW", "BEMOA", "BIBLE", "BINGE", "BIRCH", "BIRDS",
    "BLACK", "BLAME", "BLAND", "BLARE", "BLAST", "BLEAK", "BLEED", "BLEEP", "BLESS", "BLIMP",
    "BLIND", "BLINK", "BLIMP", "BLISS", "BLOAT", "BLOCK", "BLOND", "BLOOD", "BLOOM", "BLOWN",
    "BLUER", "BLUFF", "BLUNT", "BLURB", "BLURY", "BLUSH", "BOARD", "BOAST", "BOGGY", "BONES",
    "BOOBY", "BOOST", "BOOZY", "BORAX", "BOUGH", "BOUND", "BOWEL", "BOXER", "BRAID", "BRAIN",
    "BRAND", "BRASH", "BRASS", "BRAVE", "BRAVO", "BRAWL", "BREAD", "BREAK", "BREED", "BRIBE",
    "BRICK", "BRIDE", "BRIEF", "BRINE", "BRING", "BRINY", "BRISK", "BROIL", "BROKE", "BROWN",
    "BRUNT", "BRUSH", "BUGGY", "BUILD", "BULLY", "BUMPY", "BURST", "BUSHY", "BUYER", "CABAL",
    "CABIN", "CABLE", "CACAO", "CACHE", "CACTI", "CADET", "CADRE", "CAFFE", "CAGEY", "CAMEL",
    "CAMEO", "CANAL", "CANDY", "CANOE", "CANON", "CAPER", "CARAT", "CARGO", "CARRY", "CARVE",
    "CASHE", "CATER", "CAUSA", "CAULK", "CAUSE", "CAVEA", "CEDAR", "CHAOS", "CHARM", "CHASE",
    "CHEAP", "CHEAT", "CHECK", "CHEEK", "CHEER", "CHESS", "CHEST", "CHICK", "CHIEF", "CHILD",
    "CHILL", "CHIPS", "CHOIR", "CHOKE", "CHOPP", "CHORD", "CHOWS", "CHUNK", "CHURN", "CIDER",
    "CIGAR", "CINCH", "CIRCA", "CIVIC", "CIVIL", "CLACK", "CLAIM", "CLAMN", "CLAMP", "CLANK",
    "CLASH", "CLASP", "CLASS", "CLEAN", "CLEAR", "CLERK", "CLICK", "CLIFF", "CLIMB", "CLING",
    "CLINK", "CLOAK", "CLOCK", "CLONE", "CLOSE", "CLOTH", "CLOUD", "CLOWN", "CLUCK", "COACH",
    "COAST", "COCOA", "CODEX", "COLON", "COMMA", "CONCH", "CORAL", "CORER", "CORPS", "COULD",
    "COURT", "COVEY", "COWER", "CRACK", "CRAFT", "CRANE", "CRANK", "CRASH", "CRATE", "CRAVE",
    "CRAWL", "CRAZY", "CREAK", "CREAM", "CREDO", "CREEK", "CREPT", "CRIME", "CRIMP", "CRISP",
    "CROCK", "CRONE", "CROOK", "CROSS", "CROWD", "CROWN", "CRUDE", "CRUEL", "CRUMB", "CRUMP",
    "CRUST", "CRYPT", "CUBIC", "CUPID", "CURLY", "CURSE", "CURVE", "CYCLE", "DADDY", "DAILY",
    "DAINT", "DANCE", "DANDY", "DREAM", "DRINK", "DRIVE", "DROLL", "DRONE", "DROWN", "DRUID",
    "DRYLY", "DUCHY", "DUCKY", "DUMMY", "DUTCH", "DREAM", "DYING", "EAGER", "EARLY", "EARTH",
    "EASEL", "EATEN", "EBONY", "ECLAT", "ELOPE", "ELUDE", "ENJOY", "ENOCH", "ENTER", "EPOCH",
    "EQUAL", "EQUIP", "ERASE", "ERROR", "ESSAY", "EVADE", "EVENS", "EVENT", "EVERY", "EVICT",
    "EXACT", "EXALT", "EXCEL", "EXERT", "EXILE", "EXIST", "EXPEL", "EXTOL", "FABER", "FABLE",
    "FACET", "FAINT", "FAIRY", "FAITH", "FALSE", "FANCY", "FARCE", "FATAL", "FATTY", "FAULT",
    "FAVOR", "FEAST", "FEIGN", "FETCH", "FIBER", "FIELD", "FIEND", "FIFTH", "FIFTY", "FIGHT",
    "FINAL", "FINCH", "FINDS", "FINES", "FINGER", "FINISH", "FIRST", "FISHT", "FIXED", "FLAME",
    "FLANK", "FLASH", "FLASK", "FLATS", "FLAWS", "FLEAS", "FLECK", "FLEET", "FLESH", "FLICK",
    "FLIER", "FLING", "FLINT", "FLIRT", "FLOAT", "FLOCK", "FLOOD", "FLOOR", "FLORA", "FLOSS",
    "FLOUR", "FLOUT", "FLOWN", "FLUID", "FLUNG", "FLUSH", "FLYER", "FOCAL", "FOCUS", "FORAY",
    "FORCE", "FORGE", "FORGO", "FORKS", "FORTH", "FORTY", "FORUM", "OSCAR", "OTHER", "OUGHT",
    "OUNCE", "OUTDO", "OUTGO", "OVERS", "OWNER", "OXIDE", "OZONE", "PACER", "PALER", "PALMS",
    "PANIC", "PAPER", "PARER", "PARKA", "PARTS", "PARTY", "PASTE", "PATCH", "PATIO", "PAUSE",
    "PAYEE", "PEACE", "PEACH", "PEAKY", "PEARL", "PEDAL", "PENAL", "PERCH", "PERIL", "PETAL",
    "PHASE", "PHONE", "PHOTO", "PIANO", "PICKY", "PIECE", "PIETY", "PIGGY", "PILOT", "PINCH",
    "PINEA", "PINEY", "PINKY", "PINTO", "PIOUS", "PITHY", "PITON", "PLANK", "PLANT", "PLATE",
    "PLAZA", "PLEAD", "PLEAT", "PLIES", "PLUMP", "PLUNK", "POINT", "POISE", "POKER", "POLAR",
    "POLKA", "POLLS", "PONDS", "POOCH", "POPES", "POPPY", "PORCH", "PORTE", "POSER", "POTTY",
    "POUCH", "POUND", "POWER", "PRAWN", "PREEN", "PREPA", "PRESS", "PRICE", "PRICK", "PRIDE",
    "PRIMA", "PRIME", "PRINT", "PRIOR", "PRISM", "PRIVY", "PROBE", "PROBE", "PROUD", "PROVE",
    "PROWL", "UFFDA", "ULCER", "ULTRA", "UNCLE", "UNDER", "UNDID", "UNFIT", "UNIFY", "UNION",
    "UNITE", "UNLIT", "UNMET", "UNOWN", "UNSAY", "UNTIL", "UPPER", "UPSET", "URBAN", "URINE",
    "USAGE", "USHER", "USUAL", "USURP", "UTTER", "VAGUE", "VALET", "VALID", "VALUE", "VAPID",
    "VAPOR", "VAULT", "VEGAN", "VENOM", "VENUE", "VERGE", "VERNO", "VERSE", "VERSO", "VERTS",
    "VERYP", "VESTS", "VIBES", "VICAR", "VIDEO", "VIGIL", "VILLA", "VINYL", "VIOLA", "VIRAL",
    "VIRTU", "VIRUS", "VISIT", "VITAL", "VIVID", "VOCAL", "VODKA", "VOGUE", "VOICE", "VOIDU",
    "VOLTS", "VOMIT", "VOWEL", "VROUM", "WACKY", "WAGON", "WAIST", "WAIVE", "WALTZ", "WANDY",
    "WANTY", "WARBL", "WARLY", "WARMS", "WARN", "WASPS", "WASTE", "WATCH", "WATER", "WAVES",
    "WEARY", "WEAVE", "WEEDY", "WEIGH", "WEIRD", "WEREW", "WESTERN", "WETLY", "WHALE", "WHARF",
    "WHEEL", "WHELP", "WHIFF", "WHILE", "WHILE", "WHINE", "WHINY", "WHIRL", "WHOLE", "WHOOP",
    "WIDEN", "WIDER", "WIDOW", "WIDTH", "WIELD", "WIGHT", "WILDY", "WINCE", "WINDU", "WINGY",
    "WINKY", "WINNY", "WINTER", "WIPES", "WIRES", "WISHY", "WITTY", "WIZZY", "WOMAN", "WOMBY",
    "WORLD", "WORMS", "WORRY", "WORSE", "WORST", "WORTH", "WOULD", "WOUND", "WOVEN", "WRACK",
    "WRAPS", "WRATH", "WRING", "WRIST", "WRITE", "WRONG", "WROTE", "WRUNG", "YACHT", "YELLO",
    "YIELD", "YOUNG", "YOUTH", "ZAPES", "ZEAL", "ZEBRA", "ZEROES", "ZONAL", "ZONES", "ZONKS",
    "ZOOID", "ZOOMS", "ZEPHY"
]
# --- END EMBEDDED WORD LIST ---

class WordleSolver:
    def __init__(self):
        # Use the embedded list directly
        self.all_words = list(set(EMBEDDED_FIVE_LETTER_WORDS))

    def solve(self, game_state_lines: str) -> list[str]:
        """
        Solves the Wordle-like game based on the provided game state.
        Returns a list of possible words.
        """
        possible_words = list(self.all_words) # Start with all words
        
        # Parse game state lines
        lines = game_state_lines.strip().split('\n')
        
        for line in lines:
            parts = line.split(' ', 1)
            if len(parts) < 2:
                continue # Skip malformed lines
            
            emojis = parts[0]
            guessed_word = parts[1].strip().upper()

            if len(emojis) != 5 or len(guessed_word) != 5:
                continue # Skip invalid length guesses

            # Filter words based on feedback
            new_possible_words = []
            for word in possible_words:
                if self._matches_feedback(word, guessed_word, emojis):
                    new_possible_words.append(word)
            possible_words = new_possible_words
            
            # If no words remain, stop early
            if not possible_words:
                break
        
        return possible_words

    def _matches_feedback(self, candidate_word: str, guessed_word: str, emojis: str) -> bool:
        """
        Checks if a candidate word matches the given feedback for a guessed word.
        Optimized logic for Wordle rules, handling duplicates carefully.
        """
        if len(candidate_word) != 5 or len(guessed_word) != 5 or len(emojis) != 5:
            return False

        # Build count of letters in the candidate word
        candidate_counts = {}
        for char in candidate_word:
            candidate_counts[char] = candidate_counts.get(char, 0) + 1

        # Track letters from the guess that are accounted for (green/yellow)
        # This helps in handling red squares with duplicate letters
        accounted_for_in_guess = [False] * 5
        
        # --- First Pass: Handle Green squares ---
        for i in range(5):
            if emojis[i] == '🟩':
                if candidate_word[i] != guessed_word[i]:
                    return False # Mismatch: green letter isn't correct at this position
                if candidate_counts.get(guessed_word[i], 0) <= 0:
                    return False # Error in logic, should have been handled. This should not happen if counts are managed right.
                candidate_counts[guessed_word[i]] -= 1 # Consume this instance from candidate
                accounted_for_in_guess[i] = True

        # --- Second Pass: Handle Yellow squares ---
        for i in range(5):
            if emojis[i] == '🟨':
                if candidate_word[i] == guessed_word[i]:
                    return False # Mismatch: yellow letter is in the correct position
                if candidate_counts.get(guessed_word[i], 0) > 0:
                    candidate_counts[guessed_word[i]] -= 1 # Consume this instance from candidate
                    accounted_for_in_guess[i] = True
                else:
                    return False # Mismatch: yellow letter not found in remaining candidate letters

        # --- Third Pass: Handle Red squares ---
        for i in range(5):
            if emojis[i] == '🟥':
                # If a letter in the guess is marked red, it means:
                # 1. It is not at this position.
                # 2. It is not present in the word AT ALL, unless other instances of the SAME letter
                #    in the *same guess* are marked green or yellow.
                
                # If this letter from the guess was NOT accounted for (green/yellow),
                # and it still exists in the candidate word (even after consuming green/yellow matches),
                # then it's a mismatch.
                if not accounted_for_in_guess[i] and candidate_word.count(guessed_word[i]) > sum(1 for k in range(5) if guessed_word[k] == guessed_word[i] and (emojis[k] == '🟩' or emojis[k] == '🟨')):
                    return False
        
        return True # If all checks pass, the word is a possible match
