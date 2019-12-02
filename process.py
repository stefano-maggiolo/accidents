import pandas as pd
import numpy as np
import os


# How large is each subdivision, in minutes.
QUANT_MINUTES = 60


STATES_TO_EXCLUDE = [
    1, # AK Alaska, due to the high latitude
    4, # AZ Arizona, due to lack of DST and Navajo Nation
    # 12, # FL Florida, second timezone is big, but scarcely populated
    15, # HI Hawaii, due to lack of DST
    16, # ID Idaho, second timezone is big
    18, # IN Indiana, second timezone is big
    20, # KS Kansas, second timezone is big
    21, # KY Kentucky, second timezone is big
    # 26, # MI Michigan, second timezone is big but scarcely populated
    31, # NE Nebraska, second timezone is big
    38, # ND North Dakota, second timezone is big
    # 41, # OR Oregon, second timezone is big, but scarcely populated
    46, # SD South Dakota, second timezone is big
    47, # TN Tennessee, second timezone is big
    # 48, # TX Texas, second timezone is relatively small
]


def read_timezones():
  """Return timezones for each states as a dataframe with columns:
  STATE_ALPHA    object
  TZ_NO_DST     float64
  TZ_DST        float64
  NOTE           object

  """
  print("Reading timezones.csv...")
  return pd.read_csv("raw/timezones.csv").astype({
      "TZ_NO_DST": "float64",
      "TZ_DST": "float64",
  })


def read_timezone_override():
  """Return timezones for exceptional counties as a dataframe with columns:
  STATE            int64
  COUNTY           int64
  STATE_ALPHA     object
  COUNTY_NAME     object
  TZ_NO_DST      float64
  TZ_DST         float64

  """
  print("Reading counties_timezone_override.csv...")
  tz_override = pd.read_csv("raw/counties_timezone_override.csv").astype({
      "TZ_NO_DST": "float64",
      "TZ_DST": "float64"
  })
  return tz_override


def read_dst():
  """Return DST change dates as a dataframe with columns:
  TIME         datetime64[ns]
  DST_DELTA             int64

  where delta is +1 for solar time to DST transition, and -1 else.

  """
  print("Reading dst.csv...")
  dst = pd.read_csv("raw/dst.csv")
  dst["TIME"] = pd.to_datetime(dst["DATE"])
  dst = dst[["TIME", "DST_DELTA"]]
  return dst


def read_states():
  """Return state info as a dataframe with columns:
  STATE            int64
  STATE_ALPHA     object

  """
  print("Reading _states.csv...")
  return pd.read_csv("derived/_states.csv").astype({
      "STATE": "int32",
  })


def read_counties():
  """Return county info as a dataframe with columns:
  STATE            int32
  COUNTY           int32
  STATE_ALPHA     object
  COUNTY_NAME     object
  LAT            float64
  LNG            float64

  """
  print("Reading _counties.csv...")
  return pd.read_csv("derived/_counties.csv").astype({
      "STATE": "int32",
      "COUNTY": "int32"
  })


def read_accidents():
  """Read a processed accident file, return a single dataframe with columns
  STATE                 float64
  STATE_ALPHA            object
  YEAR                    int32
  MONTH                   int32
  DAY                     int32
  HOUR                    int32
  MINUTE                  int32
  ST_CASE                 int32
  LAT                   float64
  LNG                   float64

  """
  print("Reading _accidents.csv...")
  return pd.read_csv("derived/_accidents.csv")


def read_geolocation():
  """Return state info as a dataframe with columns:
  STATE            int32
  STATE_ALPHA     object
  and county info as a dataframe with columns:
  STATE            int32
  COUNTY           int32
  STATE_ALPHA     object
  COUNTY_NAME     object
  LAT            float64
  LNG            float64

  """
  print("Reading geolocation.csv...")
  geolocation = pd.read_csv("raw/geolocation.psv", sep="|")
  geolocation = geolocation.rename(columns={
      "STATE_NUMERIC": "STATE",
      "COUNTY_NUMERIC": "COUNTY",
      "PRIM_LAT_DEC": "LAT",
      "PRIM_LONG_DEC": "LNG",
  })
  geolocation = geolocation[pd.notna(geolocation["COUNTY"])]
  geolocation = geolocation.astype({
      "STATE": "int32",
      "COUNTY": "int32",
  })
  counties = geolocation[
      ["STATE", "COUNTY", "STATE_ALPHA", "COUNTY_NAME", "LAT", "LNG"]].groupby(
          ["STATE", "COUNTY", "STATE_ALPHA", "COUNTY_NAME"]).mean().reset_index()
  states = counties[["STATE", "STATE_ALPHA"]].drop_duplicates()
  return states, counties


