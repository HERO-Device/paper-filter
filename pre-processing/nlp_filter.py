import pandas as pd
import openai
import time
import os
import sys
from pathlib import Path
from tqdm import tqdm
import json
from dotenv import load_dotenv

load_dotenv(".env")

INCLUSION_CRITERIA = """
Include papers that:
- Focus on neurodegenerative disease monitoring (Parkinson's, Alzheimer's, dementia)
- Involve EEG, eye tracking, or biomedical sensors
- Discuss wearable monitoring devices or systems
- Cover machine learning/AI for health monitoring
- Relate to early detection or diagnosis of neurological conditions
"""

EXCLUSION_CRITERIA = """
Exclude papers that:
- Are purely pharmacological interventions or drug trials
- Focus only on animal studies (no human relevance)
- Are review papers, surveys, or meta-analyses
- Don't involve monitoring, detection, or sensing technology
- Are about unrelated diseases (cancer, diabetes, etc.)
"""

PROJECT_DESCRIPTION = """
The H.E.R.O. System is a biomedical monitoring device that combines EEG and 
eye tracking to monitor neurodegenerative diseases like Parkinson's and 
Alzheimer's. We're researching wearable health monitoring, biosignal processing, 
and early detection methods for neurological conditions.
"""

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))

def setup_openai():
    """Setup OpenAI API key from environment"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found, set it in your .env file")

    openai.apikey = api_key
    print("OpenAI API key loaded")
    print(f"Using model: {OPENAI_MODEL}")

def create_prompt(title, abstract):
    """Generates a prompt for OpenAI to evaluate paper relevance"""
    prompt = f"""You are a research assistant helping with a literature review for a medical device for monitoring.
    
Project Context:
{PROJECT_DESCRIPTION}
Inclusion Criteria:
{INCLUSION_CRITERIA}
Exclusion Criteria:
{EXCLUSION_CRITERIA}
    
Paper to Evaluate:
Title: {title}
Abstract: {abstract if pd.notna(abstract) else "No abstract available"}
    
Task:
Based on the title and abstract, decide if this paper should be kept for manual review or rejected.

Respond ONLY with a JSON object in this exact format:
{{
    "decision" : "keep" or "reject",
    "confidence" : "high" or "medium" or "low"
}}
    
