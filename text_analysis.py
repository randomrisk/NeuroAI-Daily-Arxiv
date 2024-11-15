import os
import json
import datetime
import logging
from glob import glob
from typing import List
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
with open("config.json") as config_file:
    config = json.load(config_file)
    api_key = config.get("api_key")

if not api_key:
    raise ValueError("API key not found in config.json")

client = OpenAI(api_key=api_key)

# Generate analysis prompt
def create_analysis_prompt(papers_data: List[dict]) -> str:
    return """
    Analyze the following NeuroAI research papers from arXiv. Provide a comprehensive analysis report following these guidelines:

    1. For each paper:
       - Extract clear problem statement and solution approach
       - Identify key technical innovations
       - Note limitations and proposed future work
       - Assess potential impact on the field

    2. Overall Trend Analysis:
       - Identify major themes and patterns across papers
       - Highlight emerging technical approaches
       - Note shifts in research focus
       - Identify gaps in current research

    3. Historical Context & Recommendations:
       - Identify foundational papers related to these works
       - Recommend key papers that provide important background
       - Focus on highly-cited works that laid groundwork
       - Consider both recent and classical contributions

    4. Future Research Predictions:
       - Project potential research directions based on current trends
       - Identify leading research groups likely to pursue each direction
       - Consider required technical breakthroughs
       - Assess potential impact and timeline
       - Ground predictions in current capabilities and limitations

    5. Novel Research Combinations:
       - Identify synergies between current papers
       - Suggest novel combinations of techniques
       - Highlight potential breakthrough applications
       - Consider technical feasibility

    Base all analysis on concrete evidence from the papers and broader research context.
    Provide specific technical details and justifications for all observations.

    Papers to analyze:
    """ + json.dumps(papers_data, indent=2)

# Load and merge JSON files from data_store
def load_and_merge_json_files(data_store: str) -> List[dict]:
    """
    Load and merge JSON files based on date conditions:
    - If today is Sunday, load the past week's files.
    - Otherwise, load the files from the past two days.

    Args:
        data_store (str): Path to the directory containing JSON files.

    Returns:
        List[dict]: Merged list of detailed paper data from the selected JSON files.
    """
    today = datetime.date.today()
    day_of_week = today.weekday()  # Monday is 0, Sunday is 6

    # Determine date range
    if day_of_week == 6:  # Sunday
        start_date = today - datetime.timedelta(days=7)
        logger.info("Today is Sunday. Loading files from the past week.")
    else:
        start_date = today - datetime.timedelta(days=2)
        logger.info("Loading files from the past two days.")

    files = glob(os.path.join(data_store, 'papers_*.json'))
    all_data = []

    for file_path in files:
        file_date_str = os.path.basename(file_path)[7:17]
        try:
            file_date = datetime.datetime.strptime(file_date_str, '%Y-%m-%d').date()
            # Include files that are within the specified date range
            if start_date <= file_date <= today:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    for category, papers in data.items():
                        for paper_id, paper_info in papers.items():
                            # Collect all information for each paper
                            paper_data = {
                                "id": paper_id,
                                "title": paper_info.get("title", ""),
                                "url": paper_info.get("url", ""),
                                "authors": paper_info.get("authors", ""),
                                "update_time": paper_info.get("update_time", ""),
                                "abstract": paper_info.get("abstract", "")
                            }
                            all_data.append(paper_data)
        except ValueError:
            logger.warning(f"Skipping file with unexpected date format: {file_path}")

    if not all_data:
        logger.warning("No valid data found in the specified date range.")
    else:
        logger.info(f"Loaded {len(all_data)} entries from files within the date range.")

    return all_data

# Analyze research papers and generate Markdown report
def analyze_research_trends(data: List[dict], output_file: str):
    prompt = create_analysis_prompt(data)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI research analyst specializing in NeuroAI."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=3000
    )

    # Check if response has content
    if not response.choices or not response.choices[0].message.content:
        logger.error("API response is empty or not in the expected format.")
        raise ValueError("Received empty or invalid response from the API")

    # Save content as Markdown file
    with open(output_file, 'w') as f:
        f.write("# NeuroAI Research Analysis Report\n\n")
        f.write(f"Generated on {datetime.date.today().strftime('%Y-%m-%d')}\n\n")
        f.write(response.choices[0].message.content)

    logger.info(f"Markdown report saved to {output_file}")

# Main function
def main(config):
    data_store_path = config.get("data_store")
    data_analysis_path = config.get("data_analysis")

    # Check for missing paths
    if not data_store_path or not data_analysis_path:
        logger.error("Both 'data_store' and 'data_analysis' paths must be specified in config.json.")
        return

    # Create output directory if it doesn't exist
    os.makedirs(data_analysis_path, exist_ok=True)

    # Load and merge JSON data
    data = load_and_merge_json_files(data_store_path)
    if not data:
        logger.error("No data loaded for analysis.")
        return

    # Generate and save analysis report
    md_path = os.path.join(data_analysis_path, f"research_analysis_{datetime.date.today().strftime('%Y-%m-%d')}.md")
    analyze_research_trends(data, md_path)

if __name__ == "__main__":
    main(config)