def read_raw_accidents(states, counties, states_to_exclude=None):
  """Read all accident files, return a single dataframe with columns
  STATE                   int32
  STATE_ALPHA            object
  YEAR                    int32
  MONTH                   int32
  DAY                     int32
  HOUR                    int32
  MINUTE                  int32
  ST_CASE                 int32
  LAT                   float64
  LNG                   float64

  """
  states_to_exclude = states_to_exclude if not None else []

  all_accidents = None

  COLS = ["STATE", "STATE_ALPHA", "YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "ST_CASE", "LAT", "LNG"]

  def _cleanup(acc, year):
    # We exclude some states as their timezone makes them unusable (see above).
    acc = acc[~acc["STATE"].isin(states_to_exclude)]
    # Some accidents are recorded with hour = 24. Not sure if that's the same as
    # 0, so we remove them.
    acc = acc[acc["HOUR"] != 24]
    # Some accidents are recorded with unknown time (set as 99).
    acc = acc[acc["HOUR"] != 99]
    acc = acc[acc["MINUTE"] != 99]
    acc = acc.assign(YEAR=year)
    return acc

  for i in range(1975, 2001):
    print("Reading %d..." % i)
    accidents = _cleanup(pd.read_csv("raw/a%d.csv" % i), i)
    accidents = pd.merge(accidents, counties, how='left', on=["STATE", "COUNTY"])
    accidents = accidents[COLS]
    if all_accidents is None:
      all_accidents = accidents
    else:
      all_accidents = pd.concat([all_accidents, accidents])

  for i in range(2001, 2018):
    print("Reading %d..." % i)
    accidents = _cleanup(pd.read_csv("raw/a%d.csv" % i), i)
    accidents = pd.merge(accidents, states, how='left', on=["STATE"])
    accidents = accidents.rename(columns={
        "LATITUDE": "LAT",
        "LONGITUD": "LNG",
    })
    accidents = accidents[COLS]
    all_accidents = pd.concat([all_accidents, accidents])

  all_accidents = all_accidents.astype({
      "STATE": "int32",
      "YEAR": "int32",
      "MONTH": "int32",
      "DAY": "int32",
      "HOUR": "int32",
      "MINUTE": "int32",
      "ST_CASE": "int32",
  })

  # Some accidents have bad location (usually 100 latitude or 1000 longitude).
  all_accidents = all_accidents[all_accidents["LAT"] < 75.0]
  all_accidents = all_accidents[all_accidents["LAT"] > 20.0]
  all_accidents = all_accidents[all_accidents["LNG"] < -60.0]
  all_accidents = all_accidents[all_accidents["LNG"] > -175.0]

  return all_accidents


def fill(accidents, tz, tz_override, dst):
  """Return a single dataframe with columns
  STATE                           float64
  STATE_ALPHA                      object
  TIME                     datetime64[ns]
  YEAR                              int32
  MONTH                             int32
  DAY                               int32
  HOUR                              int32
  MINUTE                            int32
  ST_CASE                           int32
  LAT                             float64
  LNG                             float64
  TZ_NO_DST                       float64
  TZ_DST                          float64
  DST_SWITCH               datetime64[ns]
  DST_DELTA                       float64
  DST                              object
  DAYS_FROM_DST_SWITCH              int32

  """
  COLS = [
      "STATE",
      "STATE_ALPHA",
      "TIME",
      "YEAR",
      "MONTH",
      "DAY",
      "HOUR",
      "MINUTE",
      "ST_CASE",
      "LAT",
      "LNG",
      "TZ_NO_DST",
      "TZ_DST",
      "DST_SWITCH",
      "DAYS_FROM_DST_SWITCH",
      "DST_DELTA",
      "DST",
      "OFFSET_LNG",
      "OFFSET_MINUTES",
  ]

  accidents = pd.merge(accidents, tz, how="left", on=["STATE_ALPHA"])
  accidents["TIME"] = pd.to_datetime(
      accidents[["YEAR", "MONTH", "DAY", "HOUR", "MINUTE"]], errors="coerce")

  print("Removing %d/%d accidents with invalid time..." % (
      len(accidents[accidents["TIME"].isnull()]),
      len(accidents)))
  accidents = accidents[pd.notna(accidents["TIME"])]

  # Add time to DST switch
  dst.loc[:, "DST_SWITCH"] = dst["TIME"]
  accidents = pd.merge_asof(
      accidents.sort_values(by="TIME"),
      dst.sort_values(by="TIME"),
      on="TIME",
      direction="backward")
  accidents["TIME_FROM_DST_SWITCH"] = accidents["TIME"] - accidents["DST_SWITCH"]
  accidents["DAYS_FROM_DST_SWITCH"] = accidents["TIME_FROM_DST_SWITCH"].dt.days
  accidents = accidents.astype({
      "DAYS_FROM_DST_SWITCH": "int32",
  })
  accidents["DST"] = np.where(accidents["DST_DELTA"] == 1, "yes", "no")

  accidents["OFFSET_LNG"] = np.where(
    accidents["DST_DELTA"] == 1,
    accidents["LNG"] - accidents["TZ_DST"],
    accidents["LNG"] - accidents["TZ_NO_DST"])
  accidents["OFFSET_MINUTES"] = (
    (accidents["OFFSET_LNG"] * 60.0 / 15.0 + QUANT_MINUTES / 2.0)
    // QUANT_MINUTES * QUANT_MINUTES)

  return accidents[COLS]


def main():
  if os.path.exists("derived/_states.csv") and os.path.exists("derived/_counties.csv"):
    states = read_states()
    counties = read_counties()
  else:
    states, counties = read_geolocation()
    states.to_csv("derived/_states.csv", index=False)
    counties.to_csv("derived/_counties.csv", index=False)

  dst = read_dst()
  tz = read_timezones()
  tz_override = read_timezone_override()

  if os.path.exists("derived/_accidents.csv"):
    accidents = read_accidents()
  else:
    accidents = read_raw_accidents(states, counties, states_to_exclude=STATES_TO_EXCLUDE)
    accidents.to_csv("derived/_accidents.csv", index=False)

  data = fill(accidents, tz, tz_override, dst)
  return data


if __name__ == "__main__":
  data = main()
  print("Writing _data...")
  data.to_csv("_data.csv", index=False)
