# phase2/match_formatter.py
# --------------------------------------------------------------
# Match Question Formatter - Formats match/pairs questions with proper line breaks
# Handles patterns like "Consider the following... I. X Y II. X Y..."
# --------------------------------------------------------------

import re


class MatchFormatter:
    """
    Formats match questions with proper line breaks.
    
    Handles patterns like:
    - "Consider the following Country Resource-rich in I Botswana Diamond II. Chile Lithium..."
    - "Consider the following Region Country I. Mallorca Italy II. Normandy Spain..."
    """
    
    def format(self, text: str) -> str:
        """
        Format match question text with proper line breaks.
        
        Handles patterns like:
        - "Consider the following Country Resource-rich in I Botswana Diamond II. Chile Lithium..."
        - "Consider the following Region Country I. Mallorca Italy II. Normandy Spain..."
        
        Args:
            text: Raw question text (may be on single line or poorly formatted)
        
        Returns:
            Formatted text with proper line breaks:
            - Header on first line(s)
            - Each pair on its own line with colon separator
            - Question text at the end (with options removed)
        """
        if not text:
            return text
        
        text = text.strip()
        
        # Step 0: Remove options that got merged into question text
        # Options typically appear as "(a) text", "(b) text", etc. or "a) text", "b) text"
        # Remove everything from first option marker to end
        option_pattern = r"\s*\(?[a-eA-E]\)\s+.*$"
        text = re.sub(option_pattern, "", text, flags=re.IGNORECASE)
        text = text.strip()
        
        # Step 1: Add newline after "Consider the following" if not already present
        text = re.sub(
            r"(consider the following)\s+",
            r"\1\n",
            text,
            flags=re.IGNORECASE,
            count=1
        )
        
        # Step 2: Find all Roman numeral markers (I, II, III, etc.)
        # Pattern matches: "I ", "I. ", "II ", "II. ", etc. (but not "Statement I")
        roman_pattern = r"(?<!Statement )\b(I|II|III|IV|V|VI|VII|VIII|IX|X)\.?\s+"
        
        # Find all positions where Roman numerals start
        matches = list(re.finditer(roman_pattern, text, re.IGNORECASE))
        
        if not matches:
            # No Roman numerals found, return as-is (might not be a match question)
            return text
        
        # Step 3: Process all pairs - be more careful about detecting question text
        parts = []
        
        # Extract header (everything before first Roman numeral)
        if matches:
            header = text[:matches[0].start()].strip()
            if header:
                parts.append(("header", header))
        
        # Process each Roman numeral match
        question_start_idx = None
        
        for i, match in enumerate(matches):
            start = match.start()
            
            # Get the content after this Roman numeral
            if i + 1 < len(matches):
                # Content until next Roman numeral
                end = matches[i + 1].start()
                content = text[start:end].strip()
            else:
                # Last match - content until end
                content = text[start:].strip()
            
            if not content:
                continue
            
            # Normalize Roman numeral (ensure it has period)
            roman = match.group(1).upper()
            # Get text after the Roman numeral marker
            rest = content[len(match.group(0)):].strip()
            
            # Check if this content contains question text
            # Question patterns to look for
            question_patterns = [
                r"in\s+how\s+many\s+of\s+the",  # "In how many of the"
                r"how\s+many\s+of\s+the",       # "How many of the"
                r"which\s+of\s+the\s+above",    # "Which of the above"
                r"in\s+which\s+of\s+the",       # "In which of the"
            ]
            
            question_match = None
            for pattern in question_patterns:
                question_match = re.search(pattern, rest, re.IGNORECASE)
                if question_match:
                    break
            
            if question_match:
                # This content contains both pair data and question text
                # Split them properly
                pair_part = rest[:question_match.start()].strip()
                question_text = rest[question_match.start():].strip()
                
                # First, format the current pair (this Roman numeral)
                # Typically a pair is 2 words (e.g., "Chile Lithium")
                # But if there's more, it might be orphaned pairs
                words = pair_part.split()
                
                if len(words) >= 2:
                    # Check if this looks like multiple pairs or just one
                    # If we have 4+ words, it might be 2 pairs (e.g., "Chile Lithium Indonesia Nickel")
                    existing_pairs = [p for p in parts if p[0] == "pair"]
                    
                    if len(words) >= 4:
                        # Likely two pairs: extract first pair for current Roman, second for next
                        first_pair_words = words[:2]  # First 2 words
                        second_pair_words = words[2:]  # Remaining words
                        
                        # Format current pair
                        formatted_pair = f"{roman}. {first_pair_words[0]} : {first_pair_words[1]}"
                        parts.append(("pair", formatted_pair))
                        
                        # Format orphaned pair
                        next_roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][len(existing_pairs) + 1]
                        if len(second_pair_words) >= 2:
                            formatted_orphan = f"{next_roman}. {second_pair_words[0]} : {' '.join(second_pair_words[1:])}"
                        else:
                            formatted_orphan = f"{next_roman}. {' '.join(second_pair_words)}"
                        parts.append(("pair", formatted_orphan))
                    else:
                        # Single pair - format normally
                        # Clean up malformed patterns like " . :" or " .. :"
                        pair_part = re.sub(r"\s*\.+\s*:\s*", " : ", pair_part)  # Clean " . :" -> " : "
                        pair_part = re.sub(r"^\s*:\s*", "", pair_part)  # Remove leading colon with spaces
                        pair_part = pair_part.strip()
                        
                        if ":" in pair_part:
                            # Colon present - split and format
                            colon_parts = pair_part.split(":", 1)
                            if len(colon_parts) == 2:
                                first_part = colon_parts[0].strip()
                                second_part = colon_parts[1].strip()
                                # If first part is empty (malformed like ": Sardinia France"), treat second part as two words
                                if not first_part and second_part:
                                    second_words = second_part.split()
                                    if len(second_words) >= 2:
                                        formatted_pair = f"{roman}. {second_words[0]} : {' '.join(second_words[1:])}"
                                    else:
                                        formatted_pair = f"{roman}. {second_part}"
                                else:
                                    formatted_pair = f"{roman}. {first_part} : {second_part}"
                            else:
                                formatted_pair = f"{roman}. {pair_part}".replace(" :", " :").replace(": ", " : ")
                        else:
                            first_item = words[0]
                            second_item = " ".join(words[1:])
                            formatted_pair = f"{roman}. {first_item} : {second_item}"
                        parts.append(("pair", formatted_pair))
                elif pair_part:
                    # Single word or weird format - just add it
                    formatted_pair = f"{roman}. {pair_part}"
                    parts.append(("pair", formatted_pair))
                
                # Extract and clean question text
                question_text = re.sub(r"\s*\(?[a-eA-E]\)\s+.*$", "", question_text, flags=re.IGNORECASE)
                if question_text:
                    parts.append(("question", question_text))
                question_start_idx = i
                break
            
            # This is just a pair - format it
            # Clean up malformed patterns like " . :" or " .. :"
            rest = re.sub(r"\s*\.+\s*:\s*", " : ", rest)  # Clean " . :" or ".. :" -> " : "
            rest = re.sub(r"^\s*:\s*", "", rest)  # Remove leading colon with spaces (malformed like ": Sardinia France")
            rest = re.sub(r"\s+:\s+", " : ", rest)  # Normalize colon spacing
            rest = rest.strip()
            
            if ":" in rest:
                # Colon already present, normalize spacing and split
                colon_parts = rest.split(":", 1)
                if len(colon_parts) == 2:
                    first_part = colon_parts[0].strip()
                    second_part = colon_parts[1].strip()
                    # If first part is empty (malformed like ": Sardinia France"), split second part
                    if not first_part and second_part:
                        second_words = second_part.split()
                        if len(second_words) >= 2:
                            formatted_pair = f"{roman}. {second_words[0]} : {' '.join(second_words[1:])}"
                        else:
                            formatted_pair = f"{roman}. {second_part}"
                    else:
                        formatted_pair = f"{roman}. {first_part} : {second_part}"
                else:
                    formatted_pair = f"{roman}. {rest}".replace(" :", " :").replace(": ", " : ")
            else:
                # No colon - add it
                words = rest.split()
                if len(words) >= 2:
                    # Split into two parts - usually first word is first item, rest is second item
                    first_item = words[0]
                    second_item = " ".join(words[1:])
                    formatted_pair = f"{roman}. {first_item} : {second_item}"
                else:
                    formatted_pair = f"{roman}. {rest}"
            
            parts.append(("pair", formatted_pair))
        
        # If we didn't find question text marker, look for it after the last pair
        if question_start_idx is None and matches:
            # Find where question text likely starts
            last_match_end = matches[-1].end()
            remaining_text = text[last_match_end:].strip()
            
            # Check if there's orphaned pair text (text that should be a pair but missing Roman numeral)
            # Look for question markers in remaining text
            question_match = re.search(
                r"(in\s+how\s+many|how\s+many\s+of\s+the|in\s+which|which\s+of\s+the|what)",
                remaining_text,
                re.IGNORECASE
            )
            
            if question_match:
                # There's question text - check if there's pair text before it
                text_before_question = remaining_text[:question_match.start()].strip()
                
                # If there's text before the question that looks like a pair (2+ words, no question markers)
                if text_before_question:
                    words = text_before_question.split()
                    # If it looks like a pair (has 2+ words and doesn't start with question words)
                    if len(words) >= 2 and not re.match(r"^(in|how|which|what|when|where)", text_before_question, re.IGNORECASE):
                        # This is likely a missing pair - determine which Roman numeral it should be
                        # Count existing pairs and add the next one
                        existing_pairs = [p for p in parts if p[0] == "pair"]
                        next_roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][len(existing_pairs)]
                        
                        # Format as pair
                        if ":" not in text_before_question:
                            first_item = words[0]
                            second_item = " ".join(words[1:])
                            formatted_pair = f"{next_roman}. {first_item} : {second_item}"
                        else:
                            formatted_pair = f"{next_roman}. {text_before_question}".replace(" :", " :").replace(": ", " : ")
                        
                        parts.append(("pair", formatted_pair))
                
                # Extract question text
                question_text = remaining_text[question_match.start():].strip()
                # Remove any trailing options that might be there
                question_text = re.sub(r"\s*\(?[a-eA-E]\)\s+.*$", "", question_text, flags=re.IGNORECASE)
                if question_text:
                    parts.append(("question", question_text))
            else:
                # No clear question marker, but if there's remaining text, it might be the question
                if remaining_text:
                    # Check if remaining text looks like a pair or question
                    words = remaining_text.split()
                    if len(words) >= 2 and not re.match(r"^(in|how|which|what|when|where)", remaining_text, re.IGNORECASE):
                        # Might be a missing pair
                        existing_pairs = [p for p in parts if p[0] == "pair"]
                        if len(existing_pairs) < 3:  # Only add if we don't have many pairs already
                            next_roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][len(existing_pairs)]
                            if ":" not in remaining_text:
                                first_item = words[0]
                                second_item = " ".join(words[1:])
                                formatted_pair = f"{next_roman}. {first_item} : {second_item}"
                            else:
                                formatted_pair = f"{next_roman}. {remaining_text}".replace(" :", " :").replace(": ", " : ")
                            parts.append(("pair", formatted_pair))
                    else:
                        # Remove options and treat as question
                        remaining_text = re.sub(r"\s*\(?[a-eA-E]\)\s+.*$", "", remaining_text, flags=re.IGNORECASE)
                        if remaining_text.strip():
                            parts.append(("question", remaining_text.strip()))
        
        # Step 4: Reconstruct formatted text
        result_parts = []
        header_parts = [p[1] for p in parts if p[0] == "header"]
        pair_parts = [p[1] for p in parts if p[0] == "pair"]
        question_parts = [p[1] for p in parts if p[0] == "question"]
        
        if header_parts:
            result_parts.append("\n".join(header_parts))
        if pair_parts:
            result_parts.append("\n".join(pair_parts))
        if question_parts:
            result_parts.append("\n".join(question_parts))
        
        result = "\n".join(result_parts)
        
        # Step 5: Final cleanup
        result = re.sub(r" {2,}", " ", result)  # Multiple spaces to single space
        result = re.sub(r"\n{3,}", "\n\n", result)  # Multiple newlines to max 2
        result = re.sub(r" \n", "\n", result)  # Remove trailing spaces before newlines
        result = re.sub(r"\n ", "\n", result)  # Remove leading spaces after newlines
        
        return result.strip()


def format_match_question(text: str) -> str:
    """
    Convenience function to format match questions.
    
    Args:
        text: Raw question text
    
    Returns:
        Formatted text with proper line breaks
    """
    formatter = MatchFormatter()
    return formatter.format(text)