Be strict - when in doubt about relevance reject. We want high-quality relevant papers only.
"""
    return prompt

def evaluate_paper(title, abstract, retry_count=3):
    """
    Uses OpenAI API to evaluate whether a paper should be kept or rejected

    :param title: (str) Paper title
    :param abstract: (str) Paper abstract
    :param retry_count: (int) no.of retries or failure.
    :return: (Dict) with keys: decision, confidence, reason
    """

    prompt = create_prompt(title, abstract)

    for attempt in range(retry_count):
        try:
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content":"You are a research paper filter assistant. Always respond with valid JSON only."},
                    {"role": "user", "content":prompt}
                ],
                temperature=0.2,
                max_tokens=150,
            )

            result_text = response.choices[0].messages.content.strip()

            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            result_text = result_text.strip()

            result = json.loads(result_text)

            if "decision" not in result or result["decision"] not in ["keep", "reject"]:
                raise ValueError("Invalid decision format")
            return result

        except json.JSONDecodeError:
            print(f"Could not parse JSON attempt {attempt + 1}/{retry_count}")
            if attempt == retry_count-1:
                return {
                    "decision": "reject",
                    "confidence": "low"
                }
        except Exception as e:
            print(f"Error on attempt {attempt + 1}/{retry_count}: {e}")
            if attempt == retry_count-1:
                return{
                    "decision": "reject",
                    "confidence": "low"
                }
            time.sleep(2 ** attempt)

    return None

def filter_papers(input_csv, output_dir="filtered_results"):
    """
    Mian function for filtering papers using OpenAI API
    :param input_csv: Path to CSV with papers
    :param output_dir: Path to directory to save results
    :return: (tuple) keep_df and reject_df
    """

    setup_openai()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("Loading papers...")
    df = pd.read_csv(input_csv)
    print(f"\n Loaded {len(df):,} papers")

    title_col = None
    abstract_col = None

    for col in df.columns:
        col_lower = col.lower()
        if 'title' in col_lower and title_col is None:
            title_col = col
        if 'abstract' in col_lower and abstract_col is None:
            abstract_col = col

    if title_col is None:
        raise ValueError("Could not find 'Title' column in CSV")

    print(f" Title column: '{title_col}'")
    if abstract_col:
        print(f" Abstract column: '{abstract_col}'")
    else:
        print("No abstract column found. Filtering based on titles only.")
        df['Abstract'] = None
        abstract_col = 'Abstract'

    df['nlp_decision'] = None
    df['nlp_confidence'] = None

    progress_file = output_path / 'progress.csv'
    start_idx = 0

    if progress_file.exists():
        print("\nFound existing progress file. Resuming...")
        df_progress = pd.read_csv(progress_file)
        df.update(df_progress)
        start_idx = df['nlp_decision'].notna().sum()
        print(f"Resuming from paper {start_idx + 1}/{len(df)}")

    remaining = len(df) - start_idx
    estimated_cost_min = remaining * 0.003
    estimated_cost_max = remaining * 0.01

    print("\nProcessing Configuration")
    print(f"Papers to process: {remaining:,}")
    print(f"Model: {OPENAI_MODEL}")
    print(f"Estimated cost: ${estimated_cost_min:.2f} - ${estimated_cost_max:.2f}")
    print(f"Estimated time: {remaining * 0.5 / 60:.1f} - {remaining * 1.0 / 60:.1f} minutes")
    print("=" * 60)


    if start_idx == 0:
        response = input("\nPress Enter to start filtering (Ctrl+C to cancel)... ")

    print("\nStarting Paper Filtering")

    for idx in tqdm(range(start_idx, len(df)), desc="Filtering papers"):
        row = df.iloc[idx]
        title = row[title_col]
        abstract = row[abstract_col] if pd.notna(row[abstract_col]) else ""

        result = evaluate_paper(title, abstract)

        if result:
            df.at[idx, 'nlp_decision'] = result['decision']
            df.at[idx, 'nlp_confidence'] = result.get('confidence', 'unknown')

        # Save progress every BATCH_SIZE papers
        if (idx + 1) % BATCH_SIZE == 0:
            df.to_csv(progress_file, index=False)
            kept_so_far = (df['nlp_decision'] == 'keep').sum()
            rejected_so_far = (df['nlp_decision'] == 'reject').sum()
            print(f"\nProgress saved at {idx + 1}/{len(df)} | Keep: {kept_so_far} | Reject: {rejected_so_far}")

        time.sleep(0.5)

    df.to_csv(progress_file, index=False)

    keep_df = df[df['nlp_decision'] == 'keep'].copy()
    reject_df = df[df['nlp_decision'] == 'reject'].copy()

    keep_df.to_csv(output_path / 'keep.csv', index=False)
    reject_df.to_csv(output_path / 'reject.csv', index=False)

    print("\nFILTERING COMPLETE")
    print(f"Total papers processed: {len(df):,}")
    print(f"Papers to KEEP: {len(keep_df):,} ({len(keep_df) / len(df) * 100:.1f}%)")
    print(f"Papers to REJECT: {len(reject_df):,} ({len(reject_df) / len(df) * 100:.1f}%)")

    if len(keep_df) > 0:
        print(f"\nConfidence breakdown (KEEP):")
        print(keep_df['nlp_confidence'].value_counts().to_string())

    print(f"\nResults saved to: {output_path}/")
    print(f"  ├── keep.csv ({len(keep_df):,} papers)")
    print(f"  ├── reject.csv ({len(reject_df):,} papers)")
    print(f"  └── progress.csv (full results)")

    return keep_df, reject_df


def main():
    """Main function for command-line usage"""

    if len(sys.argv) < 2:
        print("Usage: python nlp_filter.py <input_csv> [output_dir]")
        print("\nExample:")
        print("  python nlp_filter.py ../data/processed/deduplicated.csv")
        print("  python nlp_filter.py ../data/processed/deduplicated.csv ../data/processed/")
        print("\nMake sure to set your OpenAI API key in .env file:")
        print("  OPENAI_API_KEY=sk-your-key-here")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "filtered_results"

    if not Path(input_csv).exists():
        print(f"✗ Error: File not found: {input_csv}")
        sys.exit(1)

    try:
        filter_papers(input_csv, output_dir)

        print("\nFiltering complete!")
        print(f"  python csv_to_postgres.py {output_dir}/keep.csv")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        print("Progress has been saved. Run again to resume from where you left off.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
