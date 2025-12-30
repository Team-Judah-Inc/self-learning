import random
from faker import Faker

fake = Faker()
Faker.seed(12345)

def get_consistent_company(user_id: str) -> str:
    """Generates a stable company name based on the User ID seed."""
    try: seed_val = int(user_id.split('_')[1])
    except: seed_val = hash(user_id)
    temp_fake = Faker()
    temp_fake.seed_instance(seed_val)
    return f"{temp_fake.company()} {temp_fake.company_suffix()}"

def pick_weighted_category(config: dict) -> str:
    cats_dict = config['probabilities']['categories']
    return random.choices(list(cats_dict.keys()), weights=list(cats_dict.values()), k=1)[0]

def pick_location(home_city: str, config: dict) -> str:
    chance = config['probabilities']['home_location_chance']
    return home_city if random.random() < chance else fake.city()