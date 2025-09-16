import pandas as pd
from datetime import datetime, timedelta, timezone

# --- Time Zone Table (ID -> Offset) ---
TIMEZONES = {
    "Dateline Standard Time": "UTC-12:00",
    "UTC-11": "UTC-11:00",
    "Aleutian Standard Time": "UTC-10:00",
    "Hawaiian Standard Time": "UTC-10:00",
    "Marquesas Standard Time": "UTC-09:30",
    "Alaskan Standard Time": "UTC-09:00",
    "UTC-09": "UTC-09:00",
    "Pacific Standard Time (Mexico)": "UTC-08:00",
    "UTC-08": "UTC-08:00",
    "Pacific Standard Time": "UTC-08:00",
    "US Mountain Standard Time": "UTC-07:00",
    "Mountain Standard Time (Mexico)": "UTC-07:00",
    "Mountain Standard Time": "UTC-07:00",
    "Yukon Standard Time": "UTC-07:00",
    "Central America Standard Time": "UTC-06:00",
    "Central Standard Time": "UTC-06:00",
    "Easter Island Standard Time": "UTC-06:00",
    "Central Standard Time (Mexico)": "UTC-06:00",
    "Canada Central Standard Time": "UTC-06:00",
    "SA Pacific Standard Time": "UTC-05:00",
    "Eastern Standard Time (Mexico)": "UTC-05:00",
    "Eastern Standard Time": "UTC-05:00",
    "Haiti Standard Time": "UTC-05:00",
    "Cuba Standard Time": "UTC-05:00",
    "US Eastern Standard Time": "UTC-05:00",
    "Turks And Caicos Standard Time": "UTC-05:00",
    "Atlantic Standard Time": "UTC-04:00",
    "Venezuela Standard Time": "UTC-04:00",
    "Central Brazilian Standard Time": "UTC-04:00",
    "SA Western Standard Time": "UTC-04:00",
    "Pacific SA Standard Time": "UTC-04:00",
    "Newfoundland Standard Time": "UTC-03:30",
    "Tocantins Standard Time": "UTC-03:00",
    "Paraguay Standard Time": "UTC-03:00",
    "E. South America Standard Time": "UTC-03:00",
    "SA Eastern Standard Time": "UTC-03:00",
    "Argentina Standard Time": "UTC-03:00",
    "Montevideo Standard Time": "UTC-03:00",
    "Magallanes Standard Time": "UTC-03:00",
    "Saint Pierre Standard Time": "UTC-03:00",
    "Bahia Standard Time": "UTC-03:00",
    "UTC-02": "UTC-02:00",
    "Greenland Standard Time": "UTC-02:00",
    "Mid-Atlantic Standard Time": "UTC-02:00",
    "Azores Standard Time": "UTC-01:00",
    "Cape Verde Standard Time": "UTC-01:00",
    "UTC": "UTC+00:00",
    "GMT Standard Time": "UTC+00:00",
    "Greenwich Standard Time": "UTC+00:00",
    "Sao Tome Standard Time": "UTC+00:00",
    "Morocco Standard Time": "UTC+01:00",
    "W. Europe Standard Time": "UTC+01:00",
    "Central Europe Standard Time": "UTC+01:00",
    "Romance Standard Time": "UTC+01:00",
    "Central European Standard Time": "UTC+01:00",
    "W. Central Africa Standard Time": "UTC+01:00",
    "GTB Standard Time": "UTC+02:00",
    "Middle East Standard Time": "UTC+02:00",
    "Egypt Standard Time": "UTC+02:00",
    "E. Europe Standard Time": "UTC+02:00",
    "West Bank Standard Time": "UTC+02:00",
    "South Africa Standard Time": "UTC+02:00",
    "FLE Standard Time": "UTC+02:00",
    "Israel Standard Time": "UTC+02:00",
    "South Sudan Standard Time": "UTC+02:00",
    "Kaliningrad Standard Time": "UTC+02:00",
    "Sudan Standard Time": "UTC+02:00",
    "Libya Standard Time": "UTC+02:00",
    "Namibia Standard Time": "UTC+02:00",
    "Jordan Standard Time": "UTC+03:00",
    "Arabic Standard Time": "UTC+03:00",
    "Syria Standard Time": "UTC+03:00",
    "Turkey Standard Time": "UTC+03:00",
    "Arab Standard Time": "UTC+03:00",
    "Belarus Standard Time": "UTC+03:00",
    "Russian Standard Time": "UTC+03:00",
    "E. Africa Standard Time": "UTC+03:00",
    "Volgograd Standard Time": "UTC+03:00",
    "Iran Standard Time": "UTC+03:30",
    "Arabian Standard Time": "UTC+04:00",
    "Astrakhan Standard Time": "UTC+04:00",
    "Azerbaijan Standard Time": "UTC+04:00",
    "Russia Time Zone 3": "UTC+04:00",
    "Mauritius Standard Time": "UTC+04:00",
    "Saratov Standard Time": "UTC+04:00",
    "Georgian Standard Time": "UTC+04:00",
    "Caucasus Standard Time": "UTC+04:00",
    "Afghanistan Standard Time": "UTC+04:30",
    "West Asia Standard Time": "UTC+05:00",
    "Qyzylorda Standard Time": "UTC+05:00",
    "Ekaterinburg Standard Time": "UTC+05:00",
    "Pakistan Standard Time": "UTC+05:00",
    "India Standard Time": "UTC+05:30",
    "Sri Lanka Standard Time": "UTC+05:30",
    "Nepal Standard Time": "UTC+05:45",
    "Central Asia Standard Time": "UTC+06:00",
    "Bangladesh Standard Time": "UTC+06:00",
    "Omsk Standard Time": "UTC+06:00",
    "Myanmar Standard Time": "UTC+06:30",
    "SE Asia Standard Time": "UTC+07:00",
    "Altai Standard Time": "UTC+07:00",
    "W. Mongolia Standard Time": "UTC+07:00",
    "North Asia Standard Time": "UTC+07:00",
    "N. Central Asia Standard Time": "UTC+07:00",
    "Tomsk Standard Time": "UTC+07:00",
    "China Standard Time": "UTC+08:00",
    "North Asia East Standard Time": "UTC+08:00",
    "Singapore Standard Time": "UTC+08:00",
    "W. Australia Standard Time": "UTC+08:00",
    "Taipei Standard Time": "UTC+08:00",
    "Ulaanbaatar Standard Time": "UTC+08:00",
    "Aus Central W. Standard Time": "UTC+08:45",
    "Transbaikal Standard Time": "UTC+09:00",
    "Tokyo Standard Time": "UTC+09:00",
    "North Korea Standard Time": "UTC+09:00",
    "Korea Standard Time": "UTC+09:00",
    "Yakutsk Standard Time": "UTC+09:00",
    "Cen. Australia Standard Time": "UTC+09:30",
    "AUS Central Standard Time": "UTC+09:30",
    "E. Australia Standard Time": "UTC+10:00",
    "AUS Eastern Standard Time": "UTC+10:00",
    "West Pacific Standard Time": "UTC+10:00",
    "Tasmania Standard Time": "UTC+10:00",
    "Vladivostok Standard Time": "UTC+10:00",
    "Lord Howe Standard Time": "UTC+10:30",
    "Bougainville Standard Time": "UTC+11:00",
    "Russia Time Zone 10": "UTC+11:00",
    "Magadan Standard Time": "UTC+11:00",
    "Norfolk Standard Time": "UTC+11:00",
    "Sakhalin Standard Time": "UTC+11:00",
    "Central Pacific Standard Time": "UTC+11:00",
    "Russia Time Zone 11": "UTC+12:00",
    "New Zealand Standard Time": "UTC+12:00",
    "UTC+12": "UTC+12:00",
    "Fiji Standard Time": "UTC+12:00",
    "Kamchatka Standard Time": "UTC+12:00",
    "Chatham Islands Standard Time": "UTC+12:45",
    "UTC+13": "UTC+13:00",
    "Tonga Standard Time": "UTC+13:00",
    "Samoa Standard Time": "UTC+13:00",
    "Line Islands Standard Time": "UTC+14:00",
}

