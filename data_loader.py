from pathlib import Path


def load_tle_data(filename):
    """
    Load 3-line TLE records from a text file.
    """

    filepath = Path(filename)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    lines = [
        line.strip()
        for line in filepath.read_text().splitlines()
        if line.strip()
    ]

    if len(lines) % 3 != 0:
        raise ValueError(
            "TLE file must contain groups of exactly 3 lines."
        )

    objects = []

    for i in range(0, len(lines), 3):
        name = lines[i]
        line1 = lines[i + 1]
        line2 = lines[i + 2]

        objects.append({
            "name": name,
            "line1": line1,
            "line2": line2
        })

    return objects


# Test the data loader
if __name__ == "__main__":

    data_file = "data/orbital_data.txt"

    objects = load_tle_data(data_file)

    print(f"Loaded {len(objects)} objects:\n")

    for obj in objects:
        print(f"Name: {obj['name']}")
        print(f"TLE 1: {obj['line1']}")
        print(f"TLE 2: {obj['line2']}")
        print()