import arxiv
import requests
import json
import datetime
import yaml
import os

BASE_URL = "https://arxiv.paperswithcode.com/api/v0/papers/"

def load_config(config_file="config.yaml"):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def get_authors(authors):
    return ", ".join(str(author) for author in authors)

def get_daily_papers(topic, query, max_results=10):
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    results = client.results(search)
    papers = {}
    for result in results:
        paper_id = result.get_short_id()
        paper_info = {
            "title": result.title,
            "url": result.entry_id,
            "authors": get_authors(result.authors),
            "update_time": str(result.updated.date())
        }
        try:
            r = requests.get(BASE_URL + paper_id).json()
            if "official" in r and r["official"]:
                paper_info["code_url"] = r["official"]["url"]
        except:
            paper_info["code_url"] = None
        papers[paper_id] = paper_info
    return {topic: papers}

def save_json_file(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def json_to_md(json_file, md_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    with open(md_file, 'w') as f:
        f.write(f"## Updated on {datetime.date.today()}\n\n")
        for topic, papers in data.items():
            f.write(f"### {topic}\n\n")
            f.write("| Publish Date | Title | Authors | URL | Code URL |\n")
            f.write("|--------------|-------|---------|-----|----------|\n")
            for paper_id, details in papers.items():
                f.write(f"| {details['update_time']} | {details['title']} | {details['authors']} | [Link]({details['url']}) | [Code]({details['code_url']}) |\n")
            f.write("\n")

def main():
    config = load_config()
    keywords = config['keywords']
    max_results = config['max_results']
    data_store_path = config['data_store_path']
    readme_path = config['readme_path']
    
    os.makedirs(data_store_path, exist_ok=True)
    
    all_data = {}
    for keyword in keywords:
        data = get_daily_papers(keyword, keyword, max_results)
        all_data.update(data)
    
    date_str = datetime.date.today().strftime('%Y-%m-%d')
    json_path = os.path.join(data_store_path, f"papers_{date_str}.json")
    save_json_file(all_data, json_path)
    json_to_md(json_path, readme_path)

if __name__ == "__main__":
    main()