# --- Convert UTC offset string to datetime.timezone ---
def parse_offset(offset_str):
    sign = 1 if "+" in offset_str else -1
    parts = offset_str.replace("UTC", "").replace("+", "").replace("-", "").split(":")
    hours = int(parts[0]) if parts[0] else 0
    minutes = int(parts[1]) if len(parts) > 1 else 0
    return timezone(sign * timedelta(hours=hours, minutes=minutes))

# --- Show menu ---
def choose_timezone():
    tz_list = list(TIMEZONES.keys())
    for i, tz in enumerate(tz_list, start=1):
        print(f"{i}) {tz} ({TIMEZONES[tz]})")
    choice = int(input("\nEnter the number of target timezone: "))
    return tz_list[choice - 1]

# --- Main ---
def main():
    # Step 1: read CSV
    df = pd.read_csv("dates.csv")

    # Step 2: ask user to choose timezone
    target_tz_name = choose_timezone()
    target_tz = parse_offset(TIMEZONES[target_tz_name])

    # Step 3: convert each datetime
    results = []
    for d in df["datetime"]:
        dt = datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
        # assume input is UTC
        dt_utc = dt.replace(tzinfo=timezone.utc)
        dt_target = dt_utc.astimezone(target_tz)
        results.append({
            "original_date": d,
            "notion_upload_date": dt_target.strftime("%Y-%m-%d %H:%M:%S"),
            "google_sheet": dt_target.strftime("%d/%m/%Y %H:%M:%S")
        })

    # Step 4: save results
    out_df = pd.DataFrame(results)
    out_df.to_csv("outputdates.csv", index=False)
    print("\n✅ Conversion complete! Results saved to output.csv")

if __name__ == "__main__":
    main()
