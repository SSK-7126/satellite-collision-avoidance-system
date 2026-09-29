from sgp4.api import Satrec
from datetime import datetime, timedelta, timezone
import csv

from data_loader import load_tle_data


def create_satellite(tle_line1, tle_line2):
    """Create an SGP4 satellite object from TLE lines."""
    return Satrec.twoline2rv(tle_line1, tle_line2)


def propagate_object(satellite, name, time):
    """
    Propagate one object to a specific UTC time.

    Returns position in km and velocity in km/s.
    """

    # Convert Python datetime to Julian Date
    from sgp4.api import jday

    jd, fr = jday(
        time.year,
        time.month,
        time.day,
        time.hour,
        time.minute,
        time.second + time.microsecond / 1_000_000
    )

    error_code, position, velocity = satellite.sgp4(jd, fr)

    if error_code != 0:
        raise RuntimeError(
            f"SGP4 propagation failed for {name}. "
            f"Error code: {error_code}"
        )

    return position, velocity


def main():

    # Load our real TLE data
    objects = load_tle_data("data/orbital_data.txt")

    # Create SGP4 objects
    satellites = {}

    for obj in objects:
        satellites[obj["name"]] = create_satellite(
            obj["line1"],
            obj["line2"]
        )

    # Use the CARTOSAT-3 TLE epoch as our starting time
    satellite = satellites["CARTOSAT-3"]

    jd = satellite.jdsatepoch
    fr = satellite.jdsatepochF

    # Convert Julian date to a Python datetime
    from sgp4.api import days2mdhms

    year = satellite.epochyr + 2000

    month, day, hour, minute, second = days2mdhms(
        year,
        satellite.epochdays
    )

    start_time = datetime(
        year,
        month,
        day,
        hour,
        minute,
        int(second),
        tzinfo=timezone.utc
    )

    print("\nPROPAGATING OBJECTS")
    print("=" * 60)
    print(f"Start time: {start_time}")
    print("Duration: 60 minutes")
    print("Time step: 1 minute")

    # Prepare CSV output
    output_file = "output/orbital_states.csv"

    with open(output_file, "w", newline="") as csvfile:

        writer = csv.writer(csvfile)

        writer.writerow([
            "time",
            "object",
            "x_km",
            "y_km",
            "z_km",
            "vx_km_s",
            "vy_km_s",
            "vz_km_s"
        ])

        # 61 points = 0 through 60 minutes
        for minute in range(61):

            current_time = start_time + timedelta(
                minutes=minute
            )

            for obj in objects:

                name = obj["name"]

                position, velocity = propagate_object(
                    satellites[name],
                    name,
                    current_time
                )

                writer.writerow([
                    current_time.isoformat(),
                    name,
                    f"{position[0]:.6f}",
                    f"{position[1]:.6f}",
                    f"{position[2]:.6f}",
                    f"{velocity[0]:.8f}",
                    f"{velocity[1]:.8f}",
                    f"{velocity[2]:.8f}"
                ])

    print("\nPropagation complete!")
    print(f"Saved results to: {output_file}")


if __name__ == "__main__":
    main()