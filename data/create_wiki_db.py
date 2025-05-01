import os
import subprocess
import sqlite3
import json

def run_wikiextractor(xml_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    print("Running WikiExtractor...")
    subprocess.run([
        "python", "-m", "wikiextractor.WikiExtractor", xml_path,
        "-o", output_dir, "--json"
    ], check=True)
    print("WikiExtractor finished.")


def add_json_extension_to_files(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            if not os.path.splitext(filename)[1]:
                new_file_path = file_path + '.json'
                os.rename(file_path, new_file_path)
    print("Renamed files.")


def create_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- AUTOINCREMENT, starts from 1 by default
            org_id INTEGER,                        -- original id from data
            revid INTEGER,
            url TEXT,
            title TEXT,
            text TEXT
        )
    ''')
    conn.commit()
    return conn


def insert_json_files_to_db(conn, directory):
    c = conn.cursor()
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.json'):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            # dodaj tylko jeśli 'text' nie jest pusty lub None
                            if data.get('text'):
                                c.execute('''
                                    INSERT OR IGNORE INTO articles (org_id, revid, url, title, text)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (
                                    int(data.get('id')) if data.get('id') is not None else None,  # org_id
                                    int(data.get('revid')) if data.get('revid') is not None else None,
                                    data.get('url'),
                                    data.get('title'),
                                    data.get('text')
                                ))
                        except Exception as e:
                            print(f"Error in {file_path}: {e}")
    conn.commit()


def main(xml_path, db_path, extracted_dir='./extracted'):
    run_wikiextractor(xml_path, extracted_dir)
    add_json_extension_to_files(extracted_dir)
    conn = create_db(db_path)
    insert_json_files_to_db(conn, extracted_dir)
    conn.close()

if __name__ == '__main__':
    main('./input/wiki.xml', 'wiki.db')