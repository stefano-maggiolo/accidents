import pandas as pd
import numpy as np
import scipy.stats
import seaborn as sns
import matplotlib.pyplot as plt

import process
import utils


def ks_test(d1, d2, minutes_delay=0):
    t = lambda x: (x - 5 * 60) % (24 * 60)
    return scipy.stats.ks_2samp(t(d1), (t(d2) + minutes_delay) % (24 * 60)).pvalue


def _get_probs(data, keys):
  _ = data.groupby(
      ["DST", "OFFSET_MINUTES", "HOUR"])["STATE"].count()\
          .groupby(["DST", "OFFSET_MINUTES"]).transform(lambda x : x / x.sum())\
          .reset_index().rename(columns={"STATE": "ACCIDENTS"})
  return dict((k, _[_["OFFSET_MINUTES"] == k]["ACCIDENTS"].values)
              for k in keys)


def _print_pvalues(keys, data, dst_or_no):
    quarter_hour_delays = [-4, -3, -2, -1, 0, 1, 2, 3, 4]
    minutes_delays = [x * 15 for x in quarter_hour_delays]
    test_values = pd.DataFrame(columns=minutes_delays)
    for k1 in keys:
        v1 = data[data["OFFSET_MINUTES"] == k1]["DAY_MINUTE"].values
        for k2 in keys:
            v2 = data[data["OFFSET_MINUTES"] == k2]["DAY_MINUTE"].values
            row = {}
            name = "%6s %6s  " % (k1, k2)
            print name,
            for delay in minutes_delays:
                test_value = ks_test(v1, v2, delay)
                log_test_value = np.log10(1e-200 + test_value)
                print "%6.1f" % (log_test_value),
                row[delay] = log_test_value
            print
            test_values = test_values.append(
                pd.Series(row,
                          index=test_values.columns,
                          name="%s %s" % (k1, k2)))
    plt.clf()
    ax = sns.heatmap(test_values, annot=True, fmt=".1f")
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

    plt.savefig("plots/04_ks_test_values_%s.png" % dst_or_no)


def main():
  sns.set_style("whitegrid")

  data = process.main()
  data = utils.remove_first_week_after_dst_switch(data)

  data = utils.remove_small_groups(data, ["DST", "OFFSET_MINUTES"])

  dst_data = data[data["DST"] == "yes"]
  nodst_data = data[data["DST"] == "no"]

  dst_keys = utils.transform_offset_for_reading(dst_data)
  nodst_keys = utils.transform_offset_for_reading(nodst_data)

  dst_probs = _get_probs(dst_data, dst_keys)
  nodst_probs = _get_probs(nodst_data, nodst_keys)

  print("DST yes")
  print dst_data.groupby(["DST", "OFFSET_MINUTES"])["STATE"].count()
  print
  _print_pvalues(dst_keys, dst_data, "dst")

  print
  print("DST no")
  print nodst_data.groupby(["DST", "OFFSET_MINUTES"])["STATE"].count()
  print
  _print_pvalues(nodst_keys, nodst_data, "nodst")




if __name__ == "__main__":
  main()
