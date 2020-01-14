import numpy as np


def remove_first_week_after_dst_switch(data):
  # Remove first week after DST switch as it might contain outliers.
  return data[data["DAYS_FROM_DST_SWITCH"] > 7]


def remove_small_groups(
        data, group_columns, value_column="STATE", threshold=10000):
  return data[
    data.groupby(group_columns)[value_column].transform(len) >= threshold]


def transform_offset_for_reading(data):
  v = sorted(np.unique(data["OFFSET_MINUTES"].values))
  data["OFFSET_MINUTES"] = data["OFFSET_MINUTES"].apply(
    lambda x : "0" if int(x) == 0 else str(int(x)) + "m")
  return ["0" if int(x) == 0 else str(int(x)) + "m" for x in v]
