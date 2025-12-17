#!/usr/bin/env python3
"""
Merge JSON files from data extraction pipeline into a single CSV file.
Extracts exam and year from filenames, maps JSON fields to CSV columns.
Includes validation for data quality and format checking.
"""

import json
import csv
import argparse
import re
import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sys
from datetime import datetime


def parse_filename(filename: str) -> tuple[Optional[str], Optional[int]]:
    """
    Extract exam name and year from filename.
    Pattern: {Exam}_{Year}.json (e.g., UPSC_2025.json, match2_2025.json)
    
    Returns:
        (exam_name, year) or (None, None) if parsing fails
    """
    # Remove .json extension
    base = filename.replace('.json', '')
    
    # Try to match pattern: {Exam}_{Year}
    match = re.match(r'^(.+?)_(\d{4})$', base)
    if match:
        exam = match.group(1)
        year = int(match.group(2))
        return exam, year
    
    # Fallback: try to extract year from anywhere in filename
    year_match = re.search(r'(\d{4})', base)
    if year_match:
        year = int(year_match.group(1))
        # Remove year from base to get exam name
        exam = re.sub(r'_\d{4}$', '', base)
        if exam:
            return exam, year
    
    # If no year found, return exam only
    if base:
        return base, None
    
    return None, None


def validate_question_format(question: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate if question structure matches its declared format type.
    
    Returns:
        (is_valid, warning_message)
    """
    question_text = str(question.get("question", "")).lower()
    declared_format = str(question.get("format", "single")).lower()
    
    warnings = []
    
    # Check for format-specific patterns
    if declared_format == "match":
        # Match questions should contain "match" or pairing indicators
        if "match" not in question_text and "row" not in question_text:
            warnings.append("Match format declared but question doesn't contain match/pairing indicators")
    elif declared_format == "statement":
        # Statement questions should contain "statement" or "consider the following"
        if "statement" not in question_text and "consider the following" not in question_text:
            warnings.append("Statement format declared but question doesn't contain statement indicators")
    elif declared_format == "assertion":
        # Assertion-Reason questions should contain assertion/reason indicators
        assertion_keywords = ["assertion", "reason", "statement i", "statement ii", "assertion (a)", "reason (r)"]
        if not any(keyword in question_text for keyword in assertion_keywords):
            warnings.append("Assertion format declared but question doesn't contain assertion/reason indicators")
    elif declared_format == "table":
        # Table questions should contain table indicators
        if "table" not in question_text and "row" not in question_text and "column" not in question_text:
            warnings.append("Table format declared but question doesn't contain table indicators")
    elif declared_format == "paragraph":
        # Paragraph questions should be longer
        if len(question_text) < 100:
            warnings.append("Paragraph format declared but question seems too short")
    
    if warnings:
        return False, "; ".join(warnings)
    
    return True, None


def validate_question(question: Dict[str, Any], question_id: str, check_correct_answer: bool = False) -> Tuple[bool, List[str]]:
    """
    Comprehensive validation of question data.
    
    Args:
        question: Question dictionary
        question_id: Question ID for logging
        check_correct_answer: If True, validate correct_answer is not null
    
    Returns:
        (is_valid, list_of_validation_errors)
    """
    errors = []
    
    # Required fields
    if not question.get("question") or not str(question.get("question", "")).strip():
        errors.append("Missing or empty question text")
    
    # Check options
    options = question.get("options", {})
    if not isinstance(options, dict):
        errors.append("Options is not a dictionary")
    else:
        required_options = ["A", "B", "C", "D"]
        missing_options = [opt for opt in required_options if not options.get(opt) or not str(options.get(opt, "")).strip()]
        if missing_options:
            errors.append(f"Missing or empty options: {', '.join(missing_options)}")
    
    # Check correct_answer (only if explicitly requested)
    if check_correct_answer:
        correct_answer = question.get("correct_answer")
        if correct_answer is None or (isinstance(correct_answer, str) and not correct_answer.strip()):
            errors.append("Missing or null correct_answer")
        else:
            # Validate correct_answer format - should be option letter (A, B, C, D) or valid option text
            correct_answer_str = str(correct_answer).strip().upper()
            valid_letters = ["A", "B", "C", "D"]
            
            # Check if it's a valid option letter
            if correct_answer_str not in valid_letters:
                # Check if it matches any option text (case-insensitive)
                option_texts = [str(options.get(opt, "")).strip().upper() for opt in valid_letters if options.get(opt)]
                if correct_answer_str not in option_texts:
                    # Warn but don't error - might be a valid format we don't recognize
                    pass  # Could add warning here if needed
    
    # Check format
    question_format = question.get("format", "")
    valid_formats = ["single", "statement", "match", "table", "assertion", "paragraph"]
    if question_format and question_format not in valid_formats:
        errors.append(f"Invalid format: {question_format} (valid: {', '.join(valid_formats)})")
    
    # Check if extracted successfully
    if not question.get("extracted_successfully", True):
        errors.append("Question marked as not extracted successfully")
    
    return len(errors) == 0, errors


def normalize_correct_answer(correct_answer: Any, options: Dict[str, str]) -> str:
    """
    Normalize correct_answer to option letter (A, B, C, D).
    
    If correct_answer is already a letter, return it.
    If it's option text, find the matching letter.
    Otherwise, return as-is (will be validated elsewhere).
    
    Args:
        correct_answer: The correct answer value (could be letter or text)
        options: Dictionary of options {"A": "...", "B": "...", etc.}
    
    Returns:
        Normalized option letter (A, B, C, D) or original value if can't normalize
    """
    if correct_answer is None:
        return ""
    
    correct_answer_str = str(correct_answer).strip()
    
    # If it's already a valid option letter, return it
    if correct_answer_str.upper() in ["A", "B", "C", "D"]:
        return correct_answer_str.upper()
    
    # Try to match against option text (case-insensitive)
    correct_answer_upper = correct_answer_str.upper()
    for letter, option_text in options.items():
        if option_text and correct_answer_upper == str(option_text).strip().upper():
            return letter
    
    # If no match found, return original (validation will catch if invalid)
    return correct_answer_str


def map_json_to_csv_row(question: Dict[str, Any], exam: Optional[str], year: Optional[int], row_id: int) -> Dict[str, Any]:
    """
    Map JSON question object to CSV row format.
    
    Args:
        question: JSON question object
        exam: Exam name from filename
        year: Year from filename
        row_id: Auto-incrementing row ID
    
    Returns:
        Dictionary with CSV column names as keys
    """
    # Extract options
    options = question.get("options", {})
    
    # Normalize correct_answer to option letter format
    correct_answer = question.get("correct_answer", "")
    normalized_correct = normalize_correct_answer(correct_answer, options)
    
    # Handle keywords - convert list to comma-separated string
    keywords = question.get("keywords", [])
    if isinstance(keywords, list):
        keywords_str = ", ".join(str(k) for k in keywords if k)
    else:
        keywords_str = str(keywords) if keywords else ""
    
    # Map fields to CSV columns
    row = {
        "id": row_id,  # Auto-incrementing ID
        "json_question_id": question.get("id", ""),  # Original JSON question ID for internal mapping
        "question_text": question.get("question", ""),
        "option_a": options.get("A", ""),
        "option_b": options.get("B", ""),
        "option_c": options.get("C", ""),
        "option_d": options.get("D", ""),
        "exam": exam or "",
        "year": year if year is not None else "",
        "question_format": question.get("format", "single"),
        "correct_option": normalized_correct,  # Normalized to option letter
        "subject": question.get("subject", "") or "",
        "topic": question.get("topic", "") or "",
        "sub_topic": question.get("sub_topic", "") or "",
        "keywords": keywords_str
    }
    
    return row


def clean_csv_value(value: Any) -> str:
    """
    Clean and escape CSV value to handle quotes, newlines, and special characters.
    
    Args:
        value: Value to clean
    
    Returns:
        Cleaned string value
    """
    if value is None:
        return ""
    
    # Convert to string
    text = str(value)
    
    # Replace newlines with spaces (or keep them if needed)
    # For CSV, we'll keep newlines but ensure proper escaping
    text = text.strip()
    
    return text


def merge_json_files(
    input_dir: Path, 
    output_path: Path, 
    append: bool = False, 
    validate: bool = False,
    skip_null_answer: bool = True,
    log_rejected_path: Optional[Path] = None,
    pretty_format: bool = False
) -> Dict[str, int]:
    """
    Merge all JSON files from input directory into a single CSV file.
    
    Args:
        input_dir: Directory containing JSON files
        output_path: Path to output CSV file
        append: If True, append to existing CSV; otherwise overwrite
        validate: If True, validate JSON structure before processing
        skip_null_answer: If True, skip questions with null correct_answer
        log_rejected_path: Path to log file for rejected questions
        pretty_format: If True, add blank lines between rows (for readability)
    
    Returns:
        Dictionary with statistics: total_questions, skipped, errors
    """
    stats = {
        "total_questions": 0,
        "skipped": 0,
        "rejected_null_answer": 0,
        "rejected_validation": 0,
        "format_warnings": 0,
        "errors": 0,
        "files_processed": 0
    }
    
    # Find all JSON files
    json_files = list(input_dir.glob("*.json"))
    
    if not json_files:
        print(f"[WARNING] No JSON files found in {input_dir}")
        return stats
    
    print(f"[INFO] Found {len(json_files)} JSON file(s) in {input_dir}")
    
    # CSV column names - id is first, json_question_id is second
    csv_columns = [
        "id", "json_question_id", "question_text", "option_a", "option_b", "option_c", "option_d",
        "exam", "year", "question_format", "correct_option",
        "subject", "topic", "sub_topic", "keywords"
    ]
    
    # Determine starting ID
    start_id = 1
    if append and output_path.exists():
        # Read existing CSV to get the last ID
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    last_id = max(int(row.get("id", 0)) for row in rows if row.get("id", "").isdigit())
                    start_id = last_id + 1
        except Exception as e:
            print(f"[WARNING] Could not read existing CSV to determine starting ID: {e}")
            start_id = 1
    
    # Setup rejected questions log
    rejected_questions = []
    if log_rejected_path is None:
        log_rejected_path = output_path.parent / "rejected_questions.json"
    
    # Determine write mode
    write_mode = "a" if append and output_path.exists() else "w"
    
    # Track row ID
    current_id = start_id
    
    # Open CSV file for writing
    with open(output_path, write_mode, newline='', encoding='utf-8') as csvfile:
        # Use custom writer for pretty formatting if requested
        if pretty_format:
            # For pretty format, we'll write manually with blank lines
            writer = None
        else:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns, quoting=csv.QUOTE_MINIMAL, escapechar='\\')
        
        # Write header only if not appending or file is new
        if write_mode == "w" or not output_path.exists():
            if pretty_format:
                csvfile.write(",".join(csv_columns) + "\n")
            else:
                writer.writeheader()
        
        # Process each JSON file
        for json_file in json_files:
            print(f"[INFO] Processing {json_file.name}...")
            
            try:
                # Extract exam and year from filename
                exam, year = parse_filename(json_file.name)
                if not exam:
                    print(f"  [WARNING] Could not parse exam from filename: {json_file.name}")
                    stats["errors"] += 1
                    continue
                
                print(f"  [INFO] Exam: {exam}, Year: {year if year else 'N/A'}")
                
                # Read JSON file
                with open(json_file, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError as e:
                        print(f"  [ERROR] Failed to parse JSON: {e}")
                        stats["errors"] += 1
                        continue
                
                # Validate structure
                if validate:
                    if not isinstance(data, list):
                        print(f"  [WARNING] JSON file does not contain an array: {json_file.name}")
                        stats["errors"] += 1
                        continue
                
                # Process each question
                file_questions = 0
                file_skipped = 0
                file_rejected_null = 0
                file_rejected_validation = 0
                file_format_warnings = 0
                
                for question in data:
                    question_json_id = question.get("id", "unknown")
                    
                    # Skip if not extracted successfully
                    if not question.get("extracted_successfully", True):
                        file_skipped += 1
                        rejected_questions.append({
                            "json_question_id": question_json_id,
                            "reason": "extracted_successfully is False",
                            "source_file": json_file.name,
                            "timestamp": datetime.now().isoformat()
                        })
                        continue
                    
                    # Check for null correct_answer first (before validation)
                    correct_answer = question.get("correct_answer")
                    has_null_answer = (correct_answer is None or (isinstance(correct_answer, str) and not correct_answer.strip()))
                    
                    if skip_null_answer and has_null_answer:
                        file_rejected_null += 1
                        rejected_questions.append({
                            "json_question_id": question_json_id,
                            "reason": "null_correct_answer",
                            "source_file": json_file.name,
                            "timestamp": datetime.now().isoformat()
                        })
                        continue
                    
                    # Validate question (don't check correct_answer here since we handle it separately)
                    is_valid, validation_errors = validate_question(question, question_json_id, check_correct_answer=False)
                    if not is_valid:
                        file_rejected_validation += 1
                        rejected_questions.append({
                            "json_question_id": question_json_id,
                            "reason": "validation_failed",
                            "errors": validation_errors,
                            "source_file": json_file.name,
                            "timestamp": datetime.now().isoformat()
                        })
                        continue
                    
                    # Validate format
                    format_valid, format_warning = validate_question_format(question)
                    if not format_valid:
                        file_format_warnings += 1
                        print(f"  [WARNING] Format validation for {question_json_id}: {format_warning}")
                    
                    # Map to CSV row
                    row = map_json_to_csv_row(question, exam, year, current_id)
                    current_id += 1
                    
                    # Clean values
                    cleaned_row = {k: clean_csv_value(v) for k, v in row.items()}
                    
                    # Write row
                    if pretty_format:
                        # Write with manual formatting (blank line after each row)
                        # Use csv.writer for proper escaping, but add blank line after
                        row_values = [str(cleaned_row.get(col, "")) for col in csv_columns]
                        # Create a temporary StringIO to use csv.writer for proper escaping
                        temp_buffer = io.StringIO()
                        temp_writer = csv.writer(temp_buffer, quoting=csv.QUOTE_MINIMAL)
                        temp_writer.writerow(row_values)
                        csv_line = temp_buffer.getvalue().rstrip('\r\n')
                        csvfile.write(csv_line + "\n\n")
                    else:
                        writer.writerow(cleaned_row)
                    
                    file_questions += 1
                
                stats["total_questions"] += file_questions
                stats["skipped"] += file_skipped
                stats["rejected_null_answer"] += file_rejected_null
                stats["rejected_validation"] += file_rejected_validation
                stats["format_warnings"] += file_format_warnings
                stats["files_processed"] += 1
                
                print(f"  [SUCCESS] Processed {file_questions} questions")
                if file_skipped > 0:
                    print(f"  [SKIPPED] {file_skipped} questions (extraction failed)")
                if file_rejected_null > 0:
                    print(f"  [REJECTED] {file_rejected_null} questions (null correct_answer)")
                if file_rejected_validation > 0:
                    print(f"  [REJECTED] {file_rejected_validation} questions (validation failed)")
                if file_format_warnings > 0:
                    print(f"  [WARNING] {file_format_warnings} questions (format mismatch)")
                
            except Exception as e:
                print(f"  [ERROR] Error processing {json_file.name}: {e}")
                import traceback
                traceback.print_exc()
                stats["errors"] += 1
                continue
    
    # Write rejected questions log (always write, even if empty, to clear old data)
    try:
        log_rejected_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_rejected_path, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_rejected": len(rejected_questions),
                    "rejected_null_answer": stats["rejected_null_answer"],
                    "rejected_validation": stats["rejected_validation"],
                    "rejected_extraction_failed": stats["skipped"]
                },
                "rejected_questions": rejected_questions
            }, f, indent=2, ensure_ascii=False)
        if rejected_questions:
            print(f"[INFO] Rejected questions logged to: {log_rejected_path}")
        else:
            print(f"[INFO] Rejected questions log cleared (no rejections): {log_rejected_path}")
    except Exception as e:
        print(f"[WARNING] Failed to write rejected questions log: {e}")
    
    print(f"\n[SUMMARY]")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Total questions added: {stats['total_questions']}")
    print(f"  Skipped (extraction failed): {stats['skipped']}")
    print(f"  Rejected (null correct_answer): {stats['rejected_null_answer']}")
    print(f"  Rejected (validation failed): {stats['rejected_validation']}")
    print(f"  Format warnings: {stats['format_warnings']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Output saved to: {output_path}")
    if rejected_questions:
        print(f"  Rejected questions log: {log_rejected_path}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Merge JSON files from data extraction pipeline into CSV format"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="../../ai_pyq/data/questions.csv",
        help="Path to output CSV file (default: ../../ai_pyq/data/questions.csv)"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="output",
        help="Directory containing JSON files (default: output/)"
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing CSV instead of overwriting"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate JSON structure before merging"
    )
    parser.add_argument(
        "--skip-null-answer",
        action="store_true",
        default=True,
        help="Skip questions with null correct_answer (default: True)"
    )
    parser.add_argument(
        "--allow-null-answer",
        action="store_false",
        dest="skip_null_answer",
        help="Allow questions with null correct_answer"
    )
    parser.add_argument(
        "--log-rejected",
        type=str,
        default=None,
        help="Path to log file for rejected questions (default: <output_dir>/rejected_questions.json)"
    )
    parser.add_argument(
        "--pretty-format",
        action="store_true",
        help="Add blank lines between rows for better readability (testing/debugging only)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to script directory
    script_dir = Path(__file__).parent
    input_dir = (script_dir / args.input_dir).resolve()
    
    # Resolve output path relative to script directory if it's a relative path
    if Path(args.output).is_absolute():
        output_path = Path(args.output)
    else:
        output_path = (script_dir / args.output).resolve()
    
    # Resolve log path relative to script directory if it's a relative path
    if args.log_rejected:
        if Path(args.log_rejected).is_absolute():
            log_rejected_path = Path(args.log_rejected)
        else:
            log_rejected_path = (script_dir / args.log_rejected).resolve()
    else:
        log_rejected_path = None
    
    # Ensure input directory exists
    if not input_dir.exists():
        print(f"[ERROR] Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Merge files
    stats = merge_json_files(
        input_dir, 
        output_path, 
        append=args.append, 
        validate=args.validate,
        skip_null_answer=args.skip_null_answer,
        log_rejected_path=log_rejected_path,
        pretty_format=args.pretty_format
    )
    
    if stats["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
