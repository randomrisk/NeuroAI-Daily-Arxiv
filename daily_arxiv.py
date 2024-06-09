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
            "update_time": str(result.updated.date()),
            "abstract": result.summary.replace('\n', ' ')  # 获取摘要并去除换行符
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
        f.write(f"<h2 style='font-family: Helvetica, Arial, sans-serif; font-size: 16px; color: #4a4a4a;'>Updated on {datetime.date.today()}</h2>\n\n")
        for topic, papers in data.items():
            f.write(f"<h3 style='font-family: Helvetica, Arial, sans-serif; font-size: 14px; color: #2a7ae2;'>{topic}</h3>\n\n")
            f.write("<table style='width: 100%; border-collapse: collapse; font-family: Helvetica, Arial, sans-serif; font-size: 12px;'>\n")
            f.write("<thead style='background-color: #f4f4f4;'>\n")
            f.write("<tr style='border-bottom: 2px solid #d4d4d4;'>\n")
            f.write("<th style='padding: 8px; text-align: left;'>Publish Date</th>\n")
            f.write("<th style='padding: 8px; text-align: left;'>Title</th>\n")
            f.write("<th style='padding: 8px; text-align: left;'>Authors</th>\n")
            f.write("<th style='padding: 8px; text-align: left;'>URL</th>\n")
            f.write("<th style='padding: 8px; text-align: left;'>Abstract</th>\n")
            f.write("</tr>\n")
            f.write("</thead>\n")
            f.write("<tbody>\n")
            for paper_id, details in papers.items():
                f.write("<tr style='border-bottom: 1px solid #d4d4d4;'>\n")
                f.write(f"<td style='padding: 8px;'>{details['update_time']}</td>\n")
                f.write(f"<td style='padding: 8px;'>{details['title']}</td>\n")
                f.write(f"<td style='padding: 8px;'>{details['authors']}</td>\n")
                f.write(f"<td style='padding: 8px;'><a href='{details['url']}' style='color: #1a73e8;'>Link</a></td>\n")
                f.write(f"<td style='padding: 8px;'>{details['abstract']}</td>\n")
                f.write("</tr>\n")
            f.write("</tbody>\n")
            f.write("</table>\n\n")

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
