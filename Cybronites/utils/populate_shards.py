import sqlite3
import os
import sys
import torch
from sqlite3 import Error
from datetime import datetime

# Add project root to path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from Cybronites.client.dataset import load_data

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

def populate_shards():
    database = os.path.join(root_dir, "Cybronites", "guardian.db")
    conn = create_connection(database)
    if not conn:
        return

    cur = conn.cursor()
    # Clear existing shards
    cur.execute("DELETE FROM shards")

    orgs = ['MedCenter Alpha', 'FinGroup Beta', 'GovService Gamma', 'EduTrust Delta', 'TechOps Epsilon', 'Hospital Zeta', 'Retail Omega', 'Logistics Sigma']
    num_clients = len(orgs)

    print(f"Populating shards for {num_clients} nodes...")

    for i in range(num_clients):
        # Load real data to get statistics
        train_loader, _ = load_data(client_id=i, num_clients=num_clients)
        dataset = train_loader.dataset
        
        sample_count = len(dataset)
        # Size in MB (approximate: 28x28 grayscale image is ~784 bytes)
        size_mb = (sample_count * 784) / (1024 * 1024)
        
        # Calculate density (unique classes)
        targets = []
        for _, target in train_loader:
            targets.extend(target.tolist())
        unique_classes = len(set(targets))
        density = int((unique_classes / 10) * 100) # MNIST has 10 classes

        shard_id = f"MNIST-{i+1:03d}"
        org = orgs[i]
        shard_type = "Vision/MNIST"
        date = datetime.now().strftime("%b %d, %Y")

        sql = ''' INSERT INTO shards(id, org, size, density, type, date)
                  VALUES(?,?,?,?,?,?) '''
        cur.execute(sql, (shard_id, org, int(sample_count), density, shard_type, date))
        print(f"  - Registered {shard_id} for {org}: {sample_count} samples, {density}% density")

    conn.commit()
    conn.close()
    print("Database sync complete.")

if __name__ == '__main__':
    populate_shards()
