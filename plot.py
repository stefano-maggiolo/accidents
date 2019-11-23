import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from process import main as process_main

sns.set_style("whitegrid")

QUANT_MINUTES = 30


def more_process(data):
  # Remove first week after DST switch as it might contain outliers.
  data = data[data["DAYS_FROM_DST_SWITCH"] > 7]

  data["OFFSET_LNG"] = np.where(data["DST_DELTA"] == 1, data["LNG"] - data["TZ_DST"], data["LNG"] - data["TZ_NO_DST"])
  data["OFFSET_MINUTES"] = (data["OFFSET_LNG"] * 60.0 / 15.0 + QUANT_MINUTES / 2.0) // QUANT_MINUTES * QUANT_MINUTES

  return data


def _format_ax(ax):
  ax.set_xticks(range(24), minor=True)
  ax.set_xticks(range(0, 24, 3), minor=False)
  ax.set_ylim(0.01, 0.07)
  ax.grid(which='major', alpha=0.8, linestyle='-')
  ax.grid(which='minor', alpha=0.5, linestyle='-')

  vals = ax.get_yticks()
  ax.set_yticklabels(['{:,.2%}'.format(x) for x in vals])

  return ax


def _only_big(d):
  return d[d.groupby(["DST", "OFFSET_MINUTES"])["STATE"].transform(len) >= 5000]


def main():
  data = more_process(process_main())

  fig, ax = plt.subplots(figsize=(16, 9))
  _ = data.groupby(["DST", "HOUR"])["STATE"].count()\
          .groupby(["DST"]).transform(lambda x : x / x.sum())\
          .reset_index().rename(columns={"STATE": "ACCIDENTS"})
  sns.lineplot(data=_, x="HOUR", y="ACCIDENTS", hue="DST", ax=ax)
  _format_ax(ax)
  plt.savefig("plots/01_dst_nodst_comparison.png")

  data = _only_big(data)

  fig, ax = plt.subplots(figsize=(16, 9))
  _ = data.groupby(["DST", "OFFSET_MINUTES", "HOUR"])["STATE"].count()\
          .groupby(["DST", "OFFSET_MINUTES"]).transform(lambda x : x / x.sum())\
          .reset_index().rename(columns={"STATE": "ACCIDENTS"})
  _ = _[_["DST"] == "no"]
  sns.lineplot(data=_, x="HOUR", y="ACCIDENTS", hue="OFFSET_MINUTES", ax=ax)
  _format_ax(ax)
  plt.savefig("plots/02_nodst_by_offset.png")

  fig, ax = plt.subplots(figsize=(16, 9))
  _ = data.groupby(["DST", "OFFSET_MINUTES", "HOUR"])["STATE"].count()\
          .groupby(["DST", "OFFSET_MINUTES"]).transform(lambda x : x / x.sum())\
          .reset_index().rename(columns={"STATE": "ACCIDENTS"})
  _ = _[_["DST"] == "yes"]
  sns.lineplot(data=_, x="HOUR", y="ACCIDENTS", hue="OFFSET_MINUTES", ax=ax)
  _format_ax(ax)
  plt.savefig("plots/03_dst_by_offset.png")


if __name__ == "__main__":
  main()